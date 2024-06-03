#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging

# third party modules
import requests
import requests_cache
from urllib.parse import urlparse

from landscape_tools.members import Members
from landscape_tools.member import Member
from landscape_tools.svglogo import SVGLogo

class LFXProjects(Members):

    project = '' 
    defaultCrunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?$filter=parentSlug%20eq%20{}&pageSize=2000&orderBy=name'
    singleSlugEndpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug={}' 

    defaultCategory = ''
    defaultSubcategory = ''

    activeOnly = True
    addTechnologySector = True
    addIndustrySector = True
    addPMOManagedStatus = True
    addParentProject = True

    def __init__(self, project = None, loadData = True):
        if project:
            self.project = project
        super().__init__(loadData)

    def loadData(self):
        print("--Loading LFX Projects data--")

        session = requests_cache.CachedSession('landscape')
        with session.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
            for record in memberList['Data']:
                if 'Website' in record and self.find(record['Name'],record['Website']):
                    continue
                if self.activeOnly and record['Status'] != 'Active':
                    continue
                if not record['DisplayOnWebsite']:
                    continue
                if record['TestRecord']:
                    continue

                second_path = []
                member = Member()
                member.membership = 'All'
                try:
                    member.orgname = record['Name']
                except (ValueError,KeyError) as e:
                    pass
                try:
                    member.website = record['Website']
                except (ValueError,KeyError) as e:
                    pass
                try:
                    member.project_id = record['ProjectID']
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
                try:
                    member.slug = record['Slug']
                except (ValueError,KeyError) as e:
                    pass
                try:
                    member.description = record['Description']
                except (ValueError,KeyError) as e:
                    pass
                if 'ProjectLogo' in record:
                    try:
                        member.logo = record['ProjectLogo']
                    except ValueError as e:
                        member.logo = SVGLogo.createTextLogo(member.orgname)
                else:
                    member.logo = SVGLogo.createTextLogo(member.orgname)
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
                if self.addPMOManagedStatus and 'HasProgramManager' in record and record['HasProgramManager'] != False:
                    try:
                        member.second_path.append('PMO Managed / All')
                    except ValueError as e:
                        pass
                if self.addIndustrySector and 'IndustrySector' in record and record['IndustrySector'] != '':
                    try:
                        second_path.append('Industry / {}'.format(record['IndustrySector'].replace("/",":")))
                    except ValueError as e:
                        pass
                if self.addTechnologySector and 'TechnologySector' in record and record['TechnologySector'] != '':
                    try:
                        sectors = record['TechnologySector'].split(";")
                        for sector in sectors:
                            second_path.append('Technology Sector / {}'.format(sector.replace("/",":")))
                    except ValueError as e:
                        pass
                if self.addParentProject and 'ParentSlug' in record and record['ParentSlug'] != '':
                    try:
                        parentName = self.lookupParentProjectNameBySlug(record['ParentSlug'])
                        if parentName:
                            second_path.append('Project Group / {}'.format(parentName.replace("/",":")))
                    except ValueError as e:
                        pass
                if 'RepositoryURL' in record and record['RepositoryURL'] != '':
                    try:
                        if self._isGitHubRepo(record['RepositoryURL']):
                            member.repo_url = record['RepositoryURL']
                        elif self._isGitHubOrg(record['RepositoryURL']):
                            member.project_org = record['RepositoryURL']
                            member.repo_url = self._getPrimaryGitHubRepoFromGitHubOrg(record['RepositoryURL']
)
                    except ValueError as e:
                        pass
                member.second_path = second_path
                #print(member.second_path)
                self.members.append(member)

    def findBySlug(self, slug):
        for member in self.members:
            if member.slug is not None and member.slug == slug:
                return member

    def _isGitHubRepo(self, url):
        return urlparse(url).netloc.endswith('github.com') and urlparse(url).path.split("/") == 3

    def _isGitHubOrg(self, url):
        return urlparse(url).netloc.endswith('github.com') and urlparse(url).path.split("/") == 2

    def _getPrimaryGitHubRepoFromGitHubOrg(self, url):
        if not self._isGitHubOrg(url):
            return url

        apiEndPoint = 'https://api.github.com/orgs{}'.format(urlparse(url).path)
        session = requests_cache.CachedSession('githubapi')
        with session.get(apiEndPoint) as endpointResponse:
            response = endpointResponse.json()
            return response[0]["html_url"]

    def lookupParentProjectNameBySlug(self, slug):
        session = requests_cache.CachedSession('landscape')
        with session.get(self.singleSlugEndpointURL.format(slug)) as endpointResponse:
            parentProject = endpointResponse.json()
            return parentProject['Data'][0]["Name"]
        
        return False

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

