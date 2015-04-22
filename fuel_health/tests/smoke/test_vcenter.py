# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import traceback

from fuel_health.common.utils.data_utils import rand_name
from fuel_health import nmanager
from fuel_health import test

LOG = logging.getLogger(__name__)


class TestVcenter(nmanager.NovaNetworkScenarioTest):
    """Test suit verifies:
     - Instance creation
     - Floating ip creation
     - Instance connectivity by floating IP
    """
    @classmethod
    def setUpClass(cls):
        super(TestVcenter, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.tenant_id = cls.manager._get_identity_client(
                cls.config.identity.admin_username,
                cls.config.identity.admin_password,
                cls.config.identity.admin_tenant_name).tenant_id
            cls.keypairs = {}
            cls.security_groups = {}
            cls.network = []
            cls.servers = []
            cls.floating_ips = []

    def setUp(self):
        super(TestVcenter, self).setUp()
        self.check_clients_state()

    def tearDown(self):
        super(TestVcenter, self).tearDown()
        if self.manager.clients_initialized:
            if self.servers:
                for server in self.servers:
                    try:
                        self._delete_server(server)
                        self.servers.remove(server)
                    except Exception:
                        LOG.debug(traceback.format_exc())
                        LOG.debug("Server was already deleted.")

    def test_1_vcenter_create_servers(self):
        """vCenter: Launch instance
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            3. Delete instance.

        Duration: 200 s.
        Available since release: 2014.2-6.1
        Deployment tags: use_vcenter
        """
        self.check_image_exists()
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25,
                self._create_security_group,
                1,
                "Security group can not be created.",
                'security group creation',
                self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]
        img_name = 'TestVM-VMDK'

        server = self.verify(
            200,
            self._create_server,
            2,
            "Creating instance using the new security group has failed.",
            'image creation',
            self.compute_client, name, security_groups, None, None, img_name
        )

        self.verify(30, self._delete_server, 3,
                    "Server can not be deleted.",
                    "server deletion", server)

    def test_3_vcenter_check_public_instance_connectivity_from_instance(self):
        """vCenter: Check network connectivity from instance via floating IP
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            3. Create a new floating IP
            4. Assign the new floating IP to the instance.
            5. Check connectivity to the floating IP using ping command.
            6. Check that public IP 8.8.8.8 can be pinged from instance.
            7. Disassociate server floating ip.
            8. Delete floating ip
            9. Delete server.

        Duration: 300 s.
        Available since release: 2014.2-6.1
        Deployment tags: nova_network, use_vcenter
        """
        self.check_image_exists()
        if not self.security_groups:
                self.security_groups[self.tenant_id] = self.verify(
                    25, self._create_security_group, 1,
                    "Security group can not be created.",
                    'security group creation',
                    self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]
        img_name = 'TestVM-VMDK'

        server = self.verify(250, self._create_server, 2,
                             "Server can not be created.",
                             "server creation",
                             self.compute_client, name, security_groups, None,
                             None, img_name)

        floating_ip = self.verify(
            20,
            self._create_floating_ip,
            3,
            "Floating IP can not be created.",
            'floating IP creation')

        self.verify(10, self._assign_floating_ip_to_instance,
                    4, "Floating IP can not be assigned.",
                    'floating IP assignment',
                    self.compute_client, server, floating_ip)

        self.floating_ips.append(floating_ip)

        ip_address = floating_ip.ip
        LOG.info('is address is  {0}'.format(ip_address))
        LOG.debug(ip_address)

        self.verify(600, self._check_vm_connectivity, 5,
                    "VM connectivity doesn`t function properly.",
                    'VM connectivity checking', ip_address,
                    30, (6, 60))

        self.verify(600, self._check_connectivity_from_vm,
                    6, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                        "function properly."),
                    'public connectivity checking from VM', ip_address,
                    30, (6, 60))

        self.verify(10, self.compute_client.servers.remove_floating_ip,
                    7, "Floating IP cannot be removed.",
                    "removing floating IP", server, floating_ip)

        self.verify(10, self.compute_client.floating_ips.delete,
                    8, "Floating IP cannot be deleted.",
                    "floating IP deletion", floating_ip)

        if self.floating_ips:
            self.floating_ips.remove(floating_ip)

        self.verify(30, self._delete_server, 9,
                    "Server can not be deleted. ",
                    "server deletion", server)

    def test_2_vcenter_check_internet_connectivity_without_floatingIP(self):
        """vCenter: Check network connectivity from instance without floating \
            IP
        Target component: Nova

        Scenario:
            1. Create a new security group (if it doesn`t exist yet).
            2. Create an instance using the new security group.
            (if it doesn`t exist yet).
            3. Check that public IP 8.8.8.8 can be pinged from instance.
            4. Delete server.

        Duration: 300 s.
        Available since release: 2014.2-6.1
        Deployment tags: nova_network, use_vcenter
        """
        self.check_image_exists()
        if not self.security_groups:
            self.security_groups[self.tenant_id] = self.verify(
                25, self._create_security_group, 1,
                "Security group can not be created.",
                'security group creation', self.compute_client)

        name = rand_name('ost1_test-server-smoke-')
        security_groups = [self.security_groups[self.tenant_id].name]
        img_name = 'TestVM-VMDK'
        compute = None

        server = self.verify(
            250, self._create_server, 2,
            "Server can not be created.",
            'server creation',
            self.compute_client, name, security_groups, None, None, img_name)

        try:
            for addr in server.addresses:
                if addr.startswith('novanetwork'):
                    instance_ip = server.addresses[addr][0]['addr']
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("Step 3 failed: cannot get instance details. "
                      "Please refer to OpenStack logs for more details.")

        self.verify(400, self._check_connectivity_from_vm,
                    3, ("Connectivity to 8.8.8.8 from the VM doesn`t "
                        "function properly."),
                    'public connectivity checking from VM',
                    instance_ip, 30, (6, 30), compute)

        self.verify(30, self._delete_server, 4,
                    "Server can not be deleted. ",
                    "server deletion", server)


