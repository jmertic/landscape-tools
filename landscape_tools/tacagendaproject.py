#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging
import json
import os
import subprocess

# third party modules
import requests
import requests_cache
from urllib.parse import urlparse

from landscape_tools.members import Members
from landscape_tools.member import Member
from landscape_tools.svglogo import SVGLogo
from landscape_tools.config import Config

class TACAgendaProject(Members):

    gh_project_id = None
    gh_org = None
    parent_slug = None

    pcc_committee_url = 'https://api-gw.platform.linuxfoundation.org/project-service/v2/public/projects/{project_id}/committees/{committee_id}/members'
    gh_cli_call = "gh project item-list {gh_project_id} --owner {gh_org} --format json"

    def processConfig(self, config: type[Config]):
        self.parent_slug = config.slug
        self.defaultCrunchbase = config.projectsDefaultCrunchbase
        if config.tacAgendaProjectUrl:
            urlparts = urlparse(config.tacAgendaProjectUrl).path.split('/')
            if urlparts and urlparts[1] == 'orgs' and urlparts[3] == 'projects':
                self.gh_org = urlparts[2]
                self.gh_project_id = urlparts[4]

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading TAC Agenda Project data")
        
        if not self.gh_project_id or not self.gh_org:
            id = self.gh_project_id if self.gh_project_id else ''
            org = self.gh_org if self.gh_org else ''
            logger.error("Cannot find GitHub Project - ID:{id} Org:{org}".format(id=id,org=org))
            return None

        jsonProjectData = subprocess.run(self.gh_cli_call.format(gh_project_id=self.gh_project_id,gh_org=self.gh_org), shell=True, capture_output=True).stdout

        csvRows = []
        projectData = json.loads(jsonProjectData)
        for item in projectData['items']:
            if '2-annual-review' not in item['labels']:
                continue

            logger.info("Processing {}...".format(item['content']['title']))
            member = Member()
            member.orgname = item['content']['title']
            member.crunchbase = self.defaultCrunchbase
            extra = {} 
            extra['annual_review_date'] = item['last Review Date'] if 'last Review Date' in item else None
            extra['slug'] = item['slug'] if 'slug' in item else None
            extra['annual_review_url'] = item['content']['url']
            extra['next_annual_review_date'] = item['scheduled Date'] if 'scheduled Date' in item else None
            session = requests_cache.CachedSession()
            if 'pCC Project ID' in item and 'pCC TSC Committee ID' in item:
                with session.get(self.pcc_committee_url.format(project_id=item['pCC Project ID'],committee_id=item['pCC TSC Committee ID'])) as endpointResponse:
                    memberList = endpointResponse.json()
                    if 'Data' in memberList and memberList['Data']:
                        for record in memberList['Data']:
                            if 'Role' in record and record['Role'] == 'Chair':
                                extra['chair'] = '{} {}'.format(record['FirstName'],record['LastName'])
                                break

            member.extra = extra
            self.members.append(member)
