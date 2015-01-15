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

"""
Main purpose of following attribute is
to supply general information about test set.
This information will be stored in ostf database
in test_sets table.
"""
__profile__ = {
    "test_runs_ordering_priority": 1,
    "id": "sanity",
    "driver": "nose",
    "test_path": "fuel_health/tests/sanity",
    "cleanup_path": "fuel_health.cleanup",
    "description": "Sanity tests. Duration 30 sec - 2 min",
    "exclusive_testsets": []
}
