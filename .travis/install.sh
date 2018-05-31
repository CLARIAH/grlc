#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
  pyenv init
  if [[ $PYENV_VERSION == 2* ]]; then
    alias pip=pip2
  fi
  if [[ $PYENV_VERSION == 3* ]]; then
    alias pip=pip3
  fi
fi

virtualenv venv
source venv/bin/activate
pip install .
pip install -r requirements-test.txt
