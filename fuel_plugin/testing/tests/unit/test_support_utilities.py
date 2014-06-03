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

from fuel_plugin.ostf_adapter import mixins


class TestDeplTagsGetter(unittest.TestCase):

    def test_get_cluster_depl_tags(self):
        expected = {
            'cluster_id': 3,
            'depl_tags': set(
                ['ha', 'rhel', 'additional_components',
                 'murano', 'nova_network']
            )
        }

        res = mixins._get_cluster_depl_tags(expected['cluster_id'])

        self.assertEqual(res, expected['depl_tags'])
