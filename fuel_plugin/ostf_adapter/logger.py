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

import os
import logging
import logging.handlers


_LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ResultsLogger(object):
    """Logger used to log results of OSTF tests. Resutls are stored in
    /var/log/ostf/ dir. Each cluster has one log file per each set of tests.
    """

    def __init__(self, testset, cluster_id):
        self.testset = testset
        self.cluster_id = cluster_id
        self.filename = self._make_filename()
        self._logger = self._init_file_logger()

    def _init_file_logger(self):
        logger = logging.getLogger('ostf-results-log-{0}-{1}'.format(
            self.cluster_id, self.testset))

        if not logger.handlers:
            log_dir = '/var/log/ostf'
            log_file = os.path.join(log_dir, self.filename)

            file_handler = logging.handlers.WatchedFileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                '%(asctime)s %(message)s',
                _LOG_TIME_FORMAT)
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

        logger.propagate = 0

        return logger

    def _make_filename(self):
        return 'cluster_{cluster_id}_{testset}.log'.format(
            testset=self.testset, cluster_id=self.cluster_id)

    def log_results(self, test_id, test_name, status, message, traceback):
        status = status.upper()
        msg = "{status} {test_name} ({test_id}) {message} {traceback}".format(
            test_name=test_name, test_id=test_id, status=status,
            message=message, traceback=traceback)
        self._logger.info(msg)


def setup(log_file=None):
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s (%(module)s) %(message)s',
        _LOG_TIME_FORMAT)
    log = logging.getLogger(None)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    if log_file:
        log_file = os.path.abspath(log_file)
        file_handler = logging.handlers.WatchedFileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        mode = int('0644', 8)
        os.chmod(log_file, mode)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

    log.setLevel(logging.INFO)
