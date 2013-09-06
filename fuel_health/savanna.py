# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
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
import requests
import logging

import contextlib
import shutil
import socket
import telnetlib
import time
import json
import os

from fuel_health.common.ssh import Client as SSHClient
from fuel_health.exceptions import SSHExecCommandFailed
from fuel_health import exceptions
import fuel_health.nmanager
import fuel_health.test
from fuel_health import config

import keystoneclient.v2_0.client

LOG = logging.getLogger(__name__)


#class SavannaClient(fuel_health.manager.Manager):
#    """
#    Manager that provides access to the official python clients for
#    calling various Savanna APIs.
#    """
#    def __init__(self):
