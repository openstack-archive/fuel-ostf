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

import logging

from stevedore import extension

from pecan import hooks
from fuel_plugin.ostf_adapter.storage import engine


LOG = logging.getLogger(__name__)


class ExceptionHandlingHook(hooks.PecanHook):
    def on_error(self, state, e):
        LOG.exception('Pecan state %s', state)


# class StorageHook(hooks.PecanHook):
#     def __init__(self):
#         super(StorageHook, self).__init__()
#         self.storage = storage.get_storage()
#
#     def before(self, state):
#         state.request.storage = self.storage


class PluginsHook(hooks.PecanHook):
    PLUGINS_NAMESPACE = 'plugins'

    def __init__(self):
        super(PluginsHook, self).__init__()
        self.plugin_manager = extension.ExtensionManager(
            self.PLUGINS_NAMESPACE, invoke_on_load=True)

    def before(self, state):
        state.request.plugin_manager = self.plugin_manager


class SessionHook(hooks.PecanHook):

    def before(self, state):
        state.request.session = engine.get_session()
