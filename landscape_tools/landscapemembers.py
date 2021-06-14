#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## third party modules
import ruamel.yaml
import requests

from landscape_tools.members import Members
from landscape_tools.member import Member

class LandscapeMembers(Members):

    landscapeListYAML = 'https://raw.githubusercontent.com/cncf/landscapeapp/master/landscapes.yml'
    landscapeSettingsYAML = 'https://raw.githubusercontent.com/{repo}/master/settings.yml'
    landscapeLandscapeYAML = 'https://raw.githubusercontent.com/{repo}/master/landscape.yml'
    landscapeLogo = 'https://raw.githubusercontent.com/{repo}/master/hosted_logos/{logo}'
    skipLandscapes = ['openjsf']

    def __init__(self, landscapeListYAML = None, loadData = True):
        if landscapeListYAML:
            self.landscapeListYAML = landscapeListYAML
        super().__init__(loadData)

    def loadData(self):
        print("--Loading other landscape members data--")

        response = requests.get(self.landscapeListYAML)
        landscapeList = ruamel.yaml.YAML(typ='unsafe', pure=True).load(response.content)

        for landscape in landscapeList['landscapes']:
            if landscape['name'] in self.skipLandscapes:
                continue

            print("Loading "+landscape['name']+"...")

            # first figure out where memberships live
            response = requests.get(self.landscapeSettingsYAML.format(repo=landscape['repo']))
            settingsYaml = ruamel.yaml.YAML(typ='unsafe', pure=True).load(response.content) 
            # skip landscape if not well formed
            if 'global' not in settingsYaml or settingsYaml['global'] is None or 'membership' not in settingsYaml['global']:
                continue
            membershipKey = settingsYaml['global']['membership']

            # then load in members only
            response = requests.get(self.landscapeLandscapeYAML.format(repo=landscape['repo']))
            landscapeYaml = ruamel.yaml.YAML(typ='unsafe', pure=True).load(response.content)
            for category in landscapeYaml['landscape']:
                if membershipKey in category['name']:
                    for subcategory in category['subcategories']:
                        for item in subcategory['items']:
                            if not item.get('crunchbase'):
                                item['crunchbase'] = ''
                            member = Member()
                            for key, value in item.items():
                                try:
                                    if key != 'enduser':
                                        setattr(member, key, value)
                                except ValueError as e:
                                    pass
                            try:
                                member.membership = ''
                            except ValueError as e:
                                pass
                            try:
                                member.orgname = item['name']
                            except ValueError as e:
                                pass
                            try:
                                member.website = item['homepage_url']
                            except ValueError as e:
                                pass
                            try:
                                member.logo = self.normalizeLogo(item['logo'],landscape['repo'])
                            except ValueError as e:
                                pass
                            try:
                                member.crunchbase = item['crunchbase']
                            except ValueError as e:
                                pass
                            self.members.append(member)

    def normalizeLogo(self, logo, landscapeRepo):
        if logo is None or logo == '':
            return ""

        if 'https://' in logo or 'http://' in logo:
            return logo

        return self.landscapeLogo.format(repo=landscapeRepo,logo=logo)

