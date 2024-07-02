#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import os
from urllib.parse import urlparse
import logging
import socket

## third party modules
from url_normalize import url_normalize
import validators
import requests
import requests_cache
from github import Github, GithubException, RateLimitExceededException, Auth

from landscape_tools.svglogo import SVGLogo

#
# Member object to ensure we have normalization on fields. Only required fields are defined; others can be added dynamically.
#
class Member:

    membership = None
    entrysuffix = ''
    second_path = []
    organization = {}
    extra = {}
    __orgname = None
    __website = None
    __logo = None
    __crunchbase = None
    __linkedin = None
    __twitter = None
    __repo_url = None

    entrysuffix = ''

    @property
    def orgname(self):
        return self.__orgname

    @orgname.setter
    def orgname(self, orgname):
        if not orgname or orgname == '':
            orgname = None

        self.__orgname = orgname

    @property
    def repo_url(self):
        return self.__repo_url

    @repo_url.setter
    def repo_url(self, repo_url):
        if repo_url == '':
            self.__repo_url = None
        elif repo_url is not None:
            repo_url = repo_url.rstrip("/")
            repo_url = url_normalize(repo_url, default_scheme='https')

            if self._isGitHubRepo(repo_url):
                logging.info("{} is determined to be a GitHub Repo for orgname '{}'".format(repo_url,self.orgname))
                # clean up to ensure it's a valid github repo url
                x = urlparse(repo_url);
                parts = x.path.split("/");
                self.__repo_url = "https://github.com/{}/{}".format(parts[1],parts[2])
            elif self._isGitHubOrg(repo_url):
                logging.info("{} is determined to be a GitHub Org for orgname '{}' - finding related GitHub Repo".format(repo_url,self.orgname))
                self.project_org = repo_url
                try:
                    self.__repo_url = self._getPrimaryGitHubRepoFromGitHubOrg(repo_url)
                    logging.info("{} is determined to be the associated GitHub Repo for GitHub Org {} for orgname '{}'".format(self.__repo_url,self.project_org,self.orgname))
                except ValueError as e:
                    logging.warn(e)
                    self.__repo_url = repo_url
            else:
                logging.info("{} is determined to be something else".format(repo_url))
                self.__repo_url = repo_url

    def _isGitHubRepo(self, url):
        return ( urlparse(url).netloc == 'www.github.com' or urlparse(url).netloc == 'github.com') and len(urlparse(url).path.split("/")) == 3

    def _isGitHubOrg(self, url):
        return ( urlparse(url).netloc == 'www.github.com' or urlparse(url).netloc == 'github.com') and len(urlparse(url).path.split("/")) == 2

    def _getPrimaryGitHubRepoFromGitHubOrg(self, url):
        if not self._isGitHubOrg(url):
            return url
        
        while True:
            try:
                if 'GITHUB_TOKEN' in os.environ:
                    g = Github(auth=Auth.Token(os.environ['GITHUB_TOKEN']), per_page=1000)
                else:
                    g = Github(per_page=1000)
                return g.get_organization(urlparse(url).path.split("/")[1]).get_repos()[0].html_url if g.get_organization(urlparse(url).path.split("/")[1]).get_repos().totalCount > 0 else None
            except RateLimitExceededException:
                logging.info("Sleeping until we get past the API rate limit....")
                time.sleep(g.rate_limiting_resettime-now())
            except GithubException as e:
                if e.status == 502:
                    logging.info("Server error - retrying...")
                else:
                    raise ValueError(e.data)
            except socket.timeout:
                logging.info("Server error - retrying...")

        apiEndPoint = 'https://api.github.com/orgs{}/repos'.format(urlparse(url).path)
        session = requests_cache.CachedSession('githubapi')
        with session.get(apiEndPoint) as endpointResponse:
            if not endpointResponse.ok or len(endpointResponse.json()) == 0:
                raise ValueError("Cannot find repos under GitHub Organization '{}' for orgname '{}'".format(url,self.orgname))
             
            return endpointResponse.json()[0]["html_url"]

    @property
    def linkedin(self):
        return self.__linkedin

    @linkedin.setter
    def linkedin(self, linkedin):
        if linkedin == '' or not linkedin:
            self.__linkedin = None
        # See if this is just the short form part of the LinkedIn URL
        elif linkedin.startswith('company'):
            self.__linkedin = "https://www.linkedin.com/{}".format(linkedin)
        # If it is a URL, make sure it's properly formed
        elif ( urlparse(linkedin).netloc == 'linkedin.com' or urlparse(linkedin).netloc == 'www.linkedin.com' ):
            self.__linkedin = "https://www.linkedin.com{}".format(urlparse(linkedin).path)
        else:
            self.__linkedin = None
            raise ValueError("Member.linkedin for '{orgname}' must be set to a valid LinkedIn URL - '{linkedin}' provided".format(linkedin=linkedin,orgname=self.orgname))

    @property
    def crunchbase(self):
        return self.__crunchbase

    @crunchbase.setter
    def crunchbase(self, crunchbase):
        if crunchbase == '':
            self.__crunchbase = None
        elif crunchbase and ( urlparse(crunchbase).netloc == 'crunchbase.com' or urlparse(crunchbase).netloc == 'www.crunchbase.com' ) and urlparse(crunchbase).path.split("/")[1] == 'organization':
            self.__crunchbase = "https://www.crunchbase.com{}".format(urlparse(crunchbase).path)
        else:
            self.__crunchbase = None
            raise ValueError("Member.crunchbase for '{orgname}' must be set to a valid Crunchbase URL - '{crunchbase}' provided".format(crunchbase=crunchbase,orgname=self.orgname))

    @property
    def website(self):
        return self.__website

    @website.setter
    def website(self, website):
        if website == '' or website is None:
            self.__website = None
            raise ValueError("Member.website must be not be blank for '{orgname}'".format(orgname=self.orgname))
        else:
            normalizedwebsite = url_normalize(website, default_scheme='https')
            if not validators.url(normalizedwebsite):
                self.__website = None
                raise ValueError("Member.website for '{orgname}' must be set to a valid website - '{website}' provided".format(website=website,orgname=self.orgname))
            else:
                self.__website = normalizedwebsite

    @property
    def logo(self):
        return self.__logo.filename(self.orgname) if type(self.__logo) is SVGLogo else None

    @logo.setter
    def logo(self, logo):
        if logo is None or logo == '':
            self.__logo = None
            raise ValueError("Member.logo must be not be blank for '{orgname}'".format(orgname=self.orgname))
        elif type(logo) is SVGLogo:
            self.__logo = logo
        elif urlparse(logo).scheme != '':
            self.__logo = SVGLogo(url=logo)
        else:
            self.__logo = SVGLogo(filename=logo)

        if not self.__logo.isValid():
            self.__logo = None
            raise ValueError("Member.logo for '{orgname}' invalid format".format(orgname=self.orgname))
    
    def hostLogo(self, path = "./"):
        self.__logo.save(self.orgname,path)

    @property
    def twitter(self):
        return self.__twitter

    @twitter.setter
    def twitter(self, twitter):
        if not twitter or twitter == "":
            self.__twitter = None
        elif not twitter.startswith('https://twitter.com/'):
            # fix the URL if it's not formatted right
            o = urlparse(twitter)
            if o.netloc == '':
                self.__twitter = "https://twitter.com/{}".format(twitter)
            elif (o.netloc == "twitter.com" or o.netloc == "www.twitter.com"):
                self.__twitter = "https://twitter.com{path}".format(path=o.path)
            else:
                self.__twitter = None
                raise ValueError("Member.twitter for '{orgname}' must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=twitter,orgname=self.orgname))
        else:
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
            'second_path',
            'extra',
            'other_repo_url'
        ]
        returnentry = {'item': None}

        for i in allowedKeys:
            if i == 'name':
                returnentry['name'] = "{}{}".format(self.orgname,self.entrysuffix)
            elif i == 'homepage_url':
                returnentry['homepage_url'] = self.website
            elif i == 'repo_url' and not self.repo_url:
                continue
            elif i == 'twitter' and not self.twitter:
                continue
            elif i == 'second_path' and len(self.second_path) == 0:
                continue
            elif i == 'extra' and len(self.extra) == 0:
                continue
            elif i == 'organization' and len(self.organization) == 0:
                continue
            elif hasattr(self,i):
                returnentry[i] = getattr(self,i)

        if not self.crunchbase:
            logging.getLogger().info("No Crunchbase entry for '{}' - specifying orgname instead".format(self.orgname))
            returnentry['organization'] = {}
            returnentry['organization']['name'] = self.orgname
            returnentry['organization']['linkedin'] = self.linkedin
            del returnentry['crunchbase']

        return returnentry
        
    def isValidLandscapeItem(self):
        return self.website and self.logo and self.orgname

    def invalidLandscapeItemAttributes(self):
        invalidAttributes = []
        if not self.website:
            invalidAttributes.append('website')
        if not self.logo:
            invalidAttributes.append('logo')
        if not self.orgname:
            invalidAttributes.append('orgname')

        return invalidAttributes

    #
    # Overlay this Member data on another Member
    #
    def overlay(self, membertooverlay, onlykeys = []):

        memberitems = self.toLandscapeItemAttributes().items()

        for key, value in memberitems:
            if key in ['item','name','organization']:
                continue
            if onlykeys and key not in onlykeys:
                continue
            # translate website and name to the Member object attribute name
            if key == "homepage_url":
                key = "website"
            if (not hasattr(membertooverlay,key) or not getattr(membertooverlay,key)): 
                logging.getLogger().info("...Overlay "+key)
                logging.getLogger().info(".....Old Value - '{}'".format(getattr(membertooverlay,key) if hasattr(membertooverlay,key) else'empty'))
                logging.getLogger().info(".....New Value - '{}'".format(value if value else 'empty'))
                setattr(membertooverlay, key, value)

