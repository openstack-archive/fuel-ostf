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

import os
import yaml

from fuel_health.common import log as logging


LOG = logging.getLogger(__name__)


class Facts(object):
    __default_config_path = '/var/lib/puppet/yaml/facts/'

    def __init__(self, config=None):
        _config_path = config or self.__default_config_path
        self.config = self._read_config(_config_path)

    @property
    def amqp(self):
        _amqp = self._get_rabbit_data() or self._get_qpid_data()
        return _amqp

    @property
    def amqp_user(self):
        return 'nova'

    @property
    def amqp_password(self):
        return self.amqp['password']

    def _read_config(self, path):
        _file = None
        for filename in os.listdir(path):
            if filename.endswith('.yaml'):
                _file = filename
                break
        _file = open(os.path.join(path, _file))
        self._init_parser()
        data = yaml.load(_file)
        _file.close()
        return data

    def _get_rabbit_data(self):
        try:
            return self.config['values']['rabbit']
        except KeyError:
            return None

    def _get_qpid_data(self):
        try:
            return self.config['values']['qpid']
        except KeyError:
            return None

    def _init_parser(self):
        # Custom YAML constructs for ruby objects for puppet files parsing
        def _construct_ruby_object(loader, suffix, node):
                return loader.construct_yaml_map(node)

        def _construct_ruby_sym(loader, suffix, node):
            return loader.construct_yaml_str(node)

        yaml.add_multi_constructor(u"!ruby/object:", _construct_ruby_object)
        yaml.add_multi_constructor(u"!ruby/sym", _construct_ruby_sym)
