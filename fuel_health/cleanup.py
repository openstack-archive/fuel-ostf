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


# Default client libs
import cinderclient.client
import glanceclient.client
import keystoneclient.v2_0.client
import novaclient.client


from fuel_health import exceptions
import fuel_health.manager
import fuel_health.test



LOG = logging.getLogger(__name__)


class CleanUpClientManager(fuel_health.manager.Manager):
    """
    Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    NOVACLIENT_VERSION = '2'
    CINDERCLIENT_VERSION = '1'

    def __init__(self):
        super(CleanUpClientManager, self).__init__()
        self.compute_client = self._get_compute_client()
        self.image_client = self._get_image_client()
        self.identity_client = self._get_identity_client()
        self.volume_client = self._get_volume_client()
        self.client_attr_names = [
            'compute_client',
            'image_client',
            'identity_client',
            'volume_client'
        ]

    def _get_compute_client(self, username=None, password=None,
                            tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for compute client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        client_args = (username, password, tenant_name, auth_url)

        service_type = self.config.compute.catalog_type
        return novaclient.client.Client(self.NOVACLIENT_VERSION,
                                        *client_args,
                                        service_type=service_type,
                                        no_cache=True,
                                        insecure=dscv)

    def _get_image_client(self):
        keystone = self._get_identity_client()
        token = keystone.auth_token
        endpoint = keystone.service_catalog.url_for(service_type='image',
                                                    endpoint_type='publicURL')
        dscv = self.config.identity.disable_ssl_certificate_validation
        return glanceclient.Client('1', endpoint=endpoint, token=token,
                                   insecure=dscv)

    def _get_volume_client(self, username=None, password=None,
                           tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        auth_url = self.config.identity.uri
        return cinderclient.client.Client(self.CINDERCLIENT_VERSION,
                                          username,
                                          password,
                                          tenant_name,
                                          auth_url)

    def _get_identity_client(self, username=None, password=None,
                             tenant_name=None):
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        if not tenant_name:
            tenant_name = self.config.identity.admin_tenant_name

        if None in (username, password, tenant_name):
            msg = ("Missing required credentials for identity client. "
                   "username: %(username)s, password: %(password)s, "
                   "tenant_name: %(tenant_name)s") % locals()
            raise exceptions.InvalidConfiguration(msg)

        auth_url = self.config.identity.uri
        dscv = self.config.identity.disable_ssl_certificate_validation

        return keystoneclient.v2_0.client.Client(username=username,
                                                 password=password,
                                                 tenant_name=tenant_name,
                                                 auth_url=auth_url,
                                                 insecure=dscv)

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
    instances_id = []
    servers = manager._get_compute_client().servers.list()
    floating_ips = manager._get_compute_client().floating_ips.list()

    for s in servers:
        if s.name.startswith('ost1_test-'):
            instances_id.append(s.id)
            for f in floating_ips:
                if f.instance_id in instances_id:
                    try:
                        LOG.info('Delete floating ip %s' % f.ip)
                        manager._get_compute_client().floating_ips.delete(f.id)
                    except Exception as exc:
                        LOG.debug(exc)
                        pass
            try:
                LOG.info('Delete server with name %s' % s.name)
                manager._get_compute_client().servers.delete(s.id)
            except Exception as exc:
                LOG.debug(exc)
                pass

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
                LOG.info('Start keypair deletion')
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
    for role in roles:
        if role.name.startswith('ost1_test-'):
            try:
                LOG.info('Start roles deletion')
                manager._get_identity_client().roles.delete(role)
            except Exception as exc:
                LOG.debug(exc)
                pass

    images = manager._get_image_client().images.list()
    for image in images:
        if image.name.startswith('ost1_test-'):
            try:
                LOG.info('Start images deletion')
                manager._get_image_client().images.delete(image)
            except Exception as exc:
                LOG.debug(exc)
                pass

    snapshots = manager._get_volume_client().volume_snapshots.list()
    for snapshot in snapshots:
        if snapshot.name.startswith('ost1_test-'):
            try:
                LOG.info('Start snapshot deletion')
                manager._get_volume_client().volume_snapshots.delete(snapshot)
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

    sec_groups = manager._get_compute_client().security_groups.list()

    for sgroup in sec_groups:
        if sgroup.name.startswith('ost1_test-'):
            try:
                LOG.info('Start deletion of security groups')
                manager._get_compute_client().security_groups.delete(sgroup)
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


    networks = manager._get_compute_client().networks.list()
    for network in networks:
        if network.label.startswith('ost1_test-'):
            try:
                LOG.info('Start networks deletion')
                manager._get_compute_client().networks.delete(network)
            except Exception as exce:
                LOG.debug(exc)
                pass


if __name__ == "__main__":
    cleanup()
