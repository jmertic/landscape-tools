#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import csv
import re
import os
import unicodedata
import tempfile
from pathlib import Path
from slugify import slugify

## third party modules
import ruamel.yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cairo

class LandscapeOutput:

    landscapefile = 'landscape.yml'
    landscape = None
    landscapeMembers = []
    missingcsvfile = 'missing.csv'
    _missingcsvfilewriter = None
    hostedLogosDir = 'hosted_logos'

    landscapeMemberCategory = 'LF Member Company'
    landscapeMemberClasses = [
        {"name": "Platinum Membership", "category": "Platinum"},
        {"name": "Gold Membership", "category": "Gold"},
        {"name": "Silver Membership", "category": "Silver"},
        {"name": "Silver Membership - MPSF", "category": "Silver"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    membersAdded = 0
    membersUpdated = 0
    membersErrors = 0

    landscapeProjectTaxonmony = [
        {"name": "Projects", "subcategories": [
            {"name": "All"}
        ]}
    ]
    landscapeProjectsReplace = True

    def __init__(self, loadLandscape = False):
        if loadLandscape:
            self.loadLandscape()

    def newLandscape(self):
        self.landscape = {
            'landscape': [{
                'category': None,
                'name': self.landscapeMemberCategory,
                'subcategories': []
            }]
        }
        for landscapeMemberClass in self.landscapeMemberClasses:
            memberClass = {
                "subcategory": None,
                "name": landscapeMemberClass['category'],
                "items" : []
            }
            if memberClass not in self.landscapeMembers:
                self.landscapeMembers.append(memberClass)

        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                x['subcategories'] = self.landscapeMembers

    def loadLandscape(self, reset=False):
        with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as fileobject: 
            self.landscape = ruamel.yaml.YAML().load(fileobject)
            if not self.landscape or not self.landscape['landscape']:
                self.newLandscape()
            else:
                if reset:
                    for landscapeMemberClass in self.landscapeMemberClasses:
                        memberClass = {
                            "subcategory": None,
                            "name": landscapeMemberClass['category'],
                            "items" : []
                        }
                        if memberClass not in self.landscapeMembers:
                            self.landscapeMembers.append(memberClass)

                    for x in self.landscape['landscape']:
                        if x['name'] == self.landscapeMemberCategory:
                            x['subcategories'] = self.landscapeMembers
                else:
                    for x in self.landscape['landscape']:
                        if x['name'] == self.landscapeMemberCategory:
                            self.landscapeMembers = x['subcategories']

    def writeMissing(self, name, homepage_url):
        if self._missingcsvfilewriter is None:
            self._missingcsvfilewriter = csv.writer(open(self.missingcsvfile, mode='w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self._missingcsvfilewriter.writerow(['name','homepage_url'])

        self.membersErrors = self.membersErrors + 1
        self._missingcsvfilewriter.writerow([name, homepage_url])

    def _removeNulls(self,yamlout):
        dump = re.sub(r'/(- \w+:) null/g', '$1', yamlout)
        
        return dump

    def _str_presenter(self, dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    def updateLandscape(self):
        # now write it back
        found = False
        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                x['subcategories'] = self.landscapeMembers
                found = True
                continue

        if not found:
            print("Couldn't find the membership category in landscape.yml to update - please check your config.yaml settings")

        landscapefileoutput = Path(self.landscapefile)
        ryaml = ruamel.yaml.YAML(typ='rt')
        ryaml.Representer.add_representer(str,self._str_presenter)
        ryaml.indent(mapping=2, sequence=4, offset=2)
        ryaml.default_flow_style = False
        ryaml.allow_unicode = True
        ryaml.width = 160
        ryaml.preserve_quotes = False
        ryaml.dump(self.landscape,landscapefileoutput, transform=self._removeNulls)

        print("Successfully added "+str(self.membersAdded)+" members and skipped "+str(self.membersErrors)+" members")

