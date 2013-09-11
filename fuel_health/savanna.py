# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import savannaclient.api.client
import nmanager

LOG = logging.getLogger(__name__)


class SavannaClientManager(nmanager.OfficialClientManager):
    """
    Manager that provides access to the Savanna python client for
    calling Savanna API.
    """
    #TBD should be moved to nailgun or config file
    savanna_url = 'http://10.20.0.131:8386/v1.0'

    def __init__(self):
        """
        This method allows to initialize authentication before
        each test case and define parameters of
        Savanna API Service
        """
        super(SavannaClientManager, self).__init__()
        self.savanna_client = self._get_savanna_client()
        self.client_attr_names.append('savanna_client')

    def _get_savanna_client(self, username=None, password=None):
        keystone = self._get_identity_client()
        auth_url = self.config.identity.uri
        tenant_name = self.config.identity.admin_tenant_name
        if not username:
            username = self.config.identity.admin_username
        if not password:
            password = self.config.identity.admin_password
        return savannaclient.api.client.Client(username=username,
                                               api_key=password,
                                               project_name=tenant_name,
                                               auth_url=auth_url,
                                               savanna_url=self.savanna_url)


class SavannaOfficialClientTest(nmanager.OfficialClientTest):
    manager_class = SavannaClientManager


class SavannaSanityChecksTest(SavannaOfficialClientTest):
    """
    Base class for openstack sanity tests for Savanna
    """
    #TBD should be movede to nailgun or config file
    plugin = 'vanilla'
    plugin_version = '1.1.2'

    def _create_node_group_template_and_get_id(
            self, client, name, plugin_name,
            hadoop_version, description,
            volumes_per_node, volume_size,
            node_processes, node_configs):

        data = client.node_group_templates.create(
            name, plugin_name, hadoop_version, '42', description,
            volumes_per_node, volume_size, node_processes, node_configs
        )
        node_group_template_id = str(data.id)

        return node_group_template_id

    def _create_node_group_template_tt_dn_id(self, client):
        node_group_template_tt_dn_id = \
            self._create_node_group_template_and_get_id(
                client,
                'tt-dn',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=1,
                node_processes=['tasktracker', 'datanode'],
                node_configs={
                    #'HDFS': hc.DN_CONFIG,
                    #'MapReduce': '515'
                }
            )
        return node_group_template_tt_dn_id

    def _create_node_group_template_tt_id(self, client):
        node_group_template_tt_id = \
            self._create_node_group_template_and_get_id(
                client,
                'tt',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['tasktracker'],
                node_configs={
                    #'MapReduce': hc.TT_CONFIG
                }
            )
        return node_group_template_tt_id

    def _create_node_group_template_dn_id(self, client):
        node_group_template_tt_id = \
            self._create_node_group_template_and_get_id(
                client,
                'dd',
                self.plugin,
                self.plugin_version,
                description='test node group template',
                volumes_per_node=0,
                volume_size=0,
                node_processes=['datanode'],
                node_configs={
                    #'MapReduce': hc.TT_CONFIG
                }
            )
        LOG.debug(node_group_template_tt_id)
        return node_group_template_tt_id

    def _delete_node_group_template(self, client, id):
        client.node_group_templates.delete(id)

    def _list_node_group_template(self, client):
        client.node_group_templates.list()

    def _list_cluster_templates(self, client):
        cluster_templates = client.cluster_templates.list()
        return cluster_templates

    def _create_cluster_templates(self, client):
        cluster_templates = client.cluster_templates.create(
            'name', plugin,
            self.plugin_version, 'descr',
            cluster_configs,
            node_groups,
            anti_affinity)
        return cluster_templates
