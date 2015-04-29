# Copyright 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
from xml.dom.minidom import parseString as xmlparce  # noqa

from fuel_health.common.ssh import Client as SSHClient
import fuel_health.test

LOG = logging.getLogger(__name__)


class TestPacemakerStatus(fuel_health.test.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestPacemakerStatus, cls).setUpClass()
        cls.controller_names = cls.config.compute.controller_names
        cls.online_controller_names = (
            cls.config.compute.online_controller_names)
        cls.offline_controller_names = list(
            set(cls.controller_names) - set(cls.online_controller_names))

        cls.online_controller_ips = cls.config.compute.online_controllers
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.ssh_user

    def setUp(self):
        super(TestPacemakerStatus, self).setUp()
        if 'ha' not in self.config.mode:
            self.skipTest('Cluster is not HA mode, skipping tests')
        if not self.online_controller_names:
            self.skipTest('There are no controller nodes')

    def _get_pcs_resources(self, pcs_status):
        """Get pacemaker resources status to a python dict:
            return:
                {
                  str: {                        # Resource name
                    'started': int,             # count of Master/Started
                    'stopped': int,             # count of Stopped resources
                    'nodes':  [node_name, ...], # All node names where the
                                                # resource is started
                    'master': [node_name, ...], # Node names for 'Master'
                                                # ('master' is also in 'nodes')
                  },
                  ...
                }
        """
        pcs_xml = xmlparce(''.join(pcs_status))

        resources = {}
        res_group_xml = pcs_xml.getElementsByTagName('resources')
        res_set = res_group_xml[0].getElementsByTagName('resource')
        for res in res_set:
            res_name = res.getAttribute('id')
            if res_name not in resources:
                resources[res_name] = {
                    'master': [],
                    'nodes': [],
                    'started': 0,
                    'stopped': 0,
                    'active': False}

            if 'true' in res.getAttribute('active'):
                resources[res_name]['active'] = True

            res_role = res.getAttribute('role')
            num_nodes = int(res.getAttribute('nodes_running_on'))
            if num_nodes:
                resources[res_name]['started'] += num_nodes

                rnodes = res.getElementsByTagName('node')
                for rnode in rnodes:
                    if 'Master' in res_role:
                        resources[res_name]['master'].append(
                            rnode.getAttribute('name'))
                    resources[res_name]['nodes'].append(
                        rnode.getAttribute('name'))
            else:
                resources[res_name]['stopped'] += 1
        return resources

    def _get_pcs_nodes(self, pcs_status):
        pcs_xml = xmlparce(''.join(pcs_status))
        nodes_group_xml = pcs_xml.getElementsByTagName('nodes')
        nodes_set = nodes_group_xml[0].getElementsByTagName('node')
        nodes = {'Online': [], 'Offline': []}
        for node in nodes_set:
            if 'true' in node.getAttribute('online'):
                nodes['Online'].append(node.getAttribute('name'))
            else:
                nodes['Offline'].append(node.getAttribute('name'))
        return nodes

    def test_check_pacemaker_resources(self):
        """Check pacemaker status

        Scenario:
          1. Get pacemaker status from online controllers
          2. Offline controllers in Nailgun must be same as in pacemaker
          3. Any of offline nodes should not be used in started resources
          4. All 'active' resources should not have empty nodes list.
          5. All online controllers should have the same list of resources
          6. All resources should have the same list of nodes where it started.
        Duration: 10 s.
        """
        cluster_resources = {}
        for i, ip in enumerate(self.online_controller_ips):

            fqdn = self.online_controller_names[i]

            ssh_client = SSHClient(
                ip, self.controller_user,
                key_filename=self.controller_key, timeout=100)

            cmd = 'pcs status xml'

            # 1. Get pacemaker status
            pcs_status = self.verify(
                20, ssh_client.exec_command, 1,
                'Cannot get pacemaker status. '
                'Check if pacemaker is running on the controller {0}.'
                .format(fqdn), 'get pacemaker status', cmd)

            cluster_resources[fqdn] = self._get_pcs_resources(pcs_status)
            LOG.debug("Pacemaker resources status on the controller {0}: {1}."
                      .format(fqdn, cluster_resources[fqdn]))

            # 2. Compare online / offline nodes list in Nailgun and pacemaker
            nodes = self._get_pcs_nodes(pcs_status)
            LOG.debug("Pacemaker nodes status on the controller {0}: {1}."
                      .format(fqdn, nodes))
            self.verify_response_true(
                set(nodes['Online']) == set(self.online_controller_names) and
                set(nodes['Offline']) == set(self.offline_controller_names),
                'Step 2 failed: Online/Offline nodes on the controller {0} '
                'differs from the actual controllers status.'.format(fqdn))

        for fqdn in cluster_resources:
            for res_name in cluster_resources[fqdn]:
                resource = cluster_resources[fqdn][res_name]
                # 3. Ensure that every resource uses only online controllers
                not_updated = (set(self.offline_controller_names) &
                               set(resource['nodes']))
                self.verify_response_true(
                    not not_updated,
                    'Step 3 failed: On the controller {0}, resource {1} is '
                    'started on the controller(s) {2} that marked as offline '
                    'in Nailgun.'.format(fqdn, res_name, not_updated))

                # 4. Active resource should be started on controller(s)
                if resource['active']:
                    self.verify_response_true(
                        resource['started'],
                        'Step 4 failed: On the controller {0}, resource {1} is'
                        ' active but is not started on any controller.'
                        .format(fqdn, res_name))

        # Make pairs from fqdn names of controllers
        fqdns = list(cluster_resources.keys())
        fqdn_pairs = [
            (x, y) for i, x in enumerate(fqdns[:-1]) for y in fqdns[i+1:]]

        # Compare recources for every pair
        for x, y in fqdn_pairs:
            res_x = cluster_resources[x]
            res_y = cluster_resources[y]

            # 5. Compare resource lists.
            set_x = set(res_x.keys())
            set_y = set(res_y.keys())
            self.verify_response_true(
                set_x == set_y,
                'Step 5 failed: Resources list is different. Missed resources '
                'on the controller {0}: {1} ; on the controller {2}: {3}.'
                .format(x, set_y - set_x, y, set_x - set_y))

            # 6. Check that nodes list of every resource is syncronized
            for res in res_x:
                self.verify_response_true(
                    set(res_x[res]['nodes']) == set(res_y[res]['nodes']),
                    'Step 6 failed: On the controllers {0} and {1}, resource '
                    '{2} has different list of nodes where it is started.'
                    .format(x, y, res))
