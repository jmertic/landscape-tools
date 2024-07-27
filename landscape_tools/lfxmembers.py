#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import logging

# third party modules
import requests

from landscape_tools.members import Members
from landscape_tools.member import Member
from landscape_tools.svglogo import SVGLogo
from landscape_tools.config import Config

class LFXMembers(Members):

    project = ''
    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name&status=Active,At Risk' 
    
    def processConfig(self, config: type[Config]):
        self.project = config.project

    def loadData(self):
        logger = logging.getLogger()
        logger.info("Loading LFX Members data")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
            for record in memberList:
                record['Website'] = '' if 'Website' not in record else record['Website']
                if self.find(record['Name'],record['Website'],record['Membership']['Name']):
                    continue

                member = Member()
                member.orgname = record['Name'] if 'Name' in record else None
                logger.info("Found LFX Member '{}'".format(member.orgname))
                member.membership = record['Membership']['Name'] if 'Membership' in record and 'Name' in record['Membership'] else None
                try:
                    member.website = record['Website']
                except ValueError as e:
                    logger.warning(e)
                try:
                    member.logo = record['Logo'] if 'Logo' in record else None
                except ValueError as e:
                    logger.info("{} - will try to create text logo".format(e))
                    member.logo = SVGLogo(name=member.orgname)
                try:
                    member.crunchbase = record['CrunchBaseURL'] if 'CrunchBaseURL' in record else None
                except ValueError as e:
                    logger.warning(e)
                try:
                    member.twitter = record['Twitter'] if 'Twitter' in record else None
                except ValueError as e:
                    logger.warning(e)
                try:
                    member.linkedin = record['LinkedInURL'] if 'LinkedInURL' in record else None
                except ValueError as e:
                    logger.warning(e)
                self.members.append(member)

    def find(self, org, website, membership = None):
        normalizedorg = self.normalizeCompany(org)
        normalizedwebsite = self.normalizeURL(website)

        members = []
        for member in self.members:
            if ( self.normalizeCompany(member.orgname) == normalizedorg or member.website == website) and member.membership == membership:
                members.append(member)

        return members
