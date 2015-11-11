#!/usr/bin/env python
# Copyright 2013 Mirantis, Inc.
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

import os
import sys
import time

path = os.getcwd()
sys.path.append(path)

import logging
import requests
import traceback

from fuel_health import exceptions
import fuel_health.nmanager


LOG = logging.getLogger(__name__)


class CleanUpClientManager(fuel_health.nmanager.OfficialClientManager):
    """Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    def wait_for_server_termination(self, server, ignore_error=False):
        """Waits for server to reach termination."""
        start_time = int(time.time())
        while True:
            try:
                self._get_compute_client().servers.get(server)
            except exceptions.NotFound:
                return

            server_status = server.status
            if server_status == 'ERROR' and not ignore_error:
                raise exceptions.BuildErrorException(server_id=server.id)

            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException

            time.sleep(self.build_interval)


def cleanup(cluster_deployment_info):
    """Function performs cleaning up for current cluster.

    Because clusters can be deployed in different way
    function uses cluster_deployment_info argument which
    contains list of deployment tags of needed cluster.

    This approach that consists in using one cleanup function
    for all possible testsets is not so good because of
    constant checking of component presence in deployment info.

    More better way is to create separate functions for each
    set of tests so refactoring of this chunk of code is higly
    appreciated.
    """
    manager = CleanUpClientManager()

    if 'sahara' in cluster_deployment_info:
        try:
            sahara_client = manager._get_sahara_client()
            if sahara_client is not None:
                _delete_it(client=sahara_client.clusters,
                           log_message='Start sahara cluster deletion',
                           name='ostf-test-', delete_type='id')
                _delete_it(client=sahara_client.cluster_templates,
                           log_message='Start sahara cluster'
                                       ' template deletion',
                           delete_type='id')
                _delete_it(client=sahara_client.node_group_templates,
                           log_message='Start sahara node'
                                       ' group template deletion',
                           delete_type='id')
        except Exception:
            LOG.warning(traceback.format_exc())

    if 'murano' in cluster_deployment_info:
        try:
            murano_client = manager._get_murano_client()
            compute_client = manager._get_compute_client()

            if murano_client is not None:
                endpoint = manager.config.murano.api_url + '/v1/'
                headers = {'X-Auth-Token': murano_client.auth_token,
                           'content-type': 'application/json'}
                environments = requests.get(endpoint + 'environments',
                                            headers=headers).json()
                for e in environments["environments"]:
                    if e['name'].startswith('ostf_test-'):
                        try:
                            LOG.info('Start environment deletion.')
                            requests.delete('{0}environments/{1}'.format(
                                endpoint, e['id']), headers=headers)
                        except Exception:
                            LOG.warning('Failed to delete murano environment')
                            LOG.debug(traceback.format_exc())

            if compute_client is not None:
                flavors = compute_client.flavors.list()
                for flavor in flavors:
                    if 'ostf_test_Murano' in flavor.name:
                        try:
                            LOG.info('Start flavor deletion.')
                            compute_client.flavors.delete(flavor.id)
                        except Exception:
                            LOG.warning('Failed to delete flavor')
                            LOG.debug(traceback.format_exc())

        except Exception:
            LOG.warning(traceback.format_exc())

    if 'ceilometer' in cluster_deployment_info:
        try:
            ceilometer_client = manager._get_ceilometer_client()
            if ceilometer_client is not None:
                alarms = ceilometer_client.alarms.list()
                for a in alarms:
                    if a.name.startswith('ost1_test-'):
                        try:
                            LOG.info('Start alarms deletion.')
                            ceilometer_client.alarms.delete(a.id)
                        except Exception as exc:
                            LOG.debug(exc)
        except Exception as exc:
            LOG.warning(
                'Something wrong with ceilometer client. Exception: %s', exc
            )

    if 'heat' in cluster_deployment_info:
        try:
            heat_client = manager._get_heat_client()
            if heat_client is not None:
                stacks = heat_client.stacks.list()
                for s in stacks:
                    if s.stack_name.startswith('ost1_test-'):
                        try:
                            LOG.info('Start stacks deletion.')
                            heat_client.stacks.delete(s.id)
                        except Exception:
                            LOG.debug(traceback.format_exc())
        except Exception:
            LOG.warning(traceback.format_exc())

    instances_id = []
    servers = manager._get_compute_client().servers.list()
    floating_ips = manager._get_compute_client().floating_ips.list()

    if servers:
        for s in servers:
            if s.name.startswith('ost1_test-'):
                instances_id.append(s.id)
                for f in floating_ips:
                    if f.instance_id in instances_id:
                        try:
                            LOG.info('Delete floating ip %s' % f.ip)
                            manager._get_compute_client().floating_ips.delete(
                                f.id)
                        except Exception:
                            LOG.debug(traceback.format_exc())
                try:
                    LOG.info('Delete server with name %s' % s.name)
                    manager._get_compute_client().servers.delete(s.id)
                except Exception:
                    LOG.debug(traceback.format_exc())
    else:
        LOG.info('No servers found')

        for s in servers:
            try:
                LOG.info('Wait for server terminations')
                manager.wait_for_server_termination(s)
            except Exception:
                LOG.debug(traceback.format_exc())

    _delete_it(manager._get_compute_client().keypairs,
               'Start keypair deletion')
    _delete_it(manager._get_identity_client().users, 'Start deletion of users')
    _delete_it(manager._get_identity_client().tenants, 'Start tenant deletion')
    roles = manager._get_identity_client().roles.list()
    if roles:
        _delete_it(manager._get_identity_client().roles,
                   'Start roles deletion')
    else:
        LOG.info('no roles')
    _delete_it(manager._get_compute_client().images, 'Start images deletion')
    _delete_it(manager._get_volume_client().volumes, 'Start volumes deletion')
    _delete_it(manager._get_compute_client().flavors, 'start flavors deletion')
    _delete_it(manager._get_volume_client().volume_types,
               'start deletion of volume types')
    _delete_it(manager._get_compute_client().security_groups,
               'Start deletion of security groups', delete_type='id')


def _delete_it(client, log_message, name='ost1_test-', delete_type='name'):
    try:
        for item in client.list():
            try:
                if item.name.startswith(name):
                    try:
                        LOG.info(log_message)
                        if delete_type == 'name':
                            client.delete(item)
                        else:
                            client.delete(item.id)
                    except Exception:
                        LOG.debug(traceback.format_exc())
            except AttributeError:
                if item.display_name.startswith(name):
                    client.delete(item)
    except Exception:
        LOG.warning(traceback.format_exc())


if __name__ == "__main__":
    cleanup()
