#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
  brew install pyenv
  pyenv install -s $PYENV_VERSION
fi
