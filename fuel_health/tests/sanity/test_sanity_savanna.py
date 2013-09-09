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

import logging
from nose.plugins.attrib import attr

from fuel_health import nmanager
from savanna import base

LOG = logging.getLogger(__name__)


class ClusterTemplatesCrudTest(base.ITestCase):
    """
    TestClass contains tests that check basic Savanna functionality.
    """
    def setUp(self):
        super(ClusterTemplatesCrudTest, self).setUp()
        telnetlib.Telnet(self.host, self.port)
        self.create_node_group_templates()

    @attr(type=['sanity', 'fuel'])
    def test_cluster_templates(self):
        """Test checks cluster template creation with
        configuration | JT + NN | TT + DN |.
        Test checks that the list of instances is available.
        Target component: Savanna
        Scenario:
            1. Create template.
        Duration: 20 s.
        """
        fail_msg = 'Claster creating failed'
        node_list = {self.id_jt_nn: 1, self.id_tt_dn: 2}
        cl_tmpl_body = self.make_cluster_template('cl-tmpl-1', node_list)
        self.crud_object(cl_tmpl_body, self.url_cl_tmpl)


