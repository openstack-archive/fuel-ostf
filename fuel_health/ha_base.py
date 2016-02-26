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

from distutils import version
import json
import logging
from lxml import etree
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
        cls.nodes = cls.config.compute.nodes
        cls._usr = cls.config.compute.controller_node_ssh_user
        cls._pwd = cls.config.compute.controller_node_ssh_password
        cls._key = cls.config.compute.path_to_private_key
        cls._ssh_timeout = cls.config.compute.ssh_timeout
        cls._password = None
        cls._userid = None
        cls.messages = []
        cls.queues = []
        cls.release_version = \
            cls.config.compute.release_version.split('-')[1]

    @property
    def password(self):
        if version.StrictVersion(self.release_version)\
                < version.StrictVersion('7.0'):
            self._password = self.get_conf_values().strip()
            return self._password

        if self._password is None:
            self._password = self.get_hiera_values(
                hiera_hash='rabbit_hash',
                hash_key='password'
            )
        return self._password

    @property
    def amqp_hosts_name(self):
        amqp_hosts_name = {}
        if version.StrictVersion(self.release_version)\
                < version.StrictVersion('7.0'):
            for controller_ip in self._controllers:
                amqp_hosts_name[controller_ip] = [controller_ip, '5673']
            return amqp_hosts_name

        nodes = self.get_hiera_values(hiera_hash='network_metadata',
                                      hash_key='nodes',
                                      json_parse=True)
        for ip, port in self.get_amqp_hosts():
            for node in nodes:
                ips = [nodes[node]['network_roles'][role]
                       for role in nodes[node]['network_roles']]
                if ip in ips:
                    nailgun_nodes = [n for n in self.nodes
                                     if nodes[node]['name'] == n['hostname']
                                     and n['online']]
                    if len(nailgun_nodes) == 1:
                        amqp_hosts_name[nodes[node]['name']] = [ip, port]
        return amqp_hosts_name

    @property
    def userid(self):
        if version.StrictVersion(self.release_version)\
                < version.StrictVersion('7.0'):
            self._userid = 'nova'
            return self._userid

        if self._userid is None:
            self._userid = self.get_hiera_values(
                hiera_hash='rabbit_hash',
                hash_key='user'
            )
        return self._userid

    def get_ssh_connection_to_controller(self, controller):
        remote = ssh.Client(host=controller,
                            username=self._usr,
                            password=self._pwd,
                            key_filename=self._key,
                            timeout=self._ssh_timeout)
        return remote

    def list_nodes(self):
        if not self.amqp_hosts_name:
            self.fail('There are no online rabbit nodes')
        remote = \
            self.get_ssh_connection_to_controller(
                self.amqp_hosts_name.keys()[0])
        output = remote.exec_command("sudo rabbitmqctl cluster_status")
        substring_ind = output.find('{running_nodes')
        sub_end_ind = output.find('cluster_name')
        result_str = output[substring_ind: sub_end_ind]
        num_node = result_str.count("rabbit@")
        return num_node

    def pick_rabbit_master(self):
        if not self.amqp_hosts_name:
            self.fail('There are no online rabbit nodes')
        remote = \
            self.get_ssh_connection_to_controller(
                self.amqp_hosts_name.keys()[0])
        LOG.info('ssh session  to node {0} was open'.format(
            self.amqp_hosts_name.keys()[0]))
        LOG.info('Try to execute command <crm resource '
                 'status master_p_rabbitmq-server>')
        output = remote.exec_command(
            "sudo crm resource status master_p_rabbitmq-server")
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
        if not self.amqp_hosts_name:
            self.fail('There are no online rabbit nodes')
        remote = \
            self.get_ssh_connection_to_controller(
                self.amqp_hosts_name.keys()[0])
        output = remote.exec_command("sudo rabbitmqctl list_channels")

        LOG.debug('Result of executing command rabbitmqctl'
                  ' list_channels is {0}'.format(output))
        return output

    def get_hiera_values(self, hiera_hash="rabbit_hash",
                         hash_key=None,
                         conf_path="/etc/hiera.yaml",
                         json_parse=False):

        if hash_key is not None:
            lookup_cmd = ('value = hiera.lookup("{0}", {{}}, '
                          '{{}}, nil, :hash)["{1}"]').format(hiera_hash,
                                                             hash_key)
        else:
            lookup_cmd = ('value = hiera.lookup("{0}", {{}},'
                          ' {{}}, nil, :hash)').format(hiera_hash)
        if json_parse:
            print_cmd = 'require "json"; puts JSON.dump(value)'
        else:
            print_cmd = 'puts value'

        cmd = ('sudo ruby -e \'require "hiera"; '
               'hiera = Hiera.new(:config => "{0}"); '
               '{1}; {2};\'').format(conf_path, lookup_cmd, print_cmd)

        LOG.debug("Try to execute cmd {0}".format(cmd))
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        try:
            res = remote.exec_command(cmd)
            LOG.debug("result is {0}".format(res))
            if json_parse:
                return json.loads(res.strip())
            return res.strip()
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("Fail to get data from Hiera DB!")

    def get_conf_values(self, variable="rabbit_password",
                        sections="DEFAULT",
                        conf_path="/etc/nova/nova.conf"):
        cmd = ("sudo python -c 'import ConfigParser; "
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

    def get_amqp_hosts(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        cmd = 'sudo hiera amqp_hosts'
        LOG.debug("Try to execute cmd '{0}' on controller...".format(cmd))
        result = remote.exec_command(cmd)
        LOG.debug("Result: {0}".format(result))
        hosts = result.strip().split(',')
        return [host.lstrip().split(':')[0:2] for host in hosts]

    def check_rabbit_connections(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        for key in self.amqp_hosts_name.keys():
            ip, port = self.amqp_hosts_name[key]
            cmd = ("sudo python -c 'import kombu;"
                   " c = kombu.Connection(\"amqp://{1}:{2}@{0}:{3}//\");"
                   " c.connect()'".format(ip, self.userid,
                                          self.password, port))
            try:
                LOG.debug('Checking AMQP host "{0}"...'.format(ip))
                remote.exec_command(cmd)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("Failed to establish AMQP connection to {1}/tcp "
                          "port on {0} from controller node!".format(ip, port))

    def create_queue(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        for key in self.amqp_hosts_name.keys():
            ip, port = self.amqp_hosts_name[key]
            test_queue = 'test-rabbit-{0}-{1}'.format(
                data_utils.rand_name() + data_utils.generate_uuid(),
                ip
            )
            cmd = ("sudo python -c 'import kombu;"
                   " c = kombu.Connection(\"amqp://{1}:{2}@{0}:{3}//\");"
                   " c.connect(); ch = c.channel(); q = kombu.Qu"
                   "eue(\"{4}\", channel=ch, durable=False, queue_arguments={{"
                   "\"x-expires\": 15 * 60 * 1000}}); q.declare()'".format(
                       ip, self.userid, self.password, port, test_queue))
            try:
                LOG.debug("Declaring queue {0} on host {1}".format(
                    test_queue, ip))
                self.queues.append(test_queue)
                remote.exec_command(cmd)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("Failed to declare queue on host {0}".format(ip))

    def publish_message(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        for key in self.amqp_hosts_name.keys():
            ip, port = self.amqp_hosts_name[key]
            queues = [q for q in self.queues if ip in q]
            if not len(queues) > 0:
                self.fail("Can't publish message, queue created on host '{0}' "
                          "doesn't exist!".format(ip))
            test_queue = queues[0]
            id = data_utils.generate_uuid()
            cmd = ("sudo python -c 'import kombu;"
                   " c = kombu.Connection(\"amqp://{1}:{2}@{0}:{3}//\");"
                   " c.connect(); ch = c.channel(); producer = "
                   "kombu.Producer(channel=ch, routing_key=\"{4}\"); "
                   "producer.publish(\"{5}\")'".format(
                       ip, self.userid, self.password, port, test_queue, id))
            try:
                LOG.debug('Try to publish message {0}'.format(id))
                remote.exec_command(cmd)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail("Failed to publish message!")
            self.messages.append({'queue': test_queue, 'id': id})

    def check_queue_message_replication(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        for key in self.amqp_hosts_name.keys():
            ip, port = self.amqp_hosts_name[key]
            for message in self.messages:
                if ip in message['queue']:
                    continue
                cmd = ("sudo python -c 'import kombu;"
                       " c = kombu.Connection(\"amqp://{1}:{2}@{0}:{3}//\");"
                       " c.connect(); "
                       "ch = c.channel(); q = kombu.Queue(\"{4}\", channel=ch)"
                       "; msg = q.get(True); retval = 0 if msg.body in \"{5}\""
                       " else 1; exit(retval)'".format(
                           ip, self.userid, self.password, port,
                           message['queue'], message['id']))
                try:
                    LOG.debug('Checking that message with ID "{0}" was '
                              'replicated over the cluster...'.format(id))
                    remote.exec_command(cmd)
                except Exception:
                    LOG.debug(traceback.format_exc())
                    self.fail('Failed to check message replication!')
                self.messages.remove(message)
                break

    def delete_queue(self):
        if not self._controllers:
            self.fail('There are no online controllers')
        remote = self.get_ssh_connection_to_controller(self._controllers[0])
        LOG.debug('Try to deleting queues {0}... '.format(self.queues))
        if not self.queues:
            return
        host_key = self.amqp_hosts_name.keys()[0]
        ip, port = self.amqp_hosts_name[host_key]
        for test_queue in self.queues:
            cmd = ("sudo python -c 'import kombu;"
                   " c = kombu.Connection(\"amqp://{1}:{2}@{0}:{3}//\");"
                   " c.connect(); ch = c.channel(); q = kombu.Qu"
                   "eue(\"{4}\", channel=ch); q.delete();'".format(
                       ip, self.userid, self.password, port, test_queue))
            try:
                LOG.debug("Removing queue {0} on host {1}".format(
                    test_queue, ip))
                remote.exec_command(cmd)
                self.queues.remove(test_queue)
            except Exception:
                LOG.debug(traceback.format_exc())
                self.fail('Failed to delete queue "{0}"!'.format(test_queue))


class TestPacemakerBase(BaseTestCase):
    """TestPacemakerStatus class base methods."""

    @classmethod
    def setUpClass(cls):
        super(TestPacemakerBase, cls).setUpClass()
        cls.config = fuel_health.config.FuelConfig()
        cls.controller_names = cls.config.compute.controller_names
        cls.online_controller_names = (
            cls.config.compute.online_controller_names)
        cls.offline_controller_names = list(
            set(cls.controller_names) - set(cls.online_controller_names))

        cls.online_controller_ips = cls.config.compute.online_controllers
        cls.controller_key = cls.config.compute.path_to_private_key
        cls.controller_user = cls.config.compute.controller_node_ssh_user
        cls.controllers_pwd = cls.config.compute.controller_node_ssh_password
        cls.timeout = cls.config.compute.ssh_timeout

    def setUp(self):
        super(TestPacemakerBase, self).setUp()
        if 'ha' not in self.config.mode:
            self.skipTest('Cluster is not HA mode, skipping tests')
        if not self.online_controller_names:
            self.skipTest('There are no controller nodes')

    def _run_ssh_cmd(self, host, cmd):
        """Open SSH session with host and execute command."""
        try:
            sshclient = ssh.Client(host, self.controller_user,
                                   self.controllers_pwd,
                                   key_filename=self.controller_key,
                                   timeout=self.timeout)
            return sshclient.exec_longrun_command(cmd)
        except Exception:
            LOG.debug(traceback.format_exc())
            self.fail("%s command failed." % cmd)

    def _register_resource(self, res, res_name, resources):
        if res_name not in resources:
            resources[res_name] = {
                'master': [],
                'nodes': [],
                'started': 0,
                'stopped': 0,
                'active': False,
                'managed': False,
                'failed': False,
            }

        if 'true' in res.get('active'):
            resources[res_name]['active'] = True

        if 'true' in res.get('managed'):
            resources[res_name]['managed'] = True

        if 'true' in res.get('failed'):
            resources[res_name]['failed'] = True

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
                    'active': bool,             # Is resource active?
                    'managed': bool,            # Is resource managed?
                    'failed': bool,             # Has resource failed?
                  },
                  ...
                }
        """
        root = etree.fromstring(pcs_status)
        resources = {}

        for res_group in root.iter('resources'):
            for res in res_group:
                res_name = res.get('id')
                if 'resource' in res.tag:
                    self._register_resource(res, res_name, resources)
                elif 'clone' in res.tag:
                    for r in res:
                        self._register_resource(r, res_name, resources)
                elif 'group' in res.tag:
                    for r in res:
                        res_name_ingroup = r.get('id')
                        self._register_resource(r, res_name_ingroup, resources)
                        self._register_resource(r, res_name, resources)

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

    def get_pcs_constraints(self, constraints_xml):
        """Parse pacemaker constraints

        :param constraints_xml: XML string contains pacemaker constraints
        :return dict:
            {string:                # Resource name,
                {'attrs': list,     # List of dicts for resource
                                    #     attributes on each node,
                 'enabled': list    # List of strings with node names where
                                    #     the resource allowed to start,
                 'with-rsc': string # Name of an another resource
                                    #     from which this resource depends on.
                }
            }

        """

        root = etree.fromstring(constraints_xml)
        constraints = {}
        # 1. Get all attributes from constraints for each resource
        for con_group in root.iter('constraints'):
            for con in con_group:
                if 'rsc_location' in con.tag or 'rsc_colocation' in con.tag:
                    if 'score' not in con.keys():
                        # TODO(ddmitriev): process resource dependences
                        # for 'rule' section
                        continue

                    rsc = con.get('rsc')
                    if rsc not in constraints:
                        constraints[rsc] = {'attrs': [con.attrib]}
                    else:
                        constraints[rsc]['attrs'].append(con.attrib)

        # 2. Make list of nodes for each resource where it is allowed to start.
        #    Remove from 'enabled' list all nodes with score '-INFINITY'
        for rsc in constraints:
            attrs = constraints[rsc]['attrs']
            enabled = []
            disabled = []
            for attr in attrs:
                if 'with-rsc' in attr:
                    constraints[rsc]['with-rsc'] = attr['with-rsc']
                elif 'node' in attr:
                    if attr['score'] == '-INFINITY':
                        disabled.append(attr['node'])
                    else:
                        enabled.append(attr['node'])
            constraints[rsc]['enabled'] = list(set(enabled) - set(disabled))

        return constraints

    def get_resource_nodes(self, rsc, constraints, cluster_resources,
                           orig_rsc):
        if rsc in orig_rsc:
            # Constraints loop detected!
            msg = ('There is a dependency loop in constraints configuration: '
                   'resource "{0}" depends on the resource "{1}". Please check'
                   ' the pacemaker configuration!'
                   .format(orig_rsc[-1], rsc))
            raise fuel_health.exceptions.InvalidConfiguration(msg)
        else:
            orig_rsc.append(rsc)

        # Nodes where the resource is allowed to start
        allowed = constraints[rsc]['enabled']
        # Nodes where the parent resource is actually started
        if rsc in cluster_resources:
            started = cluster_resources[rsc]['nodes']
        else:
            started = []

        if 'with-rsc' in constraints[rsc]:
            # Recursively get nodes for the parent resource
            (parent_allowed,
             parent_started,
             parent_disallowed) = self.get_resource_nodes(
                 constraints[rsc]['with-rsc'],
                 constraints,
                 cluster_resources,
                 orig_rsc)
            if 'score' in constraints[rsc]:
                if constraints[rsc]['score'] == '-INFINITY':
                    # If resource banned to start on the same nodes where
                    # parent resource is started, then nodes where parent
                    # resource is started should be removed from 'allowed'
                    allowed = (set(allowed) - set(parent_started))
                else:
                    # Reduce 'allowed' list to only those nodes where
                    # the parent resource is allowed and running
                    allowed = list(set(parent_started) &
                                   set(parent_allowed) &
                                   set(allowed))
        # List of nodes, where resource is started, but not allowed to start
        disallowed = list(set(started) - set(allowed))

        return allowed, started, disallowed
