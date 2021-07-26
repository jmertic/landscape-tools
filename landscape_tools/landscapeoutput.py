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
from pathlib import Path

## third party modules
import ruamel.yaml
import requests

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

    def writeMissing(self, name, logo, homepage_url, crunchbase):
        if self._missingcsvfilewriter is None:
            self._missingcsvfilewriter = csv.writer(open(self.missingcsvfile, mode='w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self._missingcsvfilewriter.writerow(['name','logo','homepage_url','crunchbase'])

        self.membersErrors = self.membersErrors + 1
        self._missingcsvfilewriter.writerow([name, logo, homepage_url, crunchbase])

    def hostLogo(self,logo,orgname):
        if 'https://' not in logo and 'http://' not in logo:
            return logo

        print("...Hosting logo for "+orgname)
        filename = str(orgname).strip().replace(' ', '_')
        filename = filename.replace('.', '')
        filename = filename.replace(',', '')
        filename = re.sub(r'(?u)[^-\w.]', '', filename)
        filename = filename.lower()
        filenamepath = os.path.normpath(self.hostedLogosDir+"/"+unicodedata.normalize('NFKD',filename).encode('ascii', 'ignore').decode('ascii')+".svg") 

        r = requests.get(logo, allow_redirects=True)
        with open(filenamepath, 'wb') as fp:
            fp.write(r.content)

        return unicodedata.normalize('NFKD',filename).encode('ascii', 'ignore').decode('ascii')+".svg"

    def _removeNulls(self,yamlout):
        return re.sub('/(- \w+:) null/g', '$1', yamlout)

    def updateLandscape(self):
        # now write it back
        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                x['subcategories'] = self.landscapeMembers

        landscapefileoutput = Path(self.landscapefile)
        ryaml = ruamel.yaml.YAML()
        ryaml.indent(mapping=2, sequence=4, offset=2)
        ryaml.default_flow_style = False
        ryaml.allow_unicode = True
        ryaml.width = 160
        ryaml.Dumper = ruamel.yaml.RoundTripDumper
        ryaml.dump(self.landscape,landscapefileoutput, transform=self._removeNulls)

        print("Successfully added "+str(self.membersAdded)+" members and skipped "+str(self.membersErrors)+" members")

