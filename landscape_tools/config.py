#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import sys
import os

## third party modules
import ruamel.yaml

class Config:

    project = ''
    landscapeMemberCategory = 'Members'
    landscapeMemberClasses = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
    ]
    landscapefile = 'landscape.yml'
    missingcsvfile = 'missing.csv'
    hostedLogosDir = 'hosted_logos'
    memberSuffix = None

    def __init__(self, config_file = ''):
        if config_file != '' and os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as stream:
                    data_loaded = ruamel.yaml.YAML(typ='safe', pure=True).load(stream)
            except:
                sys.exit(config_file+" config file is not defined")

            if 'project' in data_loaded:
                self.project = data_loaded['project']
            else:
                sys.exit("'project' not defined in config file")
            if 'landscapeMemberCategory' in data_loaded:
                self.landscapeMemberCategory = data_loaded['landscapeMemberCategory']
            if 'landscapeMemberClasses' in data_loaded:
                self.landscapeMemberClasses = data_loaded['landscapeMemberClasses']
            if 'landscapefile' in data_loaded:
                self.landscapefile = data_loaded['landscapefile']
            if 'missingcsvfile' in data_loaded:
                self.missingcsvfile = data_loaded['missingcsvfile']
            if 'memberSuffix' in data_loaded:
                self.memberSuffix = data_loaded['memberSuffix']
            if 'hostedLogosDir' in data_loaded:
                self.hostedLogosDir = data_loaded['hostedLogosDir']
