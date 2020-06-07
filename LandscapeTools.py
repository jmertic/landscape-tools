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
from datetime import datetime

# third party modules
from yaml.representer import SafeRepresenter
import ruamel.yaml
from ruamel import yaml
import requests
import validators
from bs4 import BeautifulSoup
from url_normalize import url_normalize
from tld import get_fld
from tld.utils import update_tld_names
from simple_salesforce import Salesforce
from pycrunchbase import CrunchBase

class Config:

    sf_username = None
    sf_password = None
    sf_token = None
    project = 'The Linux Foundation'

    def __init__(self, config_file):
        if config_file != '' and os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as stream:
                    data_loaded = yaml.safe_load(stream)
            except:
                sys.exit(config_file+" config file is not defined")

            if 'sf_username' in data_loaded:
                self.sf_username = data_loaded['sf_username']
            if 'sf_password' in data_loaded:
                self.sf_password = data_loaded['sf_password']
            if 'sf_token' in data_loaded:
                self.sf_token = data_loaded['sf_token']
            elif 'SFDC_TOKEN' in os.environ:
                self.token = os.environ['SFDC_TOKEN']
            else:
                raise Exception('Salesforce security token is not defined. Set \'token\' in {config_file} or set SFDC_TOKEN environment variable to a valid Salesforce security token'.format(config_file=config_file))
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

    # we'll use these to keep track of whether the member has valid fields
    _validWebsite = False
    _validLogo = False
    _validCrunchbase = False

    @property
    def crunchbase(self):
        return self.__crunchbase

    @crunchbase.setter
    def crunchbase(self, crunchbase):
        if crunchbase is None:
            raise ValueError("Member.crunchbase must be not be blank for {orgname}".format(orgname=self.orgname))
        if not crunchbase.startswith('https://www.crunchbase.com/organization/'):
            raise ValueError("Member.crunchbase for {orgname} must be set to a valid crunchbase url - '{crunchbase}' provided".format(crunchbase=crunchbase,orgname=self.orgname))

        self._validCrunchbase = True
        self.__crunchbase = crunchbase

    @property
    def website(self):
        return self.__website

    @website.setter
    def website(self, website):
        if website is None:
            raise ValueError("Member.website must be not be blank for {orgname}".format(orgname=self.orgname))

        normalizedwebsite = url_normalize(get_fld(url_normalize(website), fail_silently=True), default_scheme='https')
        if not normalizedwebsite:
            raise ValueError("Member.website for {orgname} must be set to a valid website - '{website}' provided".format(website=website,orgname=self.orgname))

        self._validWebsite = True
        self.__website = normalizedwebsite

    @property
    def logo(self):
        return self.__logo

    @logo.setter
    def logo(self, logo):
        if logo is None:
            raise ValueError("Member.logo must be not be blank for {orgname}".format(orgname=self.orgname))

        if not os.path.splitext(logo)[1] == '.svg':
            raise ValueError("Member.logo for {orgname} must be an svg file - '{logo}' provided".format(logo=logo,orgname=self.orgname))

        self._validLogo = True
        self.__logo = logo

    def toLandscapeItemAttributes(self):
        dict = {}
        dict['item'] = None
        attributes = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]
        for i in attributes:
            if i == 'orgname':
                dict['name'] = getattr(self,i)
            elif i == 'website':
                dict['homepage_url'] = getattr(self,i)
            elif i == 'membership':
                continue
            else:
                dict[i] = getattr(self,i)

        return dict

    def isValidLandscapeItem(self):
        return self._validWebsite and self._validLogo and self._validCrunchbase and self.orgname != ''

