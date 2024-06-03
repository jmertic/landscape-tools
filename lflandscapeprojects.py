#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from landscape_tools.config import Config
from landscape_tools.lfxprojects import LFXProjects
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.crunchbasemembers import CrunchbaseMembers
from landscape_tools.landscapeoutput import LandscapeOutput

from datetime import datetime
from argparse import ArgumentParser,FileType
from os import path
from pathlib import Path
import re

import ruamel.yaml

def main():
    
    startTime = datetime.now()
    
    lfxprojects = LFXProjects()

    config = Config()
    config.landscapeMemberCategory = 'Projects'
    config.landscapeMemberClasses = [{"name": "All", "category": "All"}]

    lflandscape = LandscapeOutput()
    lflandscape.landscapeMemberCategory = config.landscapeMemberCategory
    lflandscape.landscapeMemberClasses = config.landscapeMemberClasses
    lflandscape.landscapefile = config.landscapefile
    lflandscape.missingcsvfile = config.missingcsvfile
    lflandscape.hostedLogosDir = config.hostedLogosDir
    lflandscape.loadLandscape(reset=True)

    # now pull the projects list and add entries for them
    for member in lfxprojects.members:
        print("Processing {}...".format(member.orgname))
        for memberClass in lflandscape.landscapeMembers:
            landscapeMemberClass = next((item for item in config.landscapeMemberClasses if item["name"] == member.membership), None)
            if ( not landscapeMemberClass is None ) and ( landscapeMemberClass['name'] == member.membership ) and ( memberClass['name'] == landscapeMemberClass['category'] ) :
                 
                # Write out to missing.csv if it's missing key parameters
                if not member.isValidLandscapeItem():
                    print("...Missing key attributes - skip")
                    lflandscape.writeMissing(
                        member.orgname,
                        member.website
                        )
                # otherwise we can add it
                else:
                    print("...Added to Landscape")
                    member.hostLogo(config.hostedLogosDir)
                    lflandscape.membersAdded += 1
                    # host the logo
                    if config.memberSuffix:
                        member.entrysuffix = config.memberSuffix
                    memberClass['items'].append(member.toLandscapeItemAttributes())
                break

    lflandscape.updateLandscape()

    print("This took "+str(datetime.now() - startTime)+" seconds")

if __name__ == '__main__':
    main()

