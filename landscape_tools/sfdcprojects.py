#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

# third party modules
import requests

from landscape_tools.members import Members
from landscape_tools.member import Member


class SFDCProjects(Members):

    project = 'tlf' # The Linux Foundation
    defaultCrunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=parentSlug%20eq%20{}'

    def __init__(self, project = None, loadData = True):

        if project:
            self.project = project
        super().__init__(loadData)

    def loadData(self):
        print("--Loading SFDC Projects data--")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
            for record in memberList:
                if self.find(record['Name'],record['Website']):
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
                    member.repo_url = record['RepositoryURL']
                except ValueError as e:
                    pass
                if 'ParentSlug' in record:
                    try:
                        member.slug = record['ParentSlug']
                    except ValueError as e:
                        member.slug = self.project
                if 'ProjectLogo' in record:
                    try:
                        member.logo = record['ProjectLogo']
                    except ValueError as e:
                        pass
                if 'CrunchBaseURL' in record and record['CrunchBaseURL'] != '':
                    try:
                        member.crunchbase = record['CrunchBaseURL']
                    except ValueError as e:
                        member.crunchbase = self.defaultCrunchbase
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

