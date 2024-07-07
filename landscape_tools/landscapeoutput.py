#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import csv
import re
import logging
import os
from contextlib import suppress

## third party modules
import ruamel.yaml

from landscape_tools.config import Config
from landscape_tools.members import Members

class LandscapeOutput:

    landscapefile = 'landscape.yml'
    landscape = None
    landscapeItems = []
    missingcsvfile = 'missing.csv'
    _missingcsvfilewriter = None
    hostedLogosDir = 'hosted_logos'
    memberSuffix = ''

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

    def __init__(self, config: type[Config] = None, resetCategory = False, newLandscape = False, load = True):
        self.processConfig(config)
        if load:
            self.load(resetCategory=resetCategory,newLandscape=newLandscape)

    def load(self, resetCategory = False, newLandscape = False):
        if not newLandscape:
            with open(self.landscapefile, 'r', encoding="utf8", errors='ignore') as fileobject: 
                self.landscape = ruamel.yaml.YAML().load(fileobject)

        found = False
        if self.landscape and 'landscape' in self.landscape:
            for x in self.landscape['landscape']:
                if x['name'] == self.landscapeCategory:
                    self.landscapeItems = x['subcategories']
                    found = True
                    break
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
            self.landscapefile = os.path.join(config.basedir,config.landscapefile)
            self.missingcsvfile = config.missingcsvfile
            self.hostedLogosDir = os.path.join(config.basedir,config.hostedLogosDir)
            self.memberSuffix = config.memberSuffix if config.view == 'members' else self.memberSuffix

    @property
    def itemsAdded(self):
        return self._itemsAdded
    
    @property
    def itemsUpdated(self):
        return self._itemsUpdated
    
    @property
    def itemsErrors(self):
        return self._itemsErrors

    def writeMissing(self, name, homepage_url):
        if self._missingcsvfilewriter is None:
            self._missingcsvfilewriter = csv.writer(open(self.missingcsvfile, mode='w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self._missingcsvfilewriter.writerow(['name','homepage_url'])

        self._itemsErrors += 1
        self._missingcsvfilewriter.writerow([name, homepage_url])

    def syncItems(self, members: type[Members], addmissing = True):
        logger = logging.getLogger()
        logger.info("Syncing '{}' items".format(self.landscapeCategory))
        foundSlugs = []
        for landscapeItemSubcategory in self.landscapeItems:
            for landscapeItem in landscapeItemSubcategory['items']:
                foundmembers = []
                if hasattr(members,'findBySlug'):
                    x = members.findBySlug(landscapeItem['extra']['slug']) if 'extra' in landscapeItem and 'slug' in landscapeItem['extra'] else None
                    if x:
                        foundmembers.append(x)
                if foundmembers == []:
                    foundmembers = members.find(landscapeItem['name'], landscapeItem['homepage_url'])
                for foundmember in foundmembers:
                    logger.info("Found '{}'".format(landscapeItem['name']))
                    foundSlugs.append(foundmember.extra['slug'])
                    self._itemsUpdated += 1
                    for key, value in foundmember.toLandscapeItemAttributes().items():
                        if key != 'item':
                            with suppress(ValueError):
                                if isinstance(value,dict):
                                    landscapeItem[key] = {} if key not in landscapeItem else landscapeItem[key]
                                    for subkey, subvalue in value.items():
                                        if subkey not in landscapeItem[key] or landscapeItem[key][subkey] != subvalue:
                                            logger.info("Setting '{}.{}' for '{}' from '{}' to '{}'".format(key,subkey,landscapeItem['name'],landscapeItem[key][subkey] if subkey in landscapeItem[key] else '',subvalue))
                                            landscapeItem[key][subkey] = subvalue
                                elif isinstance(value,list) and value != landscapeItem[key] if key in landscapeItem else None:
                                    logger.info("Setting '{}' for '{}' from '{}' to '{}'".format(key,landscapeItem['name'],landscapeItem[key] if key in landscapeItem else '',list(set(value + landscapeItem[key] if key in landscapeItem else []))))
                                    landscapeItem[key] = list(set(value + landscapeItem[key]))
                                elif value != None and value != landscapeItem[key] if key in landscapeItem else None: 
                                    logger.info("Setting '{}' for '{}' from '{}' to '{}'".format(key,landscapeItem['name'],landscapeItem[key] if key in landscapeItem else '',value))
                                    landscapeItem[key] = value
                                    if key == 'logo':
                                        foundmember.hostLogo(self.hostedLogosDir)

        if addmissing:
            self.addItems(members,skipSlugs=foundSlugs)

    def addItems(self, members: type[Members], skipSlugs = []):
        logger = logging.getLogger() 
        logger.info("Adding '{}' items".format(self.landscapeCategory))
        for member in members.members:
            if member.extra and 'slug' in member.extra and member.extra['slug'] in skipSlugs:
                continue
            logger.info("Found '{}'".format(member.orgname))
            foundCategory = False
            for landscapeItemSubcategory in self.landscapeItems:
                landscapeSubcategory = next((item for item in self.landscapeSubcategories if item["name"] == member.membership), None)
                if ( not landscapeSubcategory is None ) and ( landscapeSubcategory['name'] == member.membership ) and ( landscapeItemSubcategory['name'] == landscapeSubcategory['category'] ) :
                    foundCategory = True
                    # Write out to missing.csv if it's missing key parameters
                    if not member.isValidLandscapeItem():
                        logger.warning("Not adding '{}' to Landscape - Missing key attributes {}".format(member.orgname,",".join(member.invalidLandscapeItemAttributes())))
                        self.writeMissing(
                            member.orgname,
                            member.website
                            )
                    # otherwise we can add it
                    else:
                        logger.info("Added '{}' to Landscape in SubCategory '{}'".format(member.orgname,member.membership))
                        self._itemsAdded += 1
                        member.hostLogo(self.hostedLogosDir)
                        member.entrysuffix = self.memberSuffix if self.memberSuffix else member.entrysuffix
                        landscapeItemSubcategory['items'].append(member.toLandscapeItemAttributes())
                    break
            if not foundCategory:
                logger.warning("Not adding '{}' to Landscape - SubCategory '{}' not found".format(member.orgname,member.membership))
                self.writeMissing(
                    member.orgname,
                    member.website
                    )

    def save(self):
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

        with open(self.landscapefile, 'w+', encoding="utf8", errors='ignore') as fileobject: 
            ryaml = ruamel.yaml.YAML(typ='rt')
            ryaml.Representer.add_representer(str,self._str_presenter)
            ryaml.Representer.add_representer(type(None),self._none_representer)
            ryaml.indent(mapping=2, sequence=4, offset=2)
            ryaml.default_flow_style = False
            ryaml.allow_unicode = True
            ryaml.width = 180
            ryaml.preserve_quotes = False
            ryaml.dump(self.landscape, fileobject, transform=self._removeNulls)

    def _removeNulls(self,yamlout):
        return yamlout.replace('- item: null','- item:').replace('- category: null','- category:').replace('- subcategory: null','- subcategory:')

    def _str_presenter(self, dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)

    def _none_representer(self, dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:null', u'null')
