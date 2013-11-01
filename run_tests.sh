#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo ""
  echo " -p, --pep8 Just run pep8"
  echo " -h, --help Print this usage message"
  echo ""
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -p|--pep8) just_pep8=1;;
  esac
}

just_pep8=0

for arg in "$@"; do
    process_option $arg
done

function run_pep8 {
  echo "Running pep8 ..."
  # Opt-out files from pep8
  ignore_scripts="*.pyc,*.pyo,*.sh,*.swp,*.rst"
  ignore_files="*eventlet-patch:*pip-requires"
  ignore_dirs=".venv,.tox,dist,doc,vendor,*egg"
  GLOBIGNORE="$ignore_scripts:$ignore_files:$ignore_dirs"
  ignore="$ignore_scripts,$ignore_dirs"
  srcfiles="."
  ${wrapper} pep8 --repeat $FLAGS --show-source \
      --exclude=${ignore} ${srcfiles} | tee pep8.txt
}

if [ $just_pep8 -eq 1 ]; then
run_pep8
    exit
fi

