#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from LandscapeTools import Config, Member, Members, SFDCMembers, LandscapeMembers, CrunchbaseMembers, LFWebsiteMembers, CsvMembers, LandscapeOutput
from datetime import datetime
from argparse import ArgumentParser,FileType

startTime = datetime.now()

# load config
parser = ArgumentParser()
parser.add_argument("-c", "--config", dest="configfile", type=FileType('r'), help="name of YAML config file")
args = parser.parse_args()
if args.configfile:
    config = Config(args.configfile)
else:
    config = Config("config.yaml")

# load member data sources
sfdcmembers = SFDCMembers(loadData = True, sf_username = config.sf_username, sf_password = config.sf_password, sf_token = config.sf_token)
lfwmembers = LFWebsiteMembers(loadData = True)
cbmembers = CrunchbaseMembers(loadData = True)
lsmembers = LandscapeMembers(loadData = False)
lsmembers.skipLandscapes = [config.landscapeName]
lsmembers.loadData()
#csvmembers  = CsvMembers(loadData = True)
lflandscape = LandscapeOutput(loadLandscape = True)

# Iterate through the SFDCMembers and add new members
for member in sfdcmembers.members:
    print("Processing "+member.orgname)

    if not member.crunchbase:
        lsmember = lsmembers.find(member.orgname, member.website)
        if lsmember:
            try:
                print("...Get crunchbase from landscape")
                member.crunchbase = lsmember.crunchbase
            except ValueError as e:
                print(e)
        else:
            cbmember = cbmembers.find(member.orgname,member.website)
            if cbmember:
                try:
                    print("...Get crunchbase from Crunchbase")
                    member.crunchbase = cbmember.crunchbase
                except ValueError as e:
                    print(e)
    # see if member is found in landscape
    found = 0
    for memberClass in lflandscape.landscapeMembers:
        for landscapeMember in memberClass['items']:
            if member.crunchbase == landscapeMember['crunchbase'] or sfdcmembers.normalizeCompany(landscapeMember['name']) == sfdcmembers.normalizeCompany(member.orgname):
                print("...Already in landscape")
                found = 1

    if found:
        continue

    # not found, add it
    print("...Not in landscape")
    for memberClass in lflandscape.landscapeMembers:
        landscapeClassFound = list(filter(lambda landscapeClass: landscapeClass['name'] == memberClass['name'], config.landscapeMemberClasses))
        if landscapeClassFound:
            # lookup in other landscapes
            lookupmember = lsmembers.find(member.orgname, member.website)
            if lookupmember:
                print("...Data from other landscape")
                for key, value in lookupmember.toLandscapeItemAttributes().items():
                    try:
                        setattr(member, key, value)
                    except ValueError as e:
                        print(e)
            else:
                print("...Data from SFDC")
                # overlay lfwebsite data
                lfwmember = lfwmembers.find(member.orgname,member.website)
                if lfwmember:
                    if lfwmember.logo is not None and lfwmember.logo != '':
                        print("...Updating logo from LF website")
                        member.logo = lfwmember.logo
                    if lfwmember.website is not None and lfwmember.website != '':
                        print("...Updating website from LF website")
                        member.website = lfwmember.website
                # overlay crunchbase data
                cbmember = cbmembers.find(member.orgname,member.website)
                if cbmember:
                    print("...Updating crunchbase from Crunchbase")
                    member.crunchbase = cbmember.crunchbase

            # Write out to missing.csv if it's missing key parameters
            if not member.isValidLandscapeItem():
                print("...Missing key attributes - skip")
                lflandscape.writeMissing(
                    member.orgname,
                    member.logo,
                    member.website,
                    member.crunchbase
                    )
            # otherwise we can add it
            else:
                print("...Added to Landscape")
                lflandscape.membersAdded += 1
                # host the logo
                member.logo = lflandscape.hostLogo(logo=member.logo,orgname=member.orgname)
                memberClass['items'].append(member.toLandscapeItemAttributes())

lflandscape.updateLandscape()
print("This took "+str(datetime.now() - startTime)+" seconds")
