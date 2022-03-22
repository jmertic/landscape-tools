#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from landscape_tools.config import Config
from landscape_tools.sfdcprojects import SFDCProjects
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
    
    projectSlug = 'tlf'
    sfdcprojects = SFDCProjects(project = projectSlug)

    lflandscape = LandscapeOutput()
    #lflandscape.landscapeMemberCategory = config.landscapeMemberCategory
    #lflandscape.landscapeMemberClasses = config.landscapeMemberClasses
    #lflandscape.landscapefile = config.landscapefile
    #lflandscape.missingcsvfile = config.missingcsvfile
    #lflandscape.newLandscape()


    # now pull the projects list and add entries for them
    projectsLandscape = {}
    for project in sfdcprojects.members:
        print("Processing {}...".format(project.orgname))
        if project.parent_slug not in projectsLandscape:
            projectsLandscape[project.parent_slug] = []
        if project.slug != projectSlug:
            subprojects = SFDCProjects(project=project.slug)
            for subproject in subprojects.members:
                print("- Processing {}...".format(subproject.orgname))
                if subproject.parent_slug not in projectsLandscape:
                    projectsLandscape[subproject.parent_slug] = []
                if subproject.isValidLandscapeItem():
                    try:
                        subproject.logo = lflandscape.hostLogo(logo=subproject.logo,orgname=subproject.orgname)
                    except ValueError as e:
                        pass
                    projectsLandscape[subproject.parent_slug].append(subproject.toLandscapeItemAttributes())
            if project.isValidLandscapeItem():
                if project.slug not in projectsLandscape:
                    projectsLandscape[project.slug] = []
                    try:
                        project.logo = lflandscape.hostLogo(logo=project.logo,orgname=project.orgname)
                    except ValueError as e:
                        pass
                projectsLandscape[project.slug].append(project.toLandscapeItemAttributes())
        else:
            try:
                project.logo = lflandscape.hostLogo(logo=project.logo,orgname=project.orgname)
            except ValueError as e:
                pass
            projectsLandscape[project.parent_slug].append(project.toLandscapeItemAttributes())
   
    subcategories = []
    for section in projectsLandscape:
        if section != 'tlf':
            subcategories.append({
                'subcategory': None,
                'name': sfdcprojects.findBySlug(section).orgname,
                'items': projectsLandscape[section]
                })

    fullLandscape = {
        'landscape': [{
            'category': None,
            'name': 'Projects',
            'subcategories': subcategories
            }]
        }


    def _removeNulls(yamlout):
        return re.sub('/(- \w+:) null/g', '$1', yamlout)
    

    landscapefileoutput = Path('landscape.yml')
    ryaml = ruamel.yaml.YAML()
    ryaml.indent(mapping=2, sequence=4, offset=2)
    ryaml.default_flow_style = False
    ryaml.allow_unicode = True
    ryaml.width = 160
    ryaml.Dumper = ruamel.yaml.RoundTripDumper
    ryaml.dump(fullLandscape,landscapefileoutput, transform=_removeNulls)
    

    #lflandscape.updateLandscape()
    print("This took "+str(datetime.now() - startTime)+" seconds")

if __name__ == '__main__':
    main()

