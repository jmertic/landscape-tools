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


class LFXMembers(Members):

    project = 'tlf' # The Linux Foundation

    endpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects/{}/members?orderBy=name' 

    def __init__(self, project = None, loadData = True):

        if project:
            self.project = project
        super().__init__(loadData)

    def loadData(self):
        print("--Loading LFX Members data--")

        with requests.get(self.endpointURL.format(self.project)) as endpointResponse:
            memberList = endpointResponse.json()
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
                    member.membership = self.__normalizeMembershipName(record['Membership']['Name'])
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

    def __normalizeMembershipName(self,name):
        parts = name.split(" - ")
        if len(parts) > 1:
            parts2 = parts[1].split(" (")
            return parts2[0]
        
        return name
