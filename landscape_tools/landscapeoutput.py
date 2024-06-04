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
import logging
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

from landscape_tools.config import Config

class LandscapeOutput:

    landscapefile = 'landscape.yml'
    landscape = None
    landscapeItems = []
    missingcsvfile = 'missing.csv'
    _missingcsvfilewriter = None
    hostedLogosDir = 'hosted_logos'

    landscapeCategory = 'LF Member Company'
    landscapeSubcategories = [
        {"name": "Platinum Membership", "category": "Platinum"},
        {"name": "Gold Membership", "category": "Gold"},
        {"name": "Silver Membership", "category": "Silver"},
        {"name": "Silver Membership - MPSF", "category": "Silver"},
        {"name": "Associate Membership", "category": "Associate"}
    ]
    _itemsAdded = 0
    _itemsUpdated = 0
    _itemsErrors = 0

    def __init__(self, config: type[Config] = None, resetCategory = False):
        self.processConfig(config)

        with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as fileobject: 
            self.landscape = ruamel.yaml.YAML().load(fileobject)
            found = False
            if self.landscape and self.landscape['landscape']:
                for x in self.landscape['landscape']:
                    if x['name'] == self.landscapeCategory:
                        self.landscapeItems = x['subcategories']
                        found = True
                        continue
            else:
                self.landscape = {
                    'landscape': [{
                        'category': None,
                        'name': self.landscapeCategory,
                        'subcategories': []
                    }]
                }
        
            if not found or resetCategory:
                self.landscapeItems = []
                for landscapeSubcategory in self.landscapeSubcategories:
                    subcategory = {
                        "subcategory": None,
                        "name": landscapeSubcategory['category'],
                        "items" : []
                    }
                    if subcategory not in self.landscapeItems:
                        self.landscapeItems.append(subcategory)
                 
                for x in self.landscape['landscape']:
                    if x['name'] == self.landscapeCategory:
                        x['subcategories'] = self.landscapeItems
    
    def processConfig(self, config: type[Config] = None):
        if config:
            self.landscapeCategory = config.landscapeCategory
            self.landscapeSubcategories = config.landscapeSubcategories
            self.landscapefile = config.landscapefile
            self.missingcsvfile = config.missingcsvfile
            self.hostedLogosDir = config.hostedLogosDir
            self.memberSuffix = config.memberSuffix

    def writeMissing(self, name, homepage_url):
        if self._missingcsvfilewriter is None:
            self._missingcsvfilewriter = csv.writer(open(self.missingcsvfile, mode='w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self._missingcsvfilewriter.writerow(['name','homepage_url'])

        self._itemsErrors += 1
        self._missingcsvfilewriter.writerow([name, homepage_url])

    def _removeNulls(self,yamlout):
        return re.sub(r'/(- \w+:) null/g', '$1', yamlout)

    def _str_presenter(self, dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    def processIntoLandscape(self,members):
        logger = logging.getLogger()
        for member in members:
            for landscapeItemSubcategory in self.landscapeItems:
                landscapeSubcategory = next((item for item in self.landscapeSubcategories if item["name"] == member.membership), None)
                if ( not landscapeSubcategory is None ) and ( landscapeSubcategory['name'] == member.membership ) and ( landscapeItemSubcategory['name'] == landscapeSubcategory['category'] ) :
                     
                    # Write out to missing.csv if it's missing key parameters
                    if not member.isValidLandscapeItem():
                        logger.warn("Not adding {} to Landscape - Missing key attributes".format(member.orgname))
                        self.writeMissing(
                            member.orgname,
                            member.website
                            )
                    # otherwise we can add it
                    else:
                        logger.info("Added '{}' to Landscape".format(member.orgname))
                        member.hostLogo(self.hostedLogosDir)
                        self._itemsAdded += 1
                        # host the logo
                        if self.memberSuffix:
                            member.entrysuffix = self.memberSuffix
                        landscapeItemSubcategory['items'].append(member.toLandscapeItemAttributes())
                    break

    @property
    def itemsAdded(self):
        return self._itemsAdded
    
    @property
    def itemsUpdated(self):
        return self._itemsUpdated
    
    @property
    def itemsErrors(self):
        return self._itemsErrors

    def updateLandscape(self):
        # now write it back
        found = False
        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeCategory:
                x['subcategories'] = self.landscapeItems
                found = True
                continue

        if not found:
            self.landscape['landscape'].append({
                'category': None,
                'name': self.landscapeCategory,
                'subcategories': self.landscapeItems
                })
 
        landscapefileoutput = Path(self.landscapefile)
        ryaml = ruamel.yaml.YAML(typ='rt')
        ryaml.Representer.add_representer(str,self._str_presenter)
        ryaml.indent(mapping=2, sequence=4, offset=2)
        ryaml.default_flow_style = False
        ryaml.allow_unicode = True
        ryaml.width = 160
        ryaml.preserve_quotes = False
        ryaml.dump(self.landscape,landscapefileoutput, transform=self._removeNulls)

