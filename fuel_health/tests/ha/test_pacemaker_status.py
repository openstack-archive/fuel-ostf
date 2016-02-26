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
          1. Get pacemaker status for each online controller
          2. Check status of online/offline controllers in pacemaker
          3. Check status of nodes where resources are started
          4. Check that an active resource is started and not failed
          5. Check that list of resources is the same on all online controllers
          6. Check that list of nodes where a resource is started is the same
             on all controllers
          7. Check controllers that pcs resources are started on the same nodes
        Duration: 10 s.
        Available since release: 2015.1.0-7.0
        """
        # 1. Get pacemaker status
        cluster_resources = {}
        nodes = {}
        cmd = 'sudo pcs status xml'
        for i, ip in enumerate(self.online_controller_ips):
            fqdn = self.online_controller_names[i]
            err_msg = ('Cannot get pacemaker status. Execution of the "{0}" '
                       'failed on the controller {0}.'.format(cmd, fqdn))

            pcs_status = self.verify(20, self._run_ssh_cmd, 1, err_msg,
                                     'get pacemaker status', ip, cmd)[0]
            self.verify_response_true(
                pcs_status, 'Step 1 failed: Cannot get pacemaker status. Check'
                ' the pacemaker service on the controller {0}.'.format(fqdn))

            cluster_resources[fqdn] = self.get_pcs_resources(pcs_status)
            nodes[fqdn] = self.get_pcs_nodes(pcs_status)
            LOG.debug("Pacemaker resources status on the controller {0}: {1}."
                      .format(fqdn, cluster_resources[fqdn]))
            LOG.debug("Pacemaker nodes status on the controller {0}: {1}."
                      .format(fqdn, nodes[fqdn]))

        # 2. Compare online / offline nodes list in Nailgun and pacemaker
        nailgun_online = set(self.online_controller_names)
        nailgun_offline = set(self.offline_controller_names)
        for i, ip in enumerate(self.online_controller_ips):
            fqdn = self.online_controller_names[i]
            self.verify_response_true(
                set(nodes[fqdn]['Online']) == nailgun_online and
                set(nodes[fqdn]['Offline']) == nailgun_offline,
                'Step 2 failed: Online/Offline nodes on the controller {0} '
                'differs from the actual controllers status.'.format(fqdn))

        # For each fqdn, perform steps 3 and 4 (checks that pacemaker
        # is properly working with online controllers):
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

                    self.verify_response_true(
                        not resource['failed'],
                        'Step 4 failed: On the controller {0}, resource {1} is'
                        ' active but failed to start ({2}managed).'
                        .format(fqdn,
                                res_name,
                                "un" if not resource['managed'] else ""))

        # Make pairs from fqdn names of controllers
        fqdns = list(cluster_resources.keys())
        fqdn_pairs = [
            (x, y) for i, x in enumerate(fqdns[:-1]) for y in fqdns[i+1:]]

        # For each pair, perform steps 5 and 6 (checks for split brain):
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

        # 7. Check that each resource started only on nodes that
        # allowed to start this resource, and not started on other nodes.

        # Get pacemaker constraints
        cmd = 'sudo cibadmin --query --scope constraints'
        err_msg = ('Cannot get pacemaker constraints. Execution of the "{0}" '
                   'failed on the controller {0}.'
                   .format(cmd, self.online_controller_names[0]))
        constraints_xml = self.verify(
            20, self._run_ssh_cmd, 7, err_msg, 'get pacemaker constraints',
            self.online_controller_ips[0], cmd)[0]
        constraints = self.get_pcs_constraints(constraints_xml)

        for rsc in constraints:
            (allowed, started, disallowed) = self.get_resource_nodes(
                rsc, constraints, cluster_resources[fqdns[0]], orig_rsc=[])
            # In 'started' list should be only the nodes where the resource
            # is 'allowed' to start
            self.verify_response_true(
                set(allowed) >= set(started),
                'Step 7 failed: Resource {0} started on the nodes {1}, but it '
                'is allowed to start only on the nodes {2}'
                .format(rsc, started, allowed))

            # 'disallowed' list, where the resource started but
            # not allowed to start, should be empty.
            self.verify_response_true(
                not disallowed,
                'Step 7 failed: Resource {0} disallowed to start on the nodes '
                '{1}, but actually started on the nodes {2}'
                .format(rsc, disallowed, started))

            # If 'allowed' is not empty and contains:
            #   - more than one node where resource is allowed, or
            #   - at least one working controller node,
            # then 'started' should contain at least one node where
            # the resource is actually running.
            if (len(allowed) > 1) or (set(allowed) - nailgun_offline):
                self.verify_response_true(
                    set(started) - nailgun_offline,
                    'Step 7 failed: Resource {0} allowed to start on the nodes'
                    ' {1}, but it is not started on any node'
                    .format(rsc, allowed, started))
