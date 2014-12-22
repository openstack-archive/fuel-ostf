#!/bin/bash

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

set -eu

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run fuel-ostf test suite(s)"
  echo ""
  echo "  -p, --flake8          Run FLAKE8 checks"
  echo "  -P, --no-flake8       Don't run FLAKE8 checks"
  echo "  -u, --unit            Run unit tests"
  echo "  -U, --no-unit         Don't run unit tests"
  echo "  -i, --integration     Run integarion tests"
  echo "  -I, --no-integration  Don't run inteagration tests"
  echo "  -t, --tests           Run a given test files"
  echo "  -h, --help            Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run all available"
  echo "      tests with all available checks."
  exit
}

function process_options {
  for arg in $@; do
    case "$arg" in
      -h|--help) usage;;
      -p|--flake8) flake8_checks=1;;
      -P|--no-flake8) no_flake8_checks=1;;
      -u|--unit) unit_tests=1;;
      -U|--no-unit) no_unit_tests=1;;
      -i|--integration) integration_tests=1;;
      -I|--no-integration) no_integration_tests=1;;
      -t|--tests) certain_tests=1;;
      -*) testropts="$testropts $arg";;
      *) testrargs="$testrargs $arg"
    esac
  done
}

# settings
ROOT=$(dirname `readlink -f $0`)

# test options
testrargs=
testropts="--with-timer --timer-warning=10 --timer-ok=2 --timer-top-n=10"

# customizable options
ARTIFACTS=${ARTIFACTS:-`pwd`/test_run}
INTEGRATION_XUNIT=${INTEGRATION_XUNIT:-"$ROOT/integration.xml"}
OSTF_SERVER_PORT=${OSRF_SERVER_PORT:-8777}
OSTF_SERVER_WAIT_TIME=${OSTF_SERVER_WAIT_TIME:-10}
UNIT_XUNIT=${UNIT_XUNIT:-"$ROOT/unittests.xml"}

mkdir -p $ARTIFACTS

# disabled/enabled flags that are setted from the cli.
# used for manipulating run logic.
flake8_checks=0
no_flake8_checks=0
unit_tests=0
no_unit_tests=0
integration_tests=0
no_integration_tests=0
certain_tests=0


function run_tests {
  run_cleanup

  # This variable collects all failed tests. It'll be printed in
  # the end of this function as a small statistic for user.
  local errors=""

  # If tests was specified in command line then run only these tests
  if [ $certain_tests -eq 1 ]; then
    for testfile in $testrargs; do
      local testfile=`readlink -f $testfile`
      guess_test_run $testfile
    done
    exit
  fi

  # Enable all tests if none was specified skipping all explicitly disabled tests.
  if [[ $flake8_checks -eq 0 && \
      $integration_tests -eq 0 && \
      $unit_tests -eq 0 ]]; then

    if [ $no_flake8_checks -ne 1 ];  then flake8_checks=1;  fi
    if [ $no_unit_tests -ne 1 ];  then unit_tests=1;  fi
    if [ $no_integration_tests -ne 1 ]; then integration_tests=1; fi
  fi

  # Run all enabled tests
  if [ $flake8_checks -eq 1 ]; then
    run_flake8 || errors+=" flake8_checks"
  fi

  if [ $unit_tests -eq 1 ]; then
    run_unit_tests || errors+=" unit_tests"
  fi

  if [ $integration_tests -eq 1 ]; then
    run_integration_tests || errors+=" integration_tests"
  fi

  # print failed tests
  if [ -n "$errors" ]; then
    echo Failed tests: $errors
    exit 1
  fi

  exit
}


function guess_test_run {
  if [[ $1 == *integration* ]]; then
    run_integration_tests $1 || echo "ERROR: $1"
  else
    run_unit_tests $1 || echo "ERROR: $1"
  fi
}


# Remove temporary files. No need to run manually, since it's
# called automatically in `run_tests` function.
function run_cleanup {
  find . -type f -name "*.pyc" -delete
  rm -f *.log
  rm -f *.pid
}


function run_flake8 {
  echo "Starting flake8 checks"
  local result=0
  tox -e pep8 || result=1

  return $result
}


function run_unit_tests {
  echo "Starting unit tests"

  local TESTS="$ROOT/fuel_plugin/testing/tests/unit"
  local options="-vv $testropts --xunit-file $UNIT_XUNIT"
  local result=0

  if [ $# -ne 0 ]; then
    TESTS=$@
  fi

  # run tests
  tox -epy26 -- $options $TESTS  || result=1

  return $result
}


function create_ostf_conf {
  local config_path=$1
  local artifacts_path=$2
  local SERVER_PORT=${3:-$OSTF_SERVER_PORT}
  cat > $config_path <<EOL
[adapter]
server_port = $SERVER_PORT
dbpath = postgresql+psycopg2://ostf:ostf@localhost/ostf
log_file = $artifacts_path/ostf.log
EOL
}


function run_server {
  local SERVER_STDOUT=$1
  local SERVER_SETTINGS=$2
  local SERVER_PORT=${3:-$OSTF_SERVER_PORT}

  local RUN_SERVER="\
      ostf-server \
      --debug
      --debug_tests=$ROOT/fuel_plugin/testing/fixture/dummy_tests
      --config-file $SERVER_SETTINGS"

  # kill old server instance if exists
  local pid=`lsof -ti tcp:$SERVER_PORT`
  if [ -n "$pid" ]; then
    kill $pid
    sleep 5
  fi

  # run new server instance
  tox -evenv -- $RUN_SERVER >> $SERVER_STDOUT 2>&1 &

  # wait for server availability
  which curl >> /dev/null

  if [ $? -eq 0 ]; then
    # we wait for 0.1s, so there are 10 attempts in 1s
    local num_retries=$[$OSTF_SERVER_WAIT_TIME * 10]

    for i in $(seq 1 $num_retries); do
      local http_code=`curl -s -w %{http_code} -o /dev/null http://127.0.0.1:$SERVER_PORT`
      if [ "$http_code" == "200" ]; then break; fi
      sleep 0.1
    done
  else
    sleep 5
  fi

  pid=`lsof -ti tcp:$SERVER_PORT`
  local server_launched=$?
  echo $pid
  return $server_launched
}


function syncdb {
  local SERVER_SETTINGS=$1
  local RUN_SYNCDB="\
      ostf-server \
      --debug
      --after-initialization-environment-hook
      --config-file $SERVER_SETTINGS"

      tox -evenv -- $RUN_SYNCDB > /dev/null
}

function run_integration_tests {
  echo "Starting integration tests"

  local TESTS="$ROOT/fuel_plugin/testing/tests/integration"
  local options="-vv $testropts --xunit-file $INTEGRATION_XUNIT"
  local result=0
  local artifacts=$ARTIFACTS/integration
  local config=$artifacts/ostf.conf
  mkdir -p $artifacts

  if [ $# -ne 0 ]; then
    TESTS=$@
  fi

  create_ostf_conf $config $artifacts

  syncdb $config

  # run tests
  tox -epy26 -- $options $TESTS  || result=1

  return $result
}


# parse command line arguments and run the tests
process_options $@
run_tests

