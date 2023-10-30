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
    
    projectSlug = 'tlf'
    lfxprojects = LFXProjects(project = projectSlug)

    lflandscape = LandscapeOutput()
    #lflandscape.landscapeMemberCategory = config.landscapeMemberCategory
    #lflandscape.landscapeMemberClasses = config.landscapeMemberClasses
    #lflandscape.landscapefile = config.landscapefile
    #lflandscape.missingcsvfile = config.missingcsvfile
    #lflandscape.newLandscape()


    # now pull the projects list and add entries for them
    projectsLandscape = {}
    for project in lfxprojects.members:
        print("Processing {}...".format(project.orgname))
        if project.parent_slug not in projectsLandscape:
            projectsLandscape[project.parent_slug] = []
        if project.slug != projectSlug:
            subprojects = LFXProjects(project=project.slug)
            if len(subprojects.members) > 1:
                print("- Loading Subprojects...")
                for subproject in subprojects.members:
                    print("- Processing {}...".format(subproject.orgname))
                    if subproject.parent_slug not in projectsLandscape:
                        projectsLandscape[subproject.parent_slug] = []
                    try:
                        subproject.logo = lflandscape.hostLogo(logo=subproject.logo,orgname=subproject.orgname)
                    except ValueError as e:
                        pass
                    if subproject.isValidLandscapeItem():
                        projectsLandscape[subproject.parent_slug].append(subproject.toLandscapeItemAttributes())
                    else:
                        print("...Missing key attributes - skip")
                        lflandscape.removeHostedLogo(subproject.logo)
                        lflandscape.writeMissing(
                            subproject.orgname,
                            subproject.logo,
                            subproject.website,
                            subproject.crunchbase
                            )
                print("- Adding main project...")
                if project.slug not in projectsLandscape:
                    projectsLandscape[project.slug] = []
                try:
                    project.logo = lflandscape.hostLogo(logo=project.logo,orgname=project.orgname)
                except ValueError as e:
                    pass
                if project.isValidLandscapeItem():
                    projectsLandscape[project.slug].append(project.toLandscapeItemAttributes())
                else:
                    print("...Missing key attributes - skip")
                    lflandscape.removeHostedLogo(project.logo)
                    lflandscape.writeMissing(
                        project.orgname,
                        project.logo,
                        project.website,
                        project.crunchbase
                        )
            else:
                try:
                    project.logo = lflandscape.hostLogo(logo=project.logo,orgname=project.orgname)
                except ValueError as e:
                    pass
                if project.isValidLandscapeItem():
                    projectsLandscape[projectSlug].append(project.toLandscapeItemAttributes())
                else:
                    print("...Missing key attributes - skip")
                    lflandscape.removeHostedLogo(project.logo)
                    lflandscape.writeMissing(
                        project.orgname,
                        project.logo,
                        project.website,
                        project.crunchbase
                        )
   
    subcategories = []
    for section in projectsLandscape:
        if section != 'tlf':
            subcategories.append({
                'subcategory': None,
                'name': lfxprojects.findBySlug(section).orgname,
                'items': projectsLandscape[section]
                })

    lflandscape.loadLandscape()
    found = False
    for x in lflandscape.landscape['landscape']:
        if x['name'] == 'Projects':
            x['subcategories'] = subcategories
            found = True
            continue

    if not found:
        print("Couldn't find the projects category in landscape.yml to update - please check your config.yaml settings")
    


    def _removeNulls(yamlout):
        return re.sub('/(- \w+:) null/g', '$1', yamlout)
    

    landscapefileoutput = Path('landscape.yml')
    ryaml = ruamel.yaml.YAML()
    ryaml.indent(mapping=2, sequence=4, offset=2)
    ryaml.default_flow_style = False
    ryaml.allow_unicode = True
    ryaml.width = 160
    ryaml.Dumper = ruamel.yaml.RoundTripDumper
    ryaml.dump(lflandscape.landscape,landscapefileoutput, transform=_removeNulls)

    #lflandscape.updateLandscape()
    print("This took "+str(datetime.now() - startTime)+" seconds")

if __name__ == '__main__':
    main()

