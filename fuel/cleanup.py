#!/usr/bin/env python
import os
import sys

path = os.getcwd()
sys.path.append(path)

from fuel import clients


def cleanup():
    admin_manager = clients.AdminManager()
    instances_id = []

    _, body = admin_manager.servers_client.list_servers({'all_tenants': True})
    _, floating_ips = admin_manager.floating_ips_client.list_floating_ips()
    for s in body['servers']:
        if s['name'].startswith('ost1_test-'):
            instances_id.append(s['id'])
            for f in floating_ips:
                if f['instance_id'] in instances_id:
                    try:
                        admin_manager.floating_ips_client.delete_floating_ip(
                            f['id'])
                    except Exception:
                        pass
            try:
                admin_manager.servers_client.delete_server(s['id'])
            except Exception:
                pass

    for s in body['servers']:
        try:
            admin_manager.servers_client.wait_for_server_termination(s['id'])
        except Exception:
            pass

    _, keypairs = admin_manager.keypairs_client.list_keypairs()
    for k in keypairs:
        if k['keypair']['name'].startswith('ost1_test-'):
            try:
                admin_manager.keypairs_client.delete_keypair(
                    k['keypair']['name'])
            except Exception:
                pass

    _, users = admin_manager.identity_client.get_users()
    for user in users['users']:
        if user['name'].startswith('ost1_test-'):
            admin_manager.identity_client.delete_user(user['id'])

    _, tenants = admin_manager.identity_client.list_tenants()
    for tenant in tenants:
        if tenant['name'].startswith('ost1_test-'):
            admin_manager.identity_client.delete_tenant(tenant['id'])

    _, roles = admin_manager.identity_client.list_roles()
    for role in roles:
        if role['name'].startswith('ost1_test-'):
            admin_manager.identity_client.delete_role(role['id'])

    _, images = admin_manager.images_client.list_images()
    for image in images['images']:
        if image['name'].startswith('ost1_test-'):
            admin_manager.images_client.delete_image(image['id'])

    _, snapshots = admin_manager.snapshots_client.list_snapshots()
    for snapshot in snapshots['snapshots']:
        if snapshot['name'].startswith('ost1_test-'):
            admin_manager.snapshots_client.delete_snapshot(snapshot['id'])

    _, volumes = admin_manager.volumes_client.list_volumes()

    for volume in volumes['volumes']:
        if volume['display_name'].startswith('ost1_test-'):
            admin_manager.volumes_client.delete_volume(volume['id'])

    _, flavors = admin_manager.flavors_client.list_flavors()

    for flavor in flavors['flavors']:
        if flavor['name'].startswith('ost1_test-'):
            admin_manager.flavors_client.delete_flavor(flavor['id'])

    _, sec_groups = admin_manager.security_groups_client.list_security_groups()

    for sgroup in sec_groups:
        if sgroup['name'].startswith('ost1_test-'):
            admin_manager.security_groups_client.delete_security_group(
                sgroup['id'])

    _, vtypes = admin_manager.volume_types_client.list_volume_types()
    for vtype in vtypes:
        if vtype['name'].startswith('ost1_test-'):
            admin_manager.volume_types_client.delete_volume_type(vtype['id'])

    try:
        _, networks = admin_manager.network_client.list_networks()
        for network in networks['networks']:
            if network['name'].startswith('ost1_test-'):
                try:
                    admin_manager.network_client.delete_network(network['id'])
                except Exception:
                    pass
    except Exception:
        print 'Quantum is disable'


if __name__ == "__main__":
    cleanup()
