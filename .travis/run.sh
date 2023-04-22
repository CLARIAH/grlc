#!/bin/bash

# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

if [[ $TRAVIS_BUILD_STAGE_NAME == 'Deploy' ]]; then
  source venv/bin/activate
fi
pytest ./tests
