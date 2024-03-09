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


class LFXProjects(Members):

    project = 'tlf' # The Linux Foundation
    defaultCrunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=parentSlug%20eq%20{}'

    defaultCategory = ''
    defaultSubcategory = ''

    def __init__(self, project = None, loadData = True):

        if project:
            self.project = project
        super().__init__(loadData)

    def loadData(self):
        print("--Loading LFX Projects data--")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
            for record in memberList['Data']:
                if 'Website' in record and self.find(record['Name'],record['Website']):
                    continue
                if record['Status'] != 'Active':
                    continue
                if not record['DisplayOnWebsite']:
                    continue
                if record['TestRecord']:
                    continue

                member = Member()
                try:
                    member.orgname = record['Name']
                except (ValueError,KeyError) as e:
                    pass
                try:
                    member.website = record['Website']
                except (ValueError,KeyError) as e:
                    pass
                try:
                    member.repo_url = record['RepositoryURL']
                except (ValueError,KeyError) as e:
                    pass
                if 'ParentSlug' in record:
                    try:
                        member.parent_slug = record['ParentSlug']
                    except ValueError as e:
                        member.parent_slug = self.project
                else:
                    member.parent_slug = 'tlf'
                if 'Slug' in record:
                    try:
                        member.slug = record['Slug']
                    except ValueError as e:
                        pass
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
                if 'IndustrySector' in record and record['IndustrySector'] != '':
                    try:
                        member.second_path = 'Industry / {}'.format(record['IndustrySector'])
                    except ValueError as e:
                        pass
                self.members.append(member)

    def findBySlug(self, slug):
        for member in self.members:
            if member.slug is not None and member.slug == slug:
                return member

    def find(self, org, website, membership = None, repo_url = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if membership:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website) and member.membership == membership:
                    members.append(member)
            elif repo_url:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website or self.repo_url == repo_url):
                    members.append(member)
            else:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website ):
                    members.append(member)
                
        return members

