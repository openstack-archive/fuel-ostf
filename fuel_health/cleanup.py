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

from fuel_health import exceptions
import fuel_health.nmanager


LOG = logging.getLogger(__name__)


class CleanUpClientManager(fuel_health.nmanager.OfficialClientManager):
    """
    Manager that provides access to the official python clients for
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

def cleanup():
    manager = CleanUpClientManager()

    savanna_client = manager._get_savanna_client()
    if savanna_client is not None:
        savanna_clusters = savanna_client.clusters.list()
        for s in savanna_clusters:
            if s.name.startswith('ostf-test-'):
                try:
                    LOG.info('Start savanna cluster deletion.')
                    savanna_client.clusters.delete(s.id)
                except Exception as exc:
                        LOG.debug(exc)
                        pass
        savanna_clusters_template = savanna_client.cluster_templates.list()
        for s in savanna_clusters_template:
            if s.name.startswith('ostf_test-'):
                try:
                    LOG.info('Start savanna cluster template deletion.')
                    savanna_client.cluster_templates.delete(s.id)
                except Exception as exc:
                        LOG.debug(exc)
                        pass
        savanna_node_group_template = savanna_client.node_group_templates.list()
        for s in savanna_node_group_template:
            if s.name.startswith('ostf_test-'):
                try:
                    LOG.info('Start savanna node group template deletion.')
                    savanna_client.node_group_templates.delete(s.id)
                except Exception as exc:
                        LOG.debug(exc)
                        pass

    murano_client = manager._get_murano_client()
    if murano_client is not None:
        environments = murano_client.list_environments()
        for e in environments:
            if e.name.startswith('ost1_test-'):
                try:
                    LOG.info('Start environment deletion.')
                    murano_client.stacks.delete(e.id)
                except Exception as exc:
                    LOG.debug(exc)
                    pass

    heat_client = manager._get_heat_client()
    if heat_client is not None:
        stacks = heat_client.stacks.list()
        for s in stacks:
            if s.stack_name.startswith('ost1_test-'):
                if s.stack_status in ('CREATE_COMPLETE', 'ERROR'):
                    try:
                        LOG.info('Start stacks deletion.')
                        heat_client.stacks.delete(s.id)
                    except Exception as exc:
                        LOG.debug(exc)
                        pass

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
                        except Exception as exc:
                            LOG.debug(exc)
                            pass
                try:
                    LOG.info('Delete server with name %s' % s.name)
                    manager._get_compute_client().servers.delete(s.id)
                except Exception as exc:
                    LOG.debug(exc)
                    pass
    else:
        LOG.info('No servers found')

        for s in servers:
            try:
                LOG.info('Wait for server terminations')
                manager.wait_for_server_termination(s)
            except Exception as exc:
                LOG.debug(exc)
                pass

    keypairs = manager._get_compute_client().keypairs.list()

    for k in keypairs:
        if k.name.startswith('ost1_test-'):
            try:
                LOG.info('Start keypair deletion: %s' % k)
                manager._get_compute_client().keypairs.delete(k)
            except Exception as exc:
                LOG.debug(exc)
                pass

    users = manager._get_identity_client().users.list()
    for user in users:
        if user.name.startswith('ost1_test-'):
            try:
                LOG.info('Start deletion of users')
                manager._get_identity_client().users.delete(user)
            except exceptions as exc:
                LOG.debug(exc)
                pass

    tenants = manager._get_identity_client().tenants.list()
    for tenant in tenants:
        if tenant.name.startswith('ost1_test-'):
            try:
                LOG.info('Start tenant deletion')
                manager._get_identity_client().tenants.delete(tenant)
            except Exception as exc:
                LOG.debug(exc)
                pass

    roles = manager._get_identity_client().roles.list()
    if roles:
        for role in roles:
            if role.name.startswith('ost1_test-'):
                try:
                    LOG.info('Start roles deletion')
                    manager._get_identity_client().roles.delete(role)
                except Exception as exc:
                    LOG.debug(exc)
                    pass
    else:
        LOG.info('no roles')

    images = manager._get_compute_client().images.list()
    for image in images:
        if image.name.startswith('ost1'):
            try:
                LOG.info('Start images deletion')
                manager._get_compute_client().images.delete(image)
            except Exception as exc:
                LOG.debug(exc)
                pass

    sec_groups = manager._get_compute_client().security_groups.list()

    for sgroup in sec_groups:
        if sgroup.name.startswith('ost1_test-'):
            try:
                LOG.info('Start deletion of security groups')
                manager._get_compute_client().security_groups.delete(sgroup.id)
            except Exception as exc:
                LOG.debug(exc)
                pass

    volumes = manager._get_volume_client().volumes.list()

    for volume in volumes:
        if volume.display_name.startswith('ost1_test-'):
            try:
                LOG.info('Start volumes deletion')
                manager._get_volume_client().volumes.delete(volume)
            except Exception as exc:
                LOG.debug(exc)
                pass

    flavors = manager._get_compute_client().flavors.list()

    for flavor in flavors:
        if flavor.name.startswith('ost1_test-'):
            try:
                LOG.info('start flavors deletion')
                manager._get_compute_client().flavors.delete(flavor)
            except Exception as exc:
                LOG.debug(exc)
                pass

    vtypes = manager._get_volume_client().volume_types.list()
    for vtype in vtypes:
        if vtype.name.startswith('ost1_test-'):
            try:
                LOG.info('start deletion of volume types')
                manager._get_volume_client().volume_types.delete(vtype)
            except Exception as exc:
                LOG.debug(exc)
                pass


if __name__ == "__main__":
    cleanup()
