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

import unittest
import mock

from fuel_plugin.ostf_adapter.wsgi.wsgi_utils import _get_cluster_depl_tags


class TestDeplTagsGetter(unittest.TestCase):

    def test_get_cluster_depl_tags(self):
        expected = {
            'cluster_id': 3,
            'depl_tags': set(['ha', 'rhel', 'additional_components', 'murano'])
        }

        mocked_pecan_conf = mock.Mock()
        mocked_pecan_conf.nailgun.host = '127.0.0.1'
        mocked_pecan_conf.nailgun.port = 8888

        with mock.patch(
            'fuel_plugin.ostf_adapter.wsgi.wsgi_utils.conf',
            mocked_pecan_conf
        ):
            res = _get_cluster_depl_tags(expected['cluster_id'])

        self.assertEqual(res, expected['depl_tags'])
