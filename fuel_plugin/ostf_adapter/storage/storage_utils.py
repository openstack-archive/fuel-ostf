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


from fuel_plugin.ostf_adapter.storage import models


def update_all_running_test_runs(session):
    session.query(models.TestRun). \
        filter_by(status='running'). \
        update({'status': 'finished'}, synchronize_session=False)
    session.query(models.Test). \
        filter(models.Test.status.in_(('running', 'wait_running'))). \
        update({'status': 'stopped'}, synchronize_session=False)
