#!/bin/bash

if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  source venv/bin/activate
fi
pytest ./tests
