#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from LandscapeTools import Config, Member, Members, SFDCMembers, LandscapeMembers, CrunchbaseMembers, LandscapeOutput
from datetime import datetime
from argparse import ArgumentParser,FileType
import os.path
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
    sfdcmembers = SFDCMembers(loadData = False, memberClasses = config.landscapeMemberClasses, sf_username = config.sf_username, sf_password = config.sf_password, sf_token = config.sf_token)
    sfdcmembers.project = config.project
    sfdcmembers.loadData()
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
                lookupmember = lsmembers.find(member.orgname, member.website)
                if lookupmember:
                    print("...Data from other landscape")
                    for key, value in lookupmember.toLandscapeItemAttributes().items():
                        try:
                            if not hasattr(member,key) or not getattr(member,key):
                                setattr(member, key, value)
                            if key == 'crunchbase' and value != getattr(member,key):
                                setattr(member, key, value)
                        except ValueError as e:
                            print(e)
                else:
                    print("...Data from SFDC")
                    # overlay crunchbase data
                    cbmember = cbmembers.find(member.orgname,member.website)
                    if not member.crunchbase and cbmember:
                        print("...Updating crunchbase from Crunchbase")
                        member.crunchbase = cbmember.crunchbase
                    elif cbmember and member.crunchbase != cbmember.crunchbase:
                        print("...Using crunchbase from Crunchbase")
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
                break

    lflandscape.updateLandscape()
    print("This took "+str(datetime.now() - startTime)+" seconds")

if __name__ == '__main__':
    main()
