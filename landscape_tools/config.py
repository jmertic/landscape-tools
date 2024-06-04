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
    landscapeCategory = 'Members'
    landscapeSubcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
    ]
    landscapefile = 'landscape.yml'
    missingcsvfile = 'missing.csv'
    hostedLogosDir = 'hosted_logos'
    memberSuffix = None

    def __init__(self, config_file = ''):
        if config_file != '' and os.path.isfile(config_file):
            with open(config_file, 'r') as stream:
                data_loaded = ruamel.yaml.YAML(typ='safe', pure=True).load(stream)

                try:
                    self.project = data_loaded['project']
                except KeyError as e:
                    raise ValueError("'project' not defined in config file")
                
                self.landscapeCategory = data_loaded['landscapeCategory'] if 'landscapeCategory' in data_loaded else Config.landscapeCategory
                self.landscapeCategory = data_loaded['landscapeMemberCategory'] if 'landscapeMemberCategory' in data_loaded else Config.landscapeCategory
                self.landscapeSubcategories = data_loaded['landscapeSubcategories'] if 'landscapeSubcategories' in data_loaded else Config.landscapeSubcategories
                self.landscapeSubcategories = data_loaded['landscapeMemberClasses'] if 'landscapeMemberClasses' in data_loaded else Config.landscapeSubcategories
                self.landscapefile = data_loaded['landscapefile'] if 'landscapefile' in data_loaded else Config.landscapefile
                self.missingcsvfile = data_loaded['missingcsvfile'] if 'missingcsvfile' in data_loaded else Config.missingcsvfile
                self.hostedLogosDir = data_loaded['hostedLogosDir'] if 'hostedLogosDir' in data_loaded else Config.hostedLogosDir
                self.memberSuffix = data_loaded['memberSuffix'] if 'memberSuffix' in data_loaded else Config.memberSuffix
