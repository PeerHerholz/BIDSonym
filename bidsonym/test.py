import os
from glob import glob
import pandas as pd
import json

dat_file = '/Users/peerherholz/Desktop/ommaba_exp_res/SessionID-cf3dfc5c-5ae3-493c-8d30-e335c094e90e.json'

with open(dat_file, 'r') as json_file:
    data = json.load(json_file)