#
# Abstract Members class to normalize the methods used for the other ways of getting a member's info
#
class Members:

    def __init__(self, loadData = False):
        if loadData:
            self.loadData()

    def loadData(self):
        pass

    def find(self, org, website):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website):
                return member

        return False

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

    members = []
    sf_username = None
    sf_password = None
    sf_token = None
    project = 'The Linux Foundation'

    crunchbaseURL = 'https://www.crunchbase.com/{uri}'

    def __init__(self, sf_username = None, sf_password = None, sf_token = None, loadData = False):
        if ( sf_username and sf_password and sf_token ):
            self.sf_username = sf_username
            self.sf_password = sf_password
            self.sf_token = sf_token
            super().__init__(loadData)

    def loadData(self):
        print("--Loading SFDC Members data--")
        sf = Salesforce(username=self.sf_username,password=self.sf_password,security_token=self.sf_token)
        result = sf.query("select Account.Name, Account.Website, Account.Logo_URL__c, Account.cbit__Clearbit__r.cbit__CompanyCrunchbaseHandle__c, Account.cbit__Clearbit__r.cbit__CompanyTicker__c, Product2.Name from Asset where Asset.Status in ('Active','Purchased') and Asset.Project__c = '{project}'".format(project=self.project))

        for record in result['records']:
            member = Member()
            try:
                member.orgname = record['Account']['Name']
            except ValueError as e:
                pass
            try:
                member.website = record['Account']['Website']
            except ValueError as e:
                pass
            try:
                member.membership = record['Product2']['Name']
            except ValueError as e:
                pass
            try:
                member.logo = record['Account']['Logo_URL__c']
            except ValueError as e:
                pass
            try:
                if record['Account']['cbit__Clearbit__r'] and record['Account']['cbit__Clearbit__r']['cbit__CompanyCrunchbaseHandle__c']:
                    member.crunchbase = self.crunchbaseURL.format(uri=record['Account']['cbit__Clearbit__r']['cbit__CompanyCrunchbaseHandle__c'])
            except ValueError as e:
                pass

            self.members.append(member)

    def find(self, org, website, membership):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        for member in self.members:
            if ( self.normalizeCompany(member.org) == normalizedorg or member.website == website) and member.membership == membership:
                return member

        return False

class LandscapeMembers(Members):

    members = []
    landscapeListYAML = 'https://raw.githubusercontent.com/cncf/landscapeapp/master/landscapes.yml'
    landscapeSettingsYAML = 'https://raw.githubusercontent.com/{repo}/master/settings.yml'
    landscapeLandscapeYAML = 'https://raw.githubusercontent.com/{repo}/master/landscape.yml'
    landscapeLogo = 'https://raw.githubusercontent.com/{repo}/master/hosted_logos/{logo}'
    skipLandscapes = []

    def __init__(self, landscapeListYAML = None, loadData = False):
        if landscapeListYAML:
            self.landscapeListYAML = landscapeListYAML
        super().__init__(loadData)

    def loadData(self):
        print("--Loading other landscape members data--")

        response = requests.get(self.landscapeListYAML)
        landscapeList = yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)

        for landscape in landscapeList['landscapes']:
            if landscape in self.skipLandscapes:
                continue

            print("Loading "+landscape['name']+"...")

            # first figure out where memberships live
            response = requests.get(self.landscapeSettingsYAML.format(repo=landscape['repo']))
            settingsYaml = yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)
            membershipKey = settingsYaml['global']['membership']

            # then load in members only
            response = requests.get(self.landscapeLandscapeYAML.format(repo=landscape['repo']))
            landscapeYaml = yaml.load(response.content, Loader=ruamel.yaml.RoundTripLoader)
            for category in landscapeYaml['landscape']:
                if membershipKey in category['name']:
                    for subcategory in category['subcategories']:
                        for item in subcategory['items']:
                            if not item.get('crunchbase'):
                                item['crunchbase'] = ''
                            member = Member()
                            for key, value in item.items():
                                try:
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
        if logo is None:
            return ""

        if 'https://' in logo or 'http://' in logo:
            return logo

        return self.landscapeLogo.format(repo=landscapeRepo,logo=logo)

class CrunchbaseMembers(Members):

    members = []
    crunchbaseKey = ''
    bulkdata = True
    bulkdatafile = 'organizations.csv'

    def __init__(self, crunchbaseKey = None, bulkdata = True, bulkdatafile = None, loadData = False):
        if bulkdata:
            self.bulkdata = bulkdata
        if bulkdatafile:
            self.bulkdatafile = bulkdatafile
        if self.bulkdata:
            super().__init__(loadData)
        else:
            if crunchbaseKey:
                self.crunchbaseKey = crunchbaseKey
            elif 'CRUNCHBASE_KEY' in os.environ:
                self.crunchbaseKey = os.getenv('CRUNCHBASE_KEY')

    def loadData(self):
        # load from bulk export file contents
        if not self.bulkdata:
            return False

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

    def find(self, org, website):
        if self.bulkdata:
            return super().find(org, website)

        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        cb = CrunchBase(self.crunchbaseKey)

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

                return member

        return False

