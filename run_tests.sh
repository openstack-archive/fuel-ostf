#!/bin/bash

#    Copyright 2015 Mirantis, Inc.
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

function usage {
  echo "Usage: $0 [OPTION]..."
  echo ""
  echo " -p, --pep8    Just run pep8"
  echo " -P, --no-pep8 Do not run pep8"
  echo " -h, --help    Print this usage message"
  echo ""
  exit
}


function process_option {
  case "$1" in
    -h|--help) usage;;
    -p|--pep8) just_pep8=1;;
    -P|--no-pep8) no_just_pep8=1;;
  esac
}


just_pep8=0
no_just_pep8=0


function run_tests {
  # This variable collects all failed tests. It'll be printed in
  # the end of this function as a small statistic for user.
  local errors=""


  # Enable all tests if none was specified skipping all explicitly disabled tests.
  if [[ $just_pep8 -eq 0 ]]; then
    if [ $no_just_pep8 -ne 1 ];  then just_pep8=1;  fi
  fi

  # Run all enabled tests
  if [ $just_pep8 -eq 1 ]; then
    run_pep8 || errors+=" pep8_checks"
  fi

  # print failed tests
  if [ -n "$errors" ]; then
    echo Failed tests: $errors
    exit 1
  fi

  exit
}


function run_pep8 {
  echo "Running pep8 ..."
  tox -epep8 -v
}


for arg in "$@"; do
    process_option $arg
done

run_tests
