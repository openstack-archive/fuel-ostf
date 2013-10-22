# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import logging
LOG = logging.getLogger(__name__)


def create_cluster(self, name, plugin_name, hadoop_version,
                   cluster_template_id=None, default_image_id=None,
                   description=None, cluster_configs=None, node_groups=None,
                   user_keypair_id=None, anti_affinity=None, net_id=None):
    # expecting node groups to be array of dictionaries
    data = {
        'name': name,
        'plugin_name': plugin_name,
        'hadoop_version': hadoop_version
    }
    LOG.debug("Network id is '%s'" % net_id)
    if cluster_template_id is None:
        self._assert_variables(default_image_id=default_image_id,
                               cluster_configs=cluster_configs,
                               node_groups=node_groups)

    self._copy_if_defined(data,
                          cluster_template_id=cluster_template_id,
                          default_image_id=default_image_id,
                          description=description,
                          cluster_configs=cluster_configs,
                          node_groups=node_groups,
                          user_keypair_id=user_keypair_id,
                          anti_affinity=anti_affinity,
                          neutron_management_network=net_id)

    return self._create('/clusters', data, 'cluster')


def create_cluster_template(self, name, plugin_name, hadoop_version,
                            description, cluster_configs, node_groups,
                            anti_affinity, net_id=None):
    # expecting node groups to be array of dictionaries
    data = {
        'name': name,
        'plugin_name': plugin_name,
        'hadoop_version': hadoop_version,
        'description': description,
        'cluster_configs': cluster_configs,
        'node_groups': node_groups,
        'anti_affinity': anti_affinity
    }

    if net_id:
        data.update({'neutron_management_network': net_id})

    return self._create('/cluster-templates', data, 'cluster_template')


def create_nodegroup_template(self, name, plugin_name, hadoop_version,
                              flavor_id, description=None,
                              volumes_per_node=None, volumes_size=None,
                              node_processes=None, node_configs=None,
                              floating_ip_pool=None):

    data = {
        'name': name,
        'plugin_name': plugin_name,
        'hadoop_version': hadoop_version,
        'description': description,
        'flavor_id': flavor_id,
        'node_processes': node_processes,
        'node_configs': node_configs
    }

    if floating_ip_pool:
        data.update({"floating_ip_pool": floating_ip_pool})

    if volumes_per_node:
        data.update({"volumes_per_node": volumes_per_node,
                    "volumes_size": volumes_size})

    return self._create('/node-group-templates', data, 'node_group_template')


def patch_client():
    from savannaclient.api import cluster_templates
    from savannaclient.api import clusters
    from savannaclient.api import node_group_templates as ng_templates

    clusters.ClusterManager.create = create_cluster
    cluster_templates.ClusterTemplateManager.create = create_cluster_template
    ng_templates.NodeGroupTemplateManager.create = create_nodegroup_template
