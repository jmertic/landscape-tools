#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import re
from abc import ABC, abstractmethod

## third party modules
from url_normalize import url_normalize

from landscape_tools.config import Config

#
# Abstract Members class to normalize the methods used for the other ways of getting a member's info
#
class Members(ABC):

    def __init__(self, config: type[Config], loadData = True):
        self.processConfig(config)
        self.members = []
        if loadData:
            self.loadData()

    @abstractmethod
    def processConfig(self, config: type[Config]):
        pass

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
