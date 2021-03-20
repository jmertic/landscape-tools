#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

# built in modules
import csv
import sys
import re
import os
import os.path
import json
import unicodedata
from os.path import normpath, basename
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from urllib.parse import urlparse
import urllib.request

# third party modules
from yaml.representer import SafeRepresenter
import ruamel.yaml
from ruamel.yaml import YAML
import requests
import validators
from bs4 import BeautifulSoup
from url_normalize import url_normalize
from tld import get_fld
from tld.utils import update_tld_names
from pycrunchbase import CrunchBase

class Config:

    project = 'tlf' # The Linux Foundation
    landscapefile = 'landscape.yml'
    missingcsvfile = 'missing.csv'

    def __init__(self, config_file):
        if config_file != '' and os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as stream:
                    data_loaded = ruamel.yaml.safe_load(stream)
            except:
                sys.exit(config_file+" config file is not defined")

            if 'project' in data_loaded:
                self.project = data_loaded['project']
            if 'landscapeMemberCategory' in data_loaded:
                self.landscapeMemberCategory = data_loaded['landscapeMemberCategory']
            if 'landscapeMemberClasses' in data_loaded:
                self.landscapeMemberClasses = data_loaded['landscapeMemberClasses']
            if 'landscapefile' in data_loaded:
                self.landscapefile = data_loaded['landscapefile']
            if 'missingcsvfile' in data_loaded:
                self.missingcsvfile = data_loaded['missingcsvfile']
            if 'landscapeName' in data_loaded:
                self.landscapeName = data_loaded['landscapeName']

