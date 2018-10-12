#!/bin/bash

# Deactivate testing virtualenv and reactivate original one
deactivate
echo "Reactivating virtualenv:"
echo $ORIG_ENV
source $ORIG_ENV
