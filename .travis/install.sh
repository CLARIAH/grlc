#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
  pyenv global $PYENV_VERSION
  if [[ $PYENV_VERSION == 2* ]]; then
    alias pip=pip2
  fi
  if [[ $PYENV_VERSION == 3* ]]; then
    alias pip=pip3
  fi
  export PATH="/Users/travis/.pyenv/shims:${PATH}"
elif [[ $TRAVIS_OS_NAME == 'windows' ]]; then
  alias pip="pip --user"
fi

if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  virtualenv venv -p python$PYENV_VERSION
  source venv/bin/activate
fi

pip install --upgrade pip

# Horrible hack -- but we should remove pythonql functionality soon anyway...
pip install pythonql3
pip install .
pip install -r requirements-test.txt
