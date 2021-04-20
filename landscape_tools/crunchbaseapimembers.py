#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import os

from pycrunchbase import CrunchBase

from landscape_tools.members import Members
from landscape_tools.member import Member

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


