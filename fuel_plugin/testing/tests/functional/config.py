#    Copyright 2013 Mirantis, Inc.
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

CONFIG = {
    'compute-admin_password': 'nova',
    'compute-admin_tenant_name': '',
    'compute-admin_username': '',
    'compute_allow_tenant_isolation': 'True',
    'compute_allow_tenant_reuse': 'true',
    'compute_block_migrate_supports_cinder_iscsi': 'false',
    'compute_build_interval': '3',
    'compute_build_timeout': '300',
    'compute_catalog_type': 'compute',
    'compute_change_password_available': 'False',
    'compute_controller_node': '10.30.1.101',
    'compute_controller_node_name': 'fuel-controller-01.localdomain.',
    'compute_controller_node_ssh_password': 'r00tme',
    'compute_controller_node_ssh_user': 'root',
    'compute_create_image_enabled': 'true',
    'compute_disk_config_enabled_override': 'true',
    'compute_enabled_services': (
        'nova-cert, nova-consoleauth, nova-scheduler, '
        'nova-conductor, nova-cert, nova-consoleauth, '
        'nova-scheduler, nova-conductor, nova-cert, '
        'nova-consoleauth, nova-scheduler, '
        'nova-conductor, nova-compute'
    ),
    'compute_fixed_network_name': 'private',
    'compute_flavor_ref': '1',
    'compute_flavor_ref_alt': '2',
    'compute_image_alt_ssh_user': 'cirros',
    'compute_image_ref': '53734a0d-60a8-4689-b7c8-3c14917a7197',
    'compute_image_ref_alt': '53734a0d-60a8-4689-b7c8-3c14917a7197',
    'compute_image_ssh_user': 'cirros',
    'compute_ip_version_for_ssh': '4',
    'compute_live_migration_available': 'False',
    'compute_network_for_ssh': 'private',
    'compute_resize_available': 'true',
    'compute_run_ssh': 'false',
    'compute_ssh_channel_timeout': '60',
    'compute_ssh_timeout': '300',
    'compute_ssh_user': 'cirros',
    'compute_use_block_migration_for_live_migration': 'False',
    'identity_admin_password': 'nova',
    'identity_admin_tenant_name': 'admin',
    'identity_admin_username': 'admin',
    'identity_alt_password': 'nova',
    'identity_alt_tenant_name': 'alt_demo',
    'identity_alt_username': 'alt_demo',
    'identity_catalog_type': 'identity',
    'identity_disable_ssl_certificate_validation': 'False',
    'identity_password': 'nova',
    'identity_region': 'RegionOne',
    'identity_strategy': 'keystone',
    'identity_tenant_name': 'admin',
    'identity_uri': 'http://172.18.164.70:5000/v2.0/',
    'identity_url': 'http://172.18.164.70/',
    'identity_username': 'admin',
    'image_api_version': '1',
    'image_catalog_type': 'image',
    'image_http_image': ('http://download.cirros-cloud.net/'
                         '0.3.1/cirros-0.3.1-x86_64-uec.tar.gz'),
    'network_api_version': '2.0',
    'network_catalog_type': 'network',
    'network_public_network_id': 'cdb94175-2002-449f-be41-6b8afce8de13',
    'network_public_router_id': '2a6bf65b-01f7-4c91-840a-2b5f676e7016',
    'network_quantum_available': 'true',
    'network_tenant_network_cidr': '10.13.0.0/16',
    'network_tenant_network_mask_bits': '28',
    'network_tenant_networks_reachable': 'true',
    'object-storage_catalog_type': 'object-store',
    'object-storage_container_sync_interval': '5',
    'object-storage_container_sync_timeout': '120',
    'smoke_allow_tenant_isolation': 'True',
    'smoke_allow_tenant_reuse': 'true',
    'smoke_block_migrate_supports_cinder_iscsi': 'false',
    'smoke_build_interval': '3',
    'smoke_build_timeout': '300',
    'smoke_catalog_type': 'compute',
    'smoke_change_password_available': 'False',
    'smoke_create_image_enabled': 'true',
    'smoke_disk_config_enabled_override': 'true',
    'smoke_fixed_network_name': 'net04',
    'smoke_flavor_ref': '1',
    'smoke_flavor_ref_alt': '2',
    'smoke_image_alt_ssh_user': 'cirros',
    'smoke_image_ref': '53734a0d-60a8-4689-b7c8-3c14917a7197',
    'smoke_image_ref_alt': '53734a0d-60a8-4689-b7c8-3c14917a7197',
    'smoke_image_ssh_user': 'cirros',
    'smoke_ip_version_for_ssh': '4',
    'smoke_live_migration_available': 'False',
    'smoke_network_for_ssh': 'net04',
    'smoke_resize_available': 'true',
    'smoke_run_ssh': 'false',
    'smoke_ssh_channel_timeout': '60',
    'smoke_ssh_timeout': '320',
    'smoke_ssh_user': 'cirros',
    'smoke_use_block_migration_for_live_migration': 'False',
    'volume_backend1_name': 'BACKEND_1',
    'volume_backend2_name': 'BACKEND_2',
    'volume_build_interval': '3',
    'volume_build_timeout': '300',
    'volume_catalog_type': 'volume',
    'volume_multi_backend_enabled': 'false'
}
