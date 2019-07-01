#!/bin/bash

# Deactivate testing virtualenv and reactivate original one
if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  deactivate
  echo "Reactivating virtualenv:"
  echo $ORIG_ENV
  source $ORIG_ENV
fi
