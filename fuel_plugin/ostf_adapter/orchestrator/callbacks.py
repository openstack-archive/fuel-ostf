#    Copyright 2014 Mirantis, Inc.
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

from fuel_plugin.ostf_adapter.nose_plugin.nose_adapter import start_testrun


LOG = logging.getLogger(__name__)


def start_testruns_callback(body, message):
    LOG.info('Entering start_testrun_callback')
    to_be_acknowledged = False

    try:
        to_be_acknowledged = start_testrun(**body)
    except Exception as e:
        LOG.error('Exception while starting testrun. Details: {0}'
                  .format(e.message))
        to_be_acknowledged = True
    finally:
        if to_be_acknowledged:
            LOG.info('Acknowledging message in start_testrun_callback')
            message.ack()


def kill_testruns_callback(body, message):
    pass
