#!/bin/bash

# Store location of original virtualenv so we can reactivate it on deploy
if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  ORIG_ENV="$(dirname $(which python))/activate"
  echo "Original virtualenv"
  echo $ORIG_ENV
fi

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
  brew install pyenv
  pyenv install -s $PYENV_VERSION
elif [[ $TRAVIS_OS_NAME == 'windows' ]]; then
  choco install python
fi
