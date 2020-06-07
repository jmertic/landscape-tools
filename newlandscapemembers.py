#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from LandscapeTools import Config, Member, Members, SFDCMembers, LandscapeMembers, CrunchbaseMembers, LFWebsiteMembers, CsvMembers, LandscapeOutput
from datetime import datetime

startTime = datetime.now()

# load config
config = Config("config.yaml")

# load member data sources
sfdcmembers = SFDCMembers(loadData = False, sf_username = config.sf_username, sf_password = config.sf_password, sf_token = config.sf_token)
sfdcmembers.project = config.project
sfdcmembers.loadData()
lfwmembers = LFWebsiteMembers(loadData = True)
cbmembers = CrunchbaseMembers(loadData = False)
lsmembers = LandscapeMembers(loadData = False)
lsmembers.skipLandscapes = [config.landscapeName]
lsmembers.loadData()
#csvmembers  = CsvMembers(loadData = True, csvfile = config.missingcsvfile)
lflandscape = LandscapeOutput()
lflandscape.landscapeMemberCategory = config.landscapeMemberCategory
lflandscape.landscapeMemberClasses = config.landscapeMemberClasses
lflandscape.landscapefile = config.landscapefile
lflandscape.missingcsvfile = config.missingcsvfile
lflandscape.newLandscape()

# Iterate through the SFDCMembers and update the landscapeMembers
for member in sfdcmembers.members:
    print("Processing "+member.orgname)
    for memberClass in lflandscape.landscapeMembers:
        landscapeMemberClass = next((item for item in config.landscapeMemberClasses if item["name"] == member.membership), None)
        if ( not landscapeMemberClass is None ) and ( landscapeMemberClass['name'] == member.membership ) and ( memberClass['name'] == landscapeMemberClass['category'] ) :
            # lookup in other landscapes
            lookupmember = lsmembers.find(member.orgname, member.website)
            if lookupmember:
                print("...Data from other landscape")
                for key, value in lookupmember.toLandscapeItemAttributes().items():
                    try:
                        if not hasattr(member,key) or not getattr(member,key):
                            setattr(member, key, value)
                    except ValueError as e:
                        print(e)
            else:
                print("...Data from SFDC")
                # overlay lfwebsite data
                lfwmember = lfwmembers.find(member.orgname,member.website)
                if lfwmember:
                    if member.logo is None and lfwmember.logo is not None and lfwmember.logo != '':
                        print("...Updating logo from LF website")
                        member.logo = lfwmember.logo
                    if member.website is None and lfwmember.website is not None and lfwmember.website != '':
                        print("...Updating website from LF website")
                        member.website = lfwmember.website
                # overlay crunchbase data
                if not member.crunchbase:
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
                #member.logo = lflandscape.hostLogo(logo=member.logo,orgname=member.orgname)
                memberClass['items'].append(member.toLandscapeItemAttributes())
            break

lflandscape.updateLandscape()
print("This took "+str(datetime.now() - startTime)+" seconds")