class TestVcenterImageAction(nmanager.SmokeChecksTest):
    """Test class verifies the following:
      - verify that image can be created;
      - verify that instance can be booted from created image;
      - verify that snapshot can be created from an instance;
      - verify that instance can be booted from a snapshot.
    """
    @classmethod
    def setUpClass(cls):
        super(TestVcenterImageAction, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.micro_flavors = cls.find_micro_flavor()

    @classmethod
    def tearDownClass(cls):
        super(TestVcenterImageAction, cls).tearDownClass()

    def setUp(self):
        super(TestVcenterImageAction, self).setUp()
        self.check_clients_state()
        self.check_image_exists()

    def _wait_for_server_status(self, server, status):
        self.status_timeout(self.compute_client.servers,
                            server.id,
                            status)

    def _wait_for_image_status(self, image_id, status):
        self.status_timeout(self.compute_client.images, image_id, status)

    def _wait_for_server_deletion(self, server):
        def is_deletion_complete():
                # Deletion testing is only required for objects whose
                # existence cannot be checked via retrieval.
                if isinstance(server, dict):
                    return True
                try:
                    server.get()
                except Exception as e:
                    # Clients are expected to return an exception
                    # called 'NotFound' if retrieval fails.
                    if e.__class__.__name__ == 'NotFound':
                        return True
                    self.error_msg.append(e)
                    LOG.debug(traceback.format_exc())
                return False

        # Block until resource deletion has completed or timed-out
        test.call_until_true(is_deletion_complete, 10, 1)

    def _boot_image(self, image_id):
        if not self.micro_flavors:
            self.fail("Flavor for tests was not found. Seems that "
                      "something is wrong with nova services.")

        name = rand_name('ost1_test-image')
        client = self.compute_client
        LOG.debug("name:%s, image:%s" % (name, image_id))
        if 'neutron' in self.config.network.network_provider:
            network = [net.id for net in
                       self.compute_client.networks.list()
                       if net.label == self.private_net]
            if network:
                create_kwargs = {
                    'nics': [
                        {'net-id': network[0]},
                    ],
                }
            else:
                self.fail("Default private network '{0}' isn't present."
                          "Please verify it is properly created.".
                          format(self.private_net))
            server = client.servers.create(name=name,
                                           image=image_id,
                                           flavor=self.micro_flavors[0],
                                           **create_kwargs)
        else:
            server = client.servers.create(name=name,
                                           image=image_id,
                                           flavor=self.micro_flavors[0])
        self.set_resource(name, server)
        # self.addCleanup(self.compute_client.servers.delete, server)
        self.verify_response_body_content(
            name, server.name,
            msg="Please refer to OpenStack logs for more details.")
        self._wait_for_server_status(server, 'ACTIVE')
        server = client.servers.get(server)  # getting network information
        LOG.debug("server:%s" % server)
        return server

    def _create_image(self, server):
        snapshot_name = rand_name('ost1_test-snapshot-')
        create_image_client = self.compute_client.servers.create_image
        image_id = create_image_client(server, snapshot_name)
        self.addCleanup(self.compute_client.images.delete, image_id)
        self._wait_for_server_status(server, 'ACTIVE')
        self._wait_for_image_status(image_id, 'ACTIVE')
        snapshot_image = self.compute_client.images.get(image_id)
        self.verify_response_body_content(
            snapshot_name, snapshot_image.name,
            msg="Please refer to OpenStack logs for more details.")
        return image_id

    def test_4_snapshot(self):
        """vCenter: Launch instance, create snapshot, launch instance from \
            snapshot
        Target component: Glance

        Scenario:
            1. Get existing image by name.
            2. Launch an instance using the default image.
            3. Make snapshot of the created instance.
            4. Delete the instance created in step 1.
            5. Wait while instance deleted
            6. Launch another instance from the snapshot created in step 2.
            7. Delete server.

        Duration: 300 s.
        Available since release: 2014.2-6.1
        Deployment tags: nova_network, use_vcenter
        """

        img_name = 'TestVM-VMDK'
        image = self.verify(30, self.get_image_from_name, 1,
                            "Image can not be retrieved.",
                            "getting image by name",
                            img_name)

        server = self.verify(180, self._boot_image, 2,
                             "Image can not be booted.",
                             "image booting",
                             image)

        # snapshot the instance
        snapshot_image_id = self.verify(700, self._create_image, 3,
                                        "Snapshot of an"
                                        " instance can not be created.",
                                        'snapshotting an instance',
                                        server)

        self.verify(180, self.compute_client.servers.delete, 4,
                    "Instance can not be deleted.",
                    'Instance deletion',
                    server)

        self.verify(180, self._wait_for_server_deletion, 5,
                    "Instance can not be deleted.",
                    'Wait for instance deletion complete',
                    server)

        server = self.verify(700, self._boot_image, 6,
                             "Instance can not be launched from snapshot.",
                             'booting instance from snapshot',
                             snapshot_image_id)

        self.verify(30, self._delete_server, 7,
                    "Server can not be deleted.",
                    "server deletion", server)


class VcenterVolumesTest(nmanager.SmokeChecksTest):

    @classmethod
    def setUpClass(cls):
        super(VcenterVolumesTest, cls).setUpClass()
        if cls.manager.clients_initialized:
            cls.micro_flavors = cls.find_micro_flavor()

    def setUp(self):
        super(VcenterVolumesTest, self).setUp()
        self.check_clients_state()
        if (not self.config.volume.cinder_vmware_node_exist):
            self.skipTest('There are no cinder-vmware nodes')
        self.check_image_exists()

    @classmethod
    def tearDownClass(cls):
        super(VcenterVolumesTest, cls).tearDownClass()

    def _wait_for_volume_status(self, volume, status):
        self.status_timeout(self.volume_client.volumes, volume.id, status)

    def _wait_for_instance_status(self, server, status):
        self.status_timeout(self.compute_client.servers, server.id, status)

    def test_5_vcenter_volume_create(self):
        """vCenter: Create volume and attach it to instance
        Target component: Compute

        Scenario:
            1. Create a new small-size volume.
            2. Wait for volume status to become "available".
            3. Check volume has correct name.
            4. Create new instance.
            5. Wait for "Active" status
            6. Attach volume to an instance.
            7. Check volume status is "in use".
            8. Get information on the created volume by its id.
            9. Detach volume from the instance.
            10. Check volume has "available" status.
            11. Delete volume.
            12. Verify that volume deleted
            13. Delete server.

        Duration: 350 s.
        Available since release: 2014.2-6.1
        Deployment tags: nova_network, use_vcenter
        """
        msg_s1 = 'Volume was not created.'
        img_name = 'TestVM-VMDK'
        az = self.config.volume.cinder_vmware_storage_az
        # Create volume
        volume = self.verify(120, self._create_volume, 1,
                             msg_s1,
                             "volume creation",
                             self.volume_client, None, availability_zone=az)

        self.verify(200, self._wait_for_volume_status, 2,
                    msg_s1,
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify_response_true(
            volume.display_name.startswith('ostf-test-volume'),
            'Step 3 failed: {msg}'.format(msg=msg_s1))

        # create instance
        instance = self.verify(200, self._create_server, 4,
                               "Instance creation failed. ",
                               "server creation",
                               self.compute_client, img_name)

        self.verify(200, self._wait_for_instance_status, 5,
                    'Instance status did not become "available".',
                    "instance becoming 'available'",
                    instance, 'ACTIVE')

        # Attach volume
        self.verify(120, self._attach_volume_to_instance, 6,
                    'Volume couldn`t be attached.',
                    'volume attachment',
                    volume, instance.id)

        self.verify(180, self._wait_for_volume_status, 7,
                    'Attached volume status did not become "in-use".',
                    "volume becoming 'in-use'",
                    volume, 'in-use')

        # get volume details
        self.verify(20, self.volume_client.volumes.get, 8,
                    "Can not retrieve volume details. ",
                    "retrieving volume details", volume.id)

        # detach volume
        self.verify(50, self._detach_volume, 9,
                    'Can not detach volume. ',
                    "volume detachment",
                    instance.id, volume.id)

        self.verify(120, self._wait_for_volume_status, 10,
                    'Volume status did not become "available".',
                    "volume becoming 'available'",
                    volume, 'available')

        self.verify(50, self.volume_client.volumes.delete, 11,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)

        self.verify(50, self.verify_volume_deletion, 12,
                    'Can not delete volume. ',
                    "volume deletion",
                    volume)

        self.verify(30, self._delete_server, 13,
                    "Can not delete server. ",
                    "server deletion",
                    instance)
