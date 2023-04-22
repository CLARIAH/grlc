#!/bin/bash

# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

# Deactivate testing virtualenv and reactivate original one
if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  deactivate
  echo "Reactivating virtualenv:"
  echo $ORIG_ENV
  source $ORIG_ENV
fi
