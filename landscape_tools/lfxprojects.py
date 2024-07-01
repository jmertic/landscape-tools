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
        logger = logging.getLogger()
        logger.info("Loading LFX Projects data for {}".format(self.project))

        session = requests_cache.CachedSession()
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
                extra = {}
                member = Member()
                member.membership = 'All'
                member.orgname = record['Name'] if 'Name' in record else None
                logger.info("Found LFX Project '{}'".format(member.orgname))
                member.project_id = record['ProjectID'] if 'ProjectID' in record else None
                member.slug = record['Slug'] if 'Slug' in record else None
                extra['accepted'] = record['StartDate'] if 'StartDate' in record else None 
                # Let's include the root project
                if member.slug == self.project:
                    continue
                member.description = record['Description'] if 'Description' in record else None
                try:
                    member.website = record['Website'] if 'Website' in record else None
                except (ValueError,KeyError) as e:
                    logger.info("{} - try to add RepositoryURL instead".format(e))
                    try:
                        member.website = record['RepositoryURL'] if 'RepositoryURL' in record else None
                    except (ValueError,KeyError) as e:
                        logger.warning(e)
                try:
                    member.repo_url = record['RepositoryURL'] if 'RepositoryURL' in record else None
                except (ValueError,KeyError) as e:
                    logger.warning(e)
                try:
                    member.parent_slug = record['ParentSlug'] 
                    if self.addParentProject:
                        parentName = self.lookupParentProjectNameBySlug(member.parent_slug)
                        if parentName:
                            second_path.append('Project Group / {}'.format(parentName.replace("/",":")))
                except (ValueError,KeyError) as e:
                    logger.warning(e)
                    member.parent_slug = self.project
                try:
                    member.logo = record['ProjectLogo'] if 'ProjectLogo' in record else None
                except (ValueError,KeyError) as e:
                    logger.info("{} - will try to create text logo".format(e))
                    try:
                        member.logo = SVGLogo(name=member.orgname)
                    except ValueError as e:
                        logger.warning(e)
                member.crunchbase = record['CrunchBaseURL'] if 'CrunchbaseURL' in record else self.defaultCrunchbase
                try:
                    member.twitter = record['Twitter'] if 'Twitter' in record else None
                except (ValueError,KeyError) as e:
                    logger.warning(e)
                if self.addPMOManagedStatus and 'HasProgramManager' in record and record['HasProgramManager']:
                    try:
                        second_path.append('PMO Managed / All')
                    except (ValueError,KeyError) as e:
                        logger.warning(e)
                if self.addIndustrySector and 'IndustrySector' in record and record['IndustrySector'] != '':
                    try:
                        second_path.append('Industry / {}'.format(record['IndustrySector'].replace("/",":")))
                    except (ValueError,KeyError) as e:
                        logger.warning(e)
                if self.addTechnologySector and 'TechnologySector' in record and record['TechnologySector'] != '':
                    try:
                        sectors = record['TechnologySector'].split(";")
                        for sector in sectors:
                            second_path.append('Technology Sector / {}'.format(sector.replace("/",":")))
                    except (ValueError,KeyError) as e:
                        logger.warning(e)
                member.extra = extra
                member.second_path = second_path
                self.members.append(member)

    def findBySlug(self, slug):
        for member in self.members:
            if member.slug is not None and member.slug == slug:
                return member

    def lookupParentProjectNameBySlug(self, slug):
        session = requests_cache.CachedSession()
        if slug:
            with session.get(self.singleSlugEndpointURL.format(slug)) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject['Data']) > 0: 
                    return parentProject['Data'][0]["Name"]
                logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug)) 
        
        return False

    def find(self, org, website, membership = None, repo_url = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if membership:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite ) and member.membership == membership:
                    members.append(member)
            elif repo_url:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite or member.repo_url == repo_url):
                    members.append(member)
            else:
                if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == normalizedwebsite ):
                    members.append(member)
                
        return members

