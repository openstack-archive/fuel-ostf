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

from fuel_health import ha_base


LOG = logging.getLogger(__name__)


class TestPacemakerStatus(ha_base.TestPacemakerBase):
    """TestClass contains test for pacemaker status on cluster controllers."""

    def test_check_pacemaker_resources(self):
        """Check pacemaker status

        Scenario:
          1. Get pacemaker status from online controllers
          2. Check status of online/offline controllers in pacemaker
          3. Check status of nodes where resources are started
          4. Check list of nodes on active resources
          5. Check that list of resources is the same on all online controllers
          6. Check that every resource started on the same controllers
        Duration: 10 s.
        Available since release: 2014.2.2-6.1
        """
        cluster_resources = {}
        for i, ip in enumerate(self.online_controller_ips):

            fqdn = self.online_controller_names[i]

            # 1. Get pacemaker status
            cmd = 'pcs status xml'
            err_msg = ('Cannot get pacemaker status. Execution of the "{0}" '
                       'failed on the controller {0}.'.format(cmd, fqdn))
            pcs_status = self.verify(20, self._run_ssh_cmd, 1, err_msg,
                                     'get pacemaker status', ip, cmd)[0]
            self.verify_response_true(
                pcs_status, 'Step 1 failed: Cannot get pacemaker status. Check'
                ' the pacemaker service on the controller {0}.'.format(fqdn))

            cluster_resources[fqdn] = self.get_pcs_resources(pcs_status)
            LOG.debug("Pacemaker resources status on the controller {0}: {1}."
                      .format(fqdn, cluster_resources[fqdn]))

            # 2. Compare online / offline nodes list in Nailgun and pacemaker
            nodes = self.get_pcs_nodes(pcs_status)
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