class LFWebsiteMembers(Members):

    members = []
    lfwebsiteurl = 'https://www.linuxfoundation.org/membership/members/'

    def loadData(self):
        print("--Loading members listed on LF Website--")

        response = requests.get(self.lfwebsiteurl)
        soup = BeautifulSoup(response.content, "html.parser")
        companies = soup.find_all("div", class_="single-member-icon")
        for entry in companies:
            member = Member()
            try:
                member.membership = ''
            except ValueError as e:
                pass
            try:
                member.orgname = entry.contents[1].contents[0].attrs['alt']
            except ValueError as e:
                pass
            try:
                member.website = self.normalizeURL(entry.contents[1].attrs['href'])
            except ValueError as e:
                pass
            try:
                member.logo = entry.contents[1].contents[0].attrs['src']
            except ValueError as e:
                pass

            self.members.append(member)

class CsvMembers(Members):

    members = []
    csvfile = 'missing.csv'

    def __init__(self, csvfile = None, loadData = False):
        if csvfile:
            self.csvfile = csvfile
        super().__init__(loadData)

    def loadData(self):
        print("--Loading members from csv input file {filename}--".format(filename=self.csvfile))

        with open(self.csvfile, newline='') as csvfile:
            memberreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            fields = next(memberreader)
            for row in memberreader:
                member = Member()
                try:
                    member.orgname = row[0]
                except ValueError as e:
                    pass
                try:
                    member.website = row[2]
                except ValueError as e:
                    pass
                try:
                    member.logo = row[1]
                except ValueError as e:
                    pass
                try:
                    member.crunchbase = row[3]
                except ValueError as e:
                    pass

                self.members.append(member)

class LandscapeOutput:

    landscapefile = '../landscape.yml'
    landscape = None
    landscapeMembers = []
    missingcsvfile = 'missing.csv'
    _missingcsvfilewriter = None
    hostedLogosDir = '../hosted_logos/'

    landscapeMemberCategory = 'LF Member Company'
    landscapeMemberClasses = [
        {"name": "Associate Membership", "category": "Associate"},
        {"name": "Gold Membership", "category": "Gold"},
        {"name": "Platinum Membership", "category": "Platinum"},
        {"name": "Silver Membership", "category": "Silver"},
        {"name": "Silver Membership - MPSF", "category": "Silver"}
    ]
    membersAdded = 0
    membersUpdated = 0

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
            self.landscapeMembers.append(memberClass)

        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                x['subcategories'] = self.landscapeMembers

    def loadLandscape(self):
        self.landscape = yaml.load(open(self.landscapefile, 'r', encoding="utf8", errors='ignore'), Loader=ruamel.yaml.RoundTripLoader)
        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                self.landscapeMembers = x['subcategories']

    def writeMissing(self, name, logo, homepage_url, crunchbase):
        if self._missingcsvfilewriter is None:
            self._missingcsvfilewriter = csv.writer(open(self.missingcsvfile, mode='w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            self._missingcsvfilewriter.writerow(['name','logo','homepage_url','crunchbase'])

        self._missingcsvfilewriter.writerow([name, logo, homepage_url, crunchbase])

    def hostLogo(self,logo,orgname):
        if 'https://' not in logo and 'http://' not in logo:
            return logo

        print("...Hosting logo for "+orgname)
        filename = str(orgname).strip().replace(' ', '_')
        filename = re.sub(r'(?u)[^-\w.]', '', filename)
        i = 1
        while os.path.isfile("../hosted_logos/"+filename+".svg"):
            filename = filename+"_"+str(i)
            i = i + 1

        r = requests.get(logo, allow_redirects=True)
        open(self.hostedLogosDir+"/"+filename+".svg", 'wb').write(r.content)

        return filename+".svg"

    def updateLandscape(self):
        # now write it back
        for x in self.landscape['landscape']:
            if x['name'] == self.landscapeMemberCategory:
                x['subcategories'] = self.landscapeMembers

        with open(self.landscapefile, 'w', encoding = "utf-8") as landscapefileoutput:
            landscapefileoutput.write( yaml.dump(self.landscape, default_flow_style=False, allow_unicode=True, Dumper=ruamel.yaml.RoundTripDumper) )

        print("Successfully added "+str(self.membersAdded)+" members and updated "+str(self.membersUpdated)+" member entries")
