#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import os
from urllib.parse import urlparse

## third party modules
from url_normalize import url_normalize
import validators

#
# Member object to ensure we have normalization on fields. Only required fields are defined; others can be added dynamically.
#
class Member:

    orgname = None
    membership = None
    __website = None
    __logo = None
    __crunchbase = None
    __twitter = None
    __repo_url = None

    # we'll use these to keep track of whether the member has valid fields
    _validWebsite = False
    _validLogo = False
    _validCrunchbase = False
    _validTwitter = False
    _validRepo = False

    @property
    def repo_url(self):
        return self.__repo_url

    @repo_url.setter
    def repo_url(self, repo_url):
        if repo_url is None:
            self._validRepo = False
            raise ValueError("repo_url must be not be blank for {orgname}".format(orgname=self.orgname))
        if not repo_url.startswith('https://github.com/'):
            self._validRepo = False
            raise ValueError("repo_url must be for GitHub for {orgname}".format(orgname=self.orgname))

        self._validRepo = True
        self.__repo_url = repo_url



    @property
    def crunchbase(self):
        return self.__crunchbase

    @crunchbase.setter
    def crunchbase(self, crunchbase):
        if crunchbase is None:
            self._validCrunchbase = False
            raise ValueError("Member.crunchbase must be not be blank for {orgname}".format(orgname=self.orgname))
        if not crunchbase.startswith('https://www.crunchbase.com/organization/'):
            # fix the URL if it's not formatted right
            o = urlparse(crunchbase)
            if (o.netloc == "crunchbase.com" or o.netloc == "www.crunchbase.com") and o.path.startswith("/organization"):
                crunchbase = "https://www.crunchbase.com{path}".format(path=o.path)
            else:
                self._validCrunchbase = False
                raise ValueError("Member.crunchbase for {orgname} must be set to a valid crunchbase url - '{crunchbase}' provided".format(crunchbase=crunchbase,orgname=self.orgname))

        self._validCrunchbase = True
        self.__crunchbase = crunchbase

    @property
    def website(self):
        return self.__website

    @website.setter
    def website(self, website):
        if website is None:
            self._validWebsite = False
            raise ValueError("Member.website must be not be blank for {orgname}".format(orgname=self.orgname))

        normalizedwebsite = url_normalize(website, default_scheme='https')
        if not validators.url(normalizedwebsite):
            self._validWebsite = False
            raise ValueError("Member.website for {orgname} must be set to a valid website - '{website}' provided".format(website=website,orgname=self.orgname))

        self._validWebsite = True
        self.__website = normalizedwebsite

    @property
    def logo(self):
        return self.__logo

    @logo.setter
    def logo(self, logo):
        if logo is None:
            self._validLogo = False
            raise ValueError("Member.logo must be not be blank for {orgname}".format(orgname=self.orgname))

        if not os.path.splitext(logo)[1] == '.svg':
            self._validLogo = False
            raise ValueError("Member.logo for {orgname} must be an svg file - '{logo}' provided".format(logo=logo,orgname=self.orgname))

        self._validLogo = True
        self.__logo = logo

    @property
    def twitter(self):
        return self.__twitter

    @twitter.setter
    def twitter(self, twitter):
        if not twitter:
            return
        if not twitter.startswith('https://twitter.com/'):
            # fix the URL if it's not formatted right
            o = urlparse(twitter)
            if o.netloc == '':
                twitter = "https://twitter.com/{}".format(twitter)
            elif (o.netloc == "twitter.com" or o.netloc == "www.twitter.com"):
                twitter = "https://twitter.com{path}".format(path=o.path)
            else:
                self._validTwitter = False
                raise ValueError("Member.twitter for {orgname} must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=twitter,orgname=self.orgname))

        self._validTwitter = True
        self.__twitter = twitter


    def toLandscapeItemAttributes(self):
        allowedKeys = [
            'name',
            'homepage_url',
            'logo',
            'twitter',
            'repo_url',
            'crunchbase',
            'project_org',
            'additional_repos',
            'stock_ticker',
            'description',
            'branch',
            'project',
            'url_for_bestpractices',
            'enduser',
            'open_source',
            'allow_duplicate_repo',
            'unnamed_organization',
            'organization',
            'joined',
            'other_repo_url'
        ]
        returnentry = {'item': None}

        for i in allowedKeys:
            if i == 'name':
                returnentry['name'] = self.orgname
            elif i == 'homepage_url':
                returnentry['homepage_url'] = self.website
            elif i == 'twitter' and ( not self.twitter or self.twitter == ''):
                continue
            elif hasattr(self,i):
                returnentry[i] = getattr(self,i)

        return returnentry
        
    def isValidLandscapeItem(self):
        return self._validWebsite and self._validLogo and self._validCrunchbase and self.orgname != ''

    #
    # Overlay this Member data on another Member
    #
    def overlay(self, membertooverlay, onlykeys = []):

        memberitems = self.toLandscapeItemAttributes().items()

        for key, value in memberitems:
            if key in ['item','name']:
                continue
            if onlykeys and key not in onlykeys:
                continue
            # translate website and name to the Member object attribute name
            if key == "homepage_url":
                key = "website"
            if key == "name":
                key = "orgname"
            try:
                if (not hasattr(membertooverlay,key) or not getattr(membertooverlay,key)): 
                    print("...Overlay "+key)
                    print(".....Old Value - '{}'".format(getattr(membertooverlay,key) if hasattr(membertooverlay,key) else'empty'))
                    print(".....New Value - '{}'".format(value if value else 'empty'))
                    setattr(membertooverlay, key, value)
            except ValueError as e:
                print(e)

