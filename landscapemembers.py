#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from landscape_tools.config import Config
from landscape_tools.sfdcmembers import SFDCMembers
from landscape_tools.sfdcprojects import SFDCProjects
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.crunchbasemembers import CrunchbaseMembers
from landscape_tools.landscapeoutput import LandscapeOutput

from datetime import datetime
from argparse import ArgumentParser,FileType
from os import path

def main():
    
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
    sfdcmembers = SFDCMembers(project = config.project)
    cbmembers = CrunchbaseMembers()
    lsmembers = LandscapeMembers()

    lflandscape = LandscapeOutput()
    lflandscape.landscapeMemberCategory = config.landscapeMemberCategory
    lflandscape.landscapeMemberClasses = config.landscapeMemberClasses
    lflandscape.landscapefile = config.landscapefile
    lflandscape.missingcsvfile = config.missingcsvfile
    if path.exists(config.landscapefile):
        lflandscape.loadLandscape(reset=True)
    else:
        lflandscape.newLandscape()

    # Iterate through the SFDCMembers and update the landscapeMembers
    for member in sfdcmembers.members:
        print("Processing "+member.orgname)
        for memberClass in lflandscape.landscapeMembers:
            landscapeMemberClass = next((item for item in config.landscapeMemberClasses if item["name"] == member.membership), None)
            if ( not landscapeMemberClass is None ) and ( landscapeMemberClass['name'] == member.membership ) and ( memberClass['name'] == landscapeMemberClass['category'] ) :
                # lookup in other landscapes
                for lookupmember in lsmembers.find(member.orgname, member.website):
                    print("...Overlay other landscape data")
                    lookupmember.overlay(member)
                
                # overlay crunchbase data
                for cbmember in cbmembers.find(member.orgname,member.website):
                    if (not member.crunchbase and cbmember):
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
                    if config.memberSuffix:
                        member.entrysuffix = config.memberSuffix
                    memberClass['items'].append(member.toLandscapeItemAttributes())
                break

    # Interate through SFDCProjects and update the landscapeMembers
    sfdcprojects = SFDCProjects(project = config.project)
    for project in sfdcprojects.members:
        print("Processing "+member.orgname)


    lflandscape.updateLandscape()
    print("This took "+str(datetime.now() - startTime)+" seconds")

if __name__ == '__main__':
    main()
