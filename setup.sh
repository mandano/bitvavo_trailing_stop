#! /bin/bash

sudo apt-get install python3-venv pip3

python3 -m venv bitvavo_trailing_stop

source bitvavo_trailing_stop/bin/activate

pip3 install Faker pytest simplejson python-dotenv python-bitvavo-api

deactivate