#
# Member object to ensure we have normalization on fields. Only required fields are defined; others can be added dynamically.
#
class Member:

    orgname = None
    membership = None
    __website = None
    __logo = None
    __crunchbase = None
    __twitter = None

    # we'll use these to keep track of whether the member has valid fields
    _validWebsite = False
    _validLogo = False
    _validCrunchbase = False
    _validTwitter = False
    
    @property
    def crunchbase(self):
        return self.__crunchbase

    @crunchbase.setter
    def crunchbase(self, crunchbase):
        if crunchbase is None:
            self._validCrunchbase = False
            raise ValueError("Member.crunchbase must be not be blank for {orgname}".format(orgname=self.orgname))
        if not crunchbase.startswith('https://www.crunchbase.com/organization/'):
            # fix the URL if it's not formatted right
            o = urlparse(crunchbase)
            if (o.netloc == "crunchbase.com" or o.netloc == "www.crunchbase.com") and o.path.startswith("/organization"):
                crunchbase = "https://www.crunchbase.com{path}".format(path=o.path)
            else:
                self._validCrunchbase = False
                raise ValueError("Member.crunchbase for {orgname} must be set to a valid crunchbase url - '{crunchbase}' provided".format(crunchbase=crunchbase,orgname=self.orgname))

        self._validCrunchbase = True
        self.__crunchbase = crunchbase

    @property
    def website(self):
        return self.__website

    @website.setter
    def website(self, website):
        if website is None:
            self._validWebsite = False
            raise ValueError("Member.website must be not be blank for {orgname}".format(orgname=self.orgname))

        normalizedwebsite = url_normalize(get_fld(url_normalize(website), fail_silently=True), default_scheme='https')
        if not normalizedwebsite:
            self._validWebsite = False
            raise ValueError("Member.website for {orgname} must be set to a valid website - '{website}' provided".format(website=website,orgname=self.orgname))

        self._validWebsite = True
        self.__website = normalizedwebsite

    @property
    def logo(self):
        return self.__logo

    @logo.setter
    def logo(self, logo):
        if logo is None:
            self._validLogo = False
            raise ValueError("Member.logo must be not be blank for {orgname}".format(orgname=self.orgname))

        if not os.path.splitext(logo)[1] == '.svg':
            self._validLogo = False
            raise ValueError("Member.logo for {orgname} must be an svg file - '{logo}' provided".format(logo=logo,orgname=self.orgname))

        self._validLogo = True
        self.__logo = logo

    @property
    def twitter(self):
        return self.__twitter

    @twitter.setter
    def twitter(self, twitter):
        if not twitter:
            return
        if not twitter.startswith('https://twitter.com/'):
            # fix the URL if it's not formatted right
            o = urlparse(twitter)
            if o.netloc == '':
                twitter = "https://twitter.com/{}".format(twitter)
            if (o.netloc == "twitter.com" or o.netloc == "www.twitter.com"):
                twitter = "https://twitter.com{path}".format(path=o.path)
            else:
                self._validTwitter = False
                raise ValueError("Member.twitter for {orgname} must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=twitter,orgname=self.orgname))

        self._validTwitter = True
        self.__twitter = twitter


    def toLandscapeItemAttributes(self):
        allowedKeys = [
            'name',
            'homepage_url',
            'logo',
            'twitter',
            'repo_url',
            'crunchbase',
            'project_org',
            'additional_repos',
            'stock_ticker',
            'description',
            'branch',
            'project',
            'url_for_bestpractices',
            'enduser',
            'open_source',
            'allow_duplicate_repo',
            'unnamed_organization',
            'organization',
            'joined',
            'other_repo_url'
        ]
        returnentry = {'item': None}

        for i in allowedKeys:
            if i == 'name':
                returnentry['name'] = self.orgname
            elif i == 'homepage_url':
                returnentry['homepage_url'] = self.website
            elif i == 'twitter' and ( not self.twitter or self.twitter == ''):
                continue
            elif hasattr(self,i):
                returnentry[i] = getattr(self,i)

        return returnentry
        
    def isValidLandscapeItem(self):
        return self._validWebsite and self._validLogo and self._validCrunchbase and self.orgname != ''

    #
    # Overlay this Member data on another Member
    #
    def overlay(self, membertooverlay, onlykeys = []):

        memberitems = self.toLandscapeItemAttributes().items()

        for key, value in memberitems:
            if key in ['item','name']:
                continue
            if onlykeys and key not in onlykeys:
                continue
            # translate website and name to the Member object attribute name
            if key == "homepage_url":
                key = "website"
            if key == "name":
                key = "orgname"
            try:
                if (not hasattr(membertooverlay,key) or not getattr(membertooverlay,key)) or (key == 'crunchbase' and value != getattr(membertooverlay,key)):
                    print("...Overlay "+key)
                    print(".....Old Value - '{}'".format(getattr(membertooverlay,key) if hasattr(membertooverlay,key) else'empty'))
                    print(".....New Value - '{}'".format(value if value else 'empty'))
                    setattr(membertooverlay, key, value)
            except ValueError as e:
                print(e)
    

#
# Abstract Members class to normalize the methods used for the other ways of getting a member's info
#
class Members(ABC):

    def __init__(self, loadData = False):
        self.members = []
        if loadData:
            self.loadData()

    @abstractmethod
    def loadData(self):
        pass

    def find(self, org, website):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)
        found = []

        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website):
                found.append(member)

        return found

    def normalizeCompany(self, company):

        if company is None:
            return ''

        company = company.replace(', Inc.','')
        company = company.replace(', Ltd','')
        company = company.replace(',Ltd','')
        company = company.replace(' Inc.','')
        company = company.replace(' Co.','')
        company = company.replace(' Corp.','')
        company = company.replace(' AB','')
        company = company.replace(' AG','')
        company = company.replace(' BV','')
        company = company.replace(' Pty Ltd','')
        company = company.replace(' Pte Ltd','')
        company = company.replace(' Ltd','')
        company = company.replace(', LLC','')
        company = company.replace(' LLC','')
        company = company.replace(' LLP','')
        company = company.replace(' SPA','')
        company = company.replace(' GmbH','')
        company = company.replace(' PBC','')
        company = company.replace(' Limited','')
        company = company.replace(' s.r.o.','')
        company = company.replace(' srl','')
        company = company.replace(' s.r.l.','')
        company = company.replace(' a.s.','')
        company = company.replace(' S.A.','')
        company = company.replace('.','')
        company = company.replace(' (member)','')
        company = company.replace(' (supporter)','')
        company = re.sub(r'\(.*\)','',company)

        return company.strip()

    def normalizeURL(self, url):
        return url_normalize(url)

class SFDCMembers(Members):

    project = 'tlf' # The Linux Foundation

    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members' 

    def __init__(self, project = None, loadData = True):

        if project:
            self.project = project
        super().__init__(loadData)

    def loadData(self):
        print("--Loading SFDC Members data--")

        with urllib.request.urlopen(self.endpointURL.format(self.project)) as projectEndpointUrl:
            memberList = json.loads(projectEndpointUrl.read().decode())
            for record in memberList:
                if self.find(record['Name'],record['Website'],record['Membership']['Name']):
                    continue

                member = Member()
                try:
                    member.orgname = record['Name']
                except ValueError as e:
                    pass
                try:
                    member.website = record['Website']
                except ValueError as e:
                    pass
                try:
                    member.membership = record['Membership']['Name']
                except ValueError as e:
                    pass
                if 'Logo' in record:
                    try:
                        member.logo = record['Logo']
                    except ValueError as e:
                        pass
                if 'CrunchBaseURL' in record and record['CrunchBaseURL'] != '':
                    try:
                        member.crunchbase = record['CrunchBaseURL']
                    except ValueError as e:
                        pass
                if 'Twitter' in record and record['Twitter'] != '':
                    try:
                        member.twitter = record['Twitter']
                    except ValueError as e:
                        pass
                self.members.append(member)

    def find(self, org, website, membership):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website) and member.membership == membership:
                members.append(member)

        return members

