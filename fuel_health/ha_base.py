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

import kombu
from kombu import Connection
import logging
from lxml import etree
import time
import traceback

import fuel_health
from fuel_health.common import ssh
from fuel_health.common.utils import data_utils
from fuel_health.test import BaseTestCase


LOG = logging.getLogger(__name__)


class RabbitSanityClass(BaseTestCase):
    """TestClass contains RabbitMQ sanity checks."""

    @classmethod
    def setUpClass(cls):
        cls.config = fuel_health.config.FuelConfig()
        cls._controllers = cls.config.compute.online_controllers
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.path_to_private_key
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls.connections = []
        cls.ids = []
        cls.queues = []
        cls.data = []

    def get_ssh_connection_to_controller(self, controller):
        remote = ssh.Client(host=controller,
                            username=self._usr,
                            password=self._pwd,
                            key_filename=self._key,
                            timeout=self._ssh_timeout)
        return remote

    def list_nodes(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        output = remote.exec_command("rabbitmqctl cluster_status")
        substring_ind = output.find('{running_nodes')
        sub_end_ind = output.find('cluster_name')
        result_str = output[substring_ind: sub_end_ind]
        num_node = result_str.count("rabbit@")
        return num_node

    def pick_rabbit_master(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        LOG.info('ssh session  to node {0} was open'.format(
            self._controllers[0]))
        LOG.info('Try to execute command <crm resource '
                 'status master_p_rabbitmq-server>')
        output = remote.exec_command(
            "crm resource status master_p_rabbitmq-server")
        LOG.debug('Output is {0}'.format(output))
        substring_ind = output.find(
            'resource master_p_rabbitmq-server is running on:')
        sub_end_ind = output.find('Master')
        LOG.debug('Start index is {0} end'
                  ' index is {1}'.format(substring_ind, sub_end_ind))
        result_str = output[substring_ind: sub_end_ind]
        LOG.debug('Result string is {0}'.format(result_str))
        return result_str

    def list_channels(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        output = remote.exec_command("rabbitmqctl list_channels")
        if 'done' not in output:
            self.fail('Get channels list command fail.')
        else:
            LOG.debug('Result of executing command rabbitmqctl'
                      ' list_channels is {0}'.format(output))
            return output

    def get_conf_values(self, variable="rabbit_password",
                        sections="DEFAULT",
                        conf_path="/etc/nova/nova.conf"):
        cmd = ("python -c 'import ConfigParser; "
               "cfg=ConfigParser.ConfigParser(); "
               "cfg.readfp(open('\"'{0}'\"')); "
               "print cfg.get('\"'{1}'\"', '\"'{2}'\"')'")
        LOG.debug("Try to execute cmd {0}".format(cmd))
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        try:
            res = remote.exec_command(cmd.format(
                conf_path, sections, variable))
            LOG.debug("result is {0}".format(res))
            return res
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("Fail to get data from config")

    def check_rabbit_connections(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        pwd = self.get_conf_values().strip()
        for host in self._controllers:
            try:
                conn = Connection(host, userid='nova',
                                  password=pwd,
                                  virtual_host='/', port=5673)
                conn.connect()

                channel = conn.channel()
                self.connections.append((channel, host))
                LOG.debug('connections is {0}'.format(self.connections))
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("Failed to connect to "
                          "5673 port on host {0}".format(host))

    def create_queue(self):
        for channel, host in self.connections:
            test_queue = data_utils.rand_name() + data_utils.generate_uuid()
            queue = kombu.Queue(
                'test-rabbit-{0}-{1}'.format(test_queue, host),
                channel=channel,
                durable=False,
                queue_arguments={'x-expires': 15 * 60 * 1000})
            try:
                LOG.debug("Declaring queue {0} on host {1}".format(
                    queue.name, host))
                queue.declare()
                self.data.append((channel, host, queue))
                self.queues.append(queue)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("Failed to declare queue on host {0}".format(host))

    def publish_message(self):
        for channel, host, queue in self.data:
            self.ids.append(data_utils.generate_uuid())
            try:
                LOG.debug('Try to publish message {0}'.format(queue.name))
                producer = kombu.Producer(
                    channel=channel, routing_key=queue.name)
                for msg_id in self.ids:
                    producer.publish(msg_id)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("failed to publish message")

    def check_queue_message_replication(self):
        for channel, host, queue in self.data:
            rec_queue = kombu.Queue(queue.name, channel=channel)
            try:
                msg = None
                for i in range(10):
                    LOG.debug('messages ids are {0}'.format(self.ids))
                    msg = rec_queue.get(True)
                    LOG.debug('Message is {0}'.format(msg.body))
                    if msg is None:
                        time.sleep(1)
                    else:
                        break
                if msg is None:
                    self.fail("No message received")
                elif msg.body not in self.ids:
                    self.fail('received incorrect message {0}'
                              ' in ids  {1}'.format(msg.body, self.ids))
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail('Failed to check message replication')

    def delete_queue(self):
        LOG.debug('Try to deleting queue {0}... '.format(self.queues))
        if self.queues:
            try:
                self.ids = []
                [queue.delete() and self.queues.remove(queue)
                 for queue in self.queues]
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail('Failed to delete queue')


class TestPacemakerBase(fuel_health.cloudvalidation.CloudValidationTest):
    """TestPacemakerStatus class base methods."""

    @classmethod
    def setUpClass(cls):
        super(TestPacemakerBase, cls).setUpClass()
        cls.controller_names = cls.config.compute.controller_names
        cls.online_controller_names = (
            cls.config.compute.online_controller_names)
        cls.offline_controller_names = list(
            set(cls.controller_names) - set(cls.online_controller_names))

        cls.online_controller_ips = cls.config.compute.online_controllers
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.ssh_user

    def setUp(self):
        super(TestPacemakerBase, self).setUp()
        if 'ha' not in self.config.mode:
            self.skipTest('Cluster is not HA mode, skipping tests')
        if not self.online_controller_names:
            self.skipTest('There are no controller nodes')

    def _register_resource(self, res, resources):
        res_name = res.get('id')
        if res_name not in resources:
            resources[res_name] = {
                'master': [],
                'nodes': [],
                'started': 0,
                'stopped': 0,
                'active': False}

        if 'true' in res.get('active'):
            resources[res_name]['active'] = True

        res_role = res.get('role')
        num_nodes = int(res.get('nodes_running_on'))

        if num_nodes:
            resources[res_name]['started'] += num_nodes

            for rnode in res.iter('node'):
                if 'Master' in res_role:
                    resources[res_name]['master'].append(
                        rnode.get('name'))
                resources[res_name]['nodes'].append(
                    rnode.get('name'))
        else:
            resources[res_name]['stopped'] += 1

    def get_pcs_resources(self, pcs_status):
        """Get pacemaker resources status to a python dict:
            return:
                {
                  str: {                        # Resource name
                    'started': int,             # count of Master/Started
                    'stopped': int,             # count of Stopped resources
                    'nodes':  [node_name, ...], # All node names where the
                                                # resource is started
                    'master': [node_name, ...], # Node names for 'Master'
                                                # ('master' is also in 'nodes')
                  },
                  ...
                }
        """
        root = etree.fromstring(pcs_status)
        resources = {}

        for res_group in root.iter('resources'):
            for res in res_group:
                if 'resource' in res.tag:
                    self._register_resource(res, resources)
                elif 'clone' in res.tag:
                    for r in res:
                        self._register_resource(r, resources)

        return resources

    def get_pcs_nodes(self, pcs_status):
        root = etree.fromstring(pcs_status)
        nodes = {'Online': [], 'Offline': []}
        for nodes_group in root.iter('nodes'):
            for node in nodes_group:
                if 'true' in node.get('online'):
                    nodes['Online'].append(node.get('name'))
                else:
                    nodes['Offline'].append(node.get('name'))
        return nodes
