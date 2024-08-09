#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import sys
import os
import io
import logging

## third party modules
import ruamel.yaml
import requests
import requests_cache

class Config:

    project = None
    view = 'members'
    slug = None
    landscapeMembersCategory = 'Members'
    landscapeMembersSubcategories = [
        {"name": "Premier Membership", "category": "Premier"},
        {"name": "General Membership", "category": "General"},
    ]
    landscapeProjectsCategory = 'Projects'
    landscapeProjectsSubcategories = [
       {"name": "All", "category": "All"} 
    ]
    basedir = "."
    landscapefile = 'landscape.yml'
    missingcsvfile = 'missing.csv'
    hostedLogosDir = 'hosted_logos'
    memberSuffix = None
    projectsAddTechnologySector = False
    projectsAddIndustrySector = False
    projectsAddPMOManagedStatus = False
    projectsAddParentProject = False
    projectsDefaultCrunchbase = 'https://www.crunchbase.com/organization/linux-foundation'
    projectsFilterByParentSlug = True
    tacAgendaProjectUrl = None
    artworkRepoUrl = None

    def __init__(self, config_file: io.TextIOWrapper = None, view = None):
        if config_file:
            data_loaded = ruamel.yaml.YAML(typ='safe', pure=True).load(config_file)
            self.view = view if self._isValidViewOption(view) else Config.view
            self.basedir = data_loaded['basedir'] if 'basedir' in data_loaded else os.path.dirname(os.path.normpath(config_file.name))
            self.slug = data_loaded['slug'] if 'slug' in data_loaded else Config.slug
            self.project = data_loaded['project'] if 'project' in data_loaded else self._lookupProjectFromSlug(self.slug)
            if not self.slug or not self.project:
                raise ValueError("Invalid project specification in config file")
            self.landscapeProjectsCategory = data_loaded['landscapeProjectsCategory'] if 'landscapeProjectsCategory' in data_loaded else Config.landscapeProjectsCategory
            self.landscapeProjectsSubcategories = data_loaded['landscapeProjectsSubcategories'] if 'landscapeProjectsSubcategories' in data_loaded else Config.landscapeProjectsSubcategories
            self.landscapeMembersCategory = data_loaded['landscapeMembersCategory'] if 'landscapeMembersCategory' in data_loaded else Config.landscapeMembersCategory
            self.landscapeMembersCategory = data_loaded['landscapeMemberCategory'] if 'landscapeMemberCategory' in data_loaded else Config.landscapeMembersCategory
            self.landscapeMembersSubcategories = data_loaded['landscapeMembersSubcategories'] if 'landscapeMembersSubcategories' in data_loaded else Config.landscapeMembersSubcategories
            self.landscapeMembersSubcategories = data_loaded['landscapeMemberClasses'] if 'landscapeMemberClasses' in data_loaded else Config.landscapeMembersSubcategories
            self.landscapefile = data_loaded['landscapefile'] if 'landscapefile' in data_loaded else Config.landscapefile
            self.missingcsvfile = data_loaded['missingcsvfile'] if 'missingcsvfile' in data_loaded else Config.missingcsvfile
            self.hostedLogosDir = data_loaded['hostedLogosDir'] if 'hostedLogosDir' in data_loaded else Config.hostedLogosDir
            self.memberSuffix = data_loaded['memberSuffix'] if 'memberSuffix' in data_loaded else Config.memberSuffix
            self.projectsAddTechnologySector = data_loaded['projectsAddTechnologySector'] if 'projectsAddTechnologySector' in data_loaded else Config.projectsAddTechnologySector
            self.projectsAddIndustrySector = data_loaded['projectsAddIndustrySector'] if 'projectsAddIndustrySector' in data_loaded else Config.projectsAddIndustrySector
            self.projectsAddPMOManagedStatus = data_loaded['projectsAddPMOManagedStatus'] if 'projectsAddPMOManagedStatus' in data_loaded else Config.projectsAddPMOManagedStatus
            self.projectsAddParentProject = data_loaded['projectsAddParentProject'] if 'projectsAddParentProject' in data_loaded else Config.projectsAddParentProject
            self.projectsDefaultCrunchbase = data_loaded['projectsDefaultCrunchbase'] if 'projectsDefaultCrunchbase' in data_loaded else Config.projectsDefaultCrunchbase
            self.projectsFilterByParentSlug = data_loaded['projectsFilterByParentSlug'] if 'projectsFilterByParentSlug' in data_loaded else Config.projectsFilterByParentSlug
            self.tacAgendaProjectUrl = data_loaded['tacAgendaProjectUrl'] if 'tacAgendaProjectUrl' in data_loaded else Config.tacAgendaProjectUrl
            self.artworkRepoUrl = data_loaded['artworkRepoUrl'] if 'artworkRepoUrl' in data_loaded else Config.artworkRepoUrl

    def _isValidViewOption(self,view):
        return view in ['projects','members'] 

    @property
    def landscapeCategory(self):
        if self.view == 'projects':
            return self.landscapeProjectsCategory
        elif self.view == 'members':
            return self.landscapeMembersCategory

    @property
    def landscapeSubcategories(self):
        if self.view == 'projects':
            return self.landscapeProjectsSubcategories
        elif self.view == 'members':
            return self.landscapeMembersSubcategories

    def _lookupProjectFromSlug(self, slug):
        singleSlugEndpointURL = 'https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug={}' 
        session = requests_cache.CachedSession()
        if slug:
            with session.get(singleSlugEndpointURL.format(slug)) as endpointResponse:
                parentProject = endpointResponse.json()
                if len(parentProject['Data']) > 0: 
                    return parentProject['Data'][0]["ProjectID"]
        
        logging.getLogger().warning("Couldn't find project for slug '{}'".format(slug)) 
        
        return None