class LandscapeMembers(Members):

    landscapeListYAML = 'https://raw.githubusercontent.com/cncf/landscapeapp/master/landscapes.yml'
    landscapeSettingsYAML = 'https://raw.githubusercontent.com/{repo}/master/settings.yml'
    landscapeLandscapeYAML = 'https://raw.githubusercontent.com/{repo}/master/landscape.yml'
    landscapeLogo = 'https://raw.githubusercontent.com/{repo}/master/hosted_logos/{logo}'
    skipLandscapes = ['openjsf']

    def __init__(self, landscapeListYAML = None, loadData = True):
        if landscapeListYAML:
            self.landscapeListYAML = landscapeListYAML
        super().__init__(loadData)

    def loadData(self):
        print("--Loading other landscape members data--")

        response = requests.get(self.landscapeListYAML)
        landscapeList = ruamel.yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)

        for landscape in landscapeList['landscapes']:
            if landscape['name'] in self.skipLandscapes:
                continue

            print("Loading "+landscape['name']+"...")

            # first figure out where memberships live
            response = requests.get(self.landscapeSettingsYAML.format(repo=landscape['repo']))
            settingsYaml = ruamel.yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)
            membershipKey = settingsYaml['global']['membership']

            # then load in members only
            response = requests.get(self.landscapeLandscapeYAML.format(repo=landscape['repo']))
            landscapeYaml = ruamel.yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)
            for category in landscapeYaml['landscape']:
                if membershipKey in category['name']:
                    for subcategory in category['subcategories']:
                        for item in subcategory['items']:
                            if not item.get('crunchbase'):
                                item['crunchbase'] = ''
                            member = Member()
                            for key, value in item.items():
                                try:
                                    if key != 'enduser':
                                        setattr(member, key, value)
                                except ValueError as e:
                                    pass
                            try:
                                member.membership = ''
                            except ValueError as e:
                                pass
                            try:
                                member.orgname = item['name']
                            except ValueError as e:
                                pass
                            try:
                                member.website = item['homepage_url']
                            except ValueError as e:
                                pass
                            try:
                                member.logo = self.normalizeLogo(item['logo'],landscape['repo'])
                            except ValueError as e:
                                pass
                            try:
                                member.crunchbase = item['crunchbase']
                            except ValueError as e:
                                pass
                            self.members.append(member)

    def normalizeLogo(self, logo, landscapeRepo):
        if logo is None or logo == '':
            return ""

        if 'https://' in logo or 'http://' in logo:
            return logo

        return self.landscapeLogo.format(repo=landscapeRepo,logo=logo)

class CrunchbaseAPIMembers(Members):

    crunchbaseKey = ''

    def loadData(self):
        return

    def find(self, org, website):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        if not self.crunchbaseKey and 'CRUNCHBASE_KEY' in os.environ:
            self.crunchbaseKey = os.getenv('CRUNCHBASE_KEY')
        cb = CrunchBase(self.crunchbaseKey)

        members = []
        for result in cb.organizations(org):
            company = cb.organization(result.permalink)
            if self.normalizeCompany(company.name) == normalizedorg:
                member = Member()
                try:
                    member.orgname = company.name
                except ValueError as e:
                    pass
                try:
                    member.website = self.normalizeURL(company.homepage_url)
                except ValueError as e:
                    pass
                try:
                    member.crunchbase = "https://www.crunchbase.com/organization/{org}".format(org=result.permalink)
                except ValueError as e:
                    pass

                members.append(member)

        return members

class CrunchbaseMembers(Members):

    bulkdatafile = 'organizations.csv'

    def __init__(self, bulkdatafile = None, loadData = False):
        if bulkdatafile:
            self.bulkdatafile = bulkdatafile
        super().__init__(loadData)

    def loadData(self):
        if os.path.isfile(self.bulkdatafile):
            print("--Loading Crunchbase bulk export data--")
            with open(self.bulkdatafile, newline='') as csvfile:
                memberreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                fields = next(memberreader)
                for row in memberreader:
                    member = Member()
                    try:
                        member.membership = ''
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.orgname = row[1]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.website = row[11]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.crunchbase = row[4]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo

                    self.members.append(member)

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
            self.landscape = ruamel.yaml.load(fileobject, Loader=ruamel.yaml.RoundTripLoader)
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
