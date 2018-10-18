#!/bin/bash

# Store location of original virtualenv so we can reactivate it later
ORIG_ENV="$(dirname $(which python))/activate"
echo "Original virtualenv"
echo $ORIG_ENV

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
  brew install pyenv
  pyenv install -s $PYENV_VERSION
fi
