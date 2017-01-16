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

from oslo_log import log as logging

from fuel_health import ha_base


LOG = logging.getLogger(__name__)


class RabbitSanityTest(ha_base.RabbitSanityClass):
    """TestClass contains RabbitMQ test checks."""

    def setUp(self):
        super(RabbitSanityTest, self).setUp()
        if 'ha' not in self.config.mode:
            self.skipTest("It is not HA configuration")
        if not self._controllers:
            self.skipTest('There are no controller nodes')
        if len(self.amqp_hosts_name) == 1:
            self.skipTest('There is only one RabbitMQ node online. '
                          'Nothing to check')

    def test_001_rabbitmqctl_status(self):
        """Check RabbitMQ is available

        Scenario:
          1. Retrieve cluster status for each controller.
          2. Check that numbers of rabbit nodes is the same
             in Hiera DB and in actual cluster.
          3. Check crm status for rabbit
          4. List channels
        Duration: 100 s.
        Deployment tags: CENTOS
        """
        self.verify(20, self.list_nodes, 1,
                    'Cannot retrieve cluster nodes')

        if len(self.amqp_hosts_name) != self.list_nodes():
            self.fail('Step 2 failed: Number of RabbitMQ nodes '
                      'is not equal to number of cluster nodes.')

        res = self.verify(20, self.pick_rabbit_master, 3,
                          'Cannot retrieve crm status')

        LOG.debug("Current res is {0}".format(res))

        if not res:
            LOG.debug("Current res is {0}".format(res))
            self.fail('Step 3 failed: Rabbit Master node is not running.')

        fail_msg_4 = 'Can not get rabbit channel list in 40 seconds.'

        self.verify(40, self.list_channels, 4, fail_msg_4,
                    'Can not retrieve channels list')

    def test_002_rabbitmqctl_status_ubuntu(self):
        """RabbitMQ availability
        Scenario:
          1. Retrieve cluster status for each controller.
          2. Check that numbers of rabbit nodes is the same
             in Hiera DB and in actual cluster.
          3. Check crm status for rabbit
          4. List channels
        Duration: 100 s.
        Deployment tags: Ubuntu
        """
        self.verify(20, self.list_nodes, 1, 'Cannot retrieve cluster nodes')

        if len(self.amqp_hosts_name) != self.list_nodes():
            self.fail('Step 2 failed: Number of RabbitMQ nodes '
                      'is not equal to number of cluster nodes.')

        res = self.verify(20, self.pick_rabbit_master, 3,
                          'Cannot retrieve crm status')

        LOG.debug("Current res is {0}".format(res))

        if not res:
            LOG.debug("Current res is {0}".format(res))
            self.fail('Step 3 failed: Rabbit Master node is not running.')

        fail_msg_4 = 'Can not get rabbit channel list in 40 seconds.'

        self.verify(40, self.list_channels, 4, fail_msg_4,
                    'Can not retrieve channels list')

    def test_003_rabbitmqctl_replication(self):
        """RabbitMQ replication
        Scenario:
          1. Check rabbitmq connections.
          2. Create queue.
          3. Publish test message in created queue
          4. Request created queue and message
          5. Delete queue
        Duration: 100 s.
        Available since release: 2014.2-6.1
        """
        self.verify(40, self.check_rabbit_connections, 1,
                    'Cannot retrieve cluster nodes')

        self.verify(60, self.create_queue, 2,
                    'Failed to create queue')

        self.verify(40, self.publish_message, 3,
                    'Failed to publish message')

        self.verify(40, self.check_queue_message_replication, 4,
                    'Consume of message failed')

        self.verify(40, self.delete_queue, 5,
                    'Failed to delete queue')
