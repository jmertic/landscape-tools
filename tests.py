#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import unittest.mock
from unittest.mock import Mock, MagicMock, patch, mock_open
from unittest import mock
import tempfile
import os
import responses
from responses.registries import OrderedRegistry
import requests
import logging
import json

from landscape_tools.config import Config
from landscape_tools.cli import Cli
from landscape_tools.member import Member
from landscape_tools.members import Members
from landscape_tools.lfxmembers import LFXMembers
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.landscapeoutput import LandscapeOutput
from landscape_tools.svglogo import SVGLogo
from landscape_tools.lfxprojects import LFXProjects

class TestConfig(unittest.TestCase):

    def testLoadConfig(self):
        testconfigfilecontents = """
hostedLogosDir: 'hosted_logos'
landscapeMemberClasses:
   - name: Premier Membership
     category: Premier
   - name: General Membership
     category: General
   - name: Associate Membership
     category: Associate
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
landscapeMemberCategory: ASWF Member Company
memberSuffix: " (help)"
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.project,"a09410000182dD2AAI")
            self.assertEqual(config.landscapeCategory,"ASWF Member Company")
            self.assertEqual(config.landscapefile,"landscape.yml")
            self.assertEqual(config.missingcsvfile,"missing.csv")
            self.assertEqual(config.landscapeSubcategories[0]['name'],"Premier Membership")
            self.assertEqual(config.memberSuffix," (help)")

        os.unlink(tmpfilename.name)

    def testLoadConfigMissingCsvFileLandscapeFile(self):
        testconfigfilecontents = """
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
landscapefile: foo.yml
missingcsvfile: foo.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.project,"a09410000182dD2AAI")
            self.assertEqual(config.landscapefile,"foo.yml")
            self.assertEqual(config.missingcsvfile,"foo.csv")

        os.unlink(tmpfilename.name)
    
    def testLoadConfigDefaults(self):
        testconfigfilecontents = """
project: a09410000182dD2AAI # Academy Software Foundation
slug: aswf
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.landscapeCategory,'Members')
            self.assertEqual(config.landscapeSubcategories,[
                {"name": "Premier Membership", "category": "Premier"},
                {"name": "General Membership", "category": "General"},
            ])
            self.assertEqual(config.landscapefile,'landscape.yml')
            self.assertEqual(config.missingcsvfile,'missing.csv')
            self.assertEqual(config.hostedLogosDir,'hosted_logos')
            self.assertIsNone(config.memberSuffix)
            self.assertEqual(config.project,"a09410000182dD2AAI")

        os.unlink(tmpfilename.name)

    def testLoadConfigDefaultsNotSet(self):
        testconfigfilecontents = """
projectewew: a09410000182dD2AAI # Academy Software Foundation
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with self.assertRaises(ValueError, msg="'project' not defined in config file"):
            config = Config(tmpfilename.name)

        os.unlink(tmpfilename.name)

    def testLoadProjectsConfig(self):
        testconfigfilecontents = """
landscapeName: lfenergy
landscapeMemberClasses:
  - name: Strategic Membership
    category: Strategic
  - name: Premier Membership
    category: Strategic
  - name: General Membership
    category: General
  - name: Associate Membership
    category: Associate
project: a094100001Cb6HaAAJ # LF Energy Foundation
slug: lfenergy
landscapeMemberCategory: LF Energy Member
landscapeProjectsCategory: LF Energy Projects
landscapeProjectsSubcategories:
  - name: All
    category: All
landscapefile: landscape.yml
memberSuffix: ' (member)'
missingcsvfile: missing.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp,view='projects')

            self.assertEqual(config.project,"a094100001Cb6HaAAJ")
            self.assertEqual(config.landscapeCategory,"LF Energy Projects")
            self.assertEqual(config.landscapefile,"landscape.yml")
            self.assertEqual(config.missingcsvfile,"missing.csv")
            self.assertEqual(config.landscapeSubcategories[0]['name'],"All")
            self.assertEqual(config.memberSuffix," (member)")

        os.unlink(tmpfilename.name)

    def testLoadUndefinedConfig(self):
        testconfigfilecontents = """
landscapeName: lfenergy
landscapeMemberClasses:
  - name: Strategic Membership
    category: Strategic
  - name: Premier Membership
    category: Strategic
  - name: General Membership
    category: General
  - name: Associate Membership
    category: Associate
project: a094100001Cb6HaAAJ # LF Energy Foundation
slug: lfenergy
landscapeMemberCategory: LF Energy Member
landscapeProjectsCategory: LF Energy Projects
landscapeProjectsSubcategories:
  - name: All
    category: All
landscapefile: landscape.yml
memberSuffix: ' (member)'
missingcsvfile: missing.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp,view='undefined')
            
            self.assertEqual(config.view,Config.view)

        os.unlink(tmpfilename.name)

    @responses.activate
    def testLookupSlugByProjectID(self):

        responses.add(
            method=responses.GET,
            url='https://api-gw.platform.linuxfoundation.org/project-service/v1/public/projects?slug=aswf',
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Model": [
                            "Membership"
                        ],
                        "Name": "Academy Software Foundation (ASWF)",
                        "ProjectID": "a09410000182dD2AAI",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/aswf.svg",
                        "ProjectType": "Project Group",
                        "RepositoryURL": "https://github.com/academysoftwarefoundation",
                        "Slug": "aswf",
                        "StartDate": "2018-08-10",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Website": "https://www.aswf.io/"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 1
                }
            })

        testconfigfilecontents = """
slug: aswf
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        with open(tmpfilename.name) as fp:
            config = Config(fp)

            self.assertEqual(config.slug,'aswf')
            self.assertEqual(config.project,"a09410000182dD2AAI")

        os.unlink(tmpfilename.name)

class TestMember(unittest.TestCase):

    def testLinkedInValid(self):
        validLinkedInURLs = [
            'https://www.linkedin.com/company/1nce',
            'company/1nce',
            'https://linkedin.com/company/1nce',
        ]

        for validLinkedInURL in validLinkedInURLs:
            member = Member()
            member.linkedin = validLinkedInURL
            self.assertEqual(member.linkedin,'https://www.linkedin.com/company/1nce')

    def testSetLinkedInNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        member.linkedin = ''
        self.assertIsNone(member.linkedin)

    def testSetLinkedNotValid(self):
        invalidLinkedInURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidLinkedInURL in invalidLinkedInURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError):
                member.linkedin = invalidLinkedInURL
            self.assertIsNone(member.linkedin)
    
    def testSetCrunchbaseValid(self):
        validCrunchbaseURLs = [
            'https://www.crunchbase.com/organization/visual-effects-society'
        ]

        for validCrunchbaseURL in validCrunchbaseURLs:
            member = Member()
            member.crunchbase = validCrunchbaseURL
            self.assertEqual(member.crunchbase,validCrunchbaseURL)

    def testSetCrunchbaseNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        member.crunchbase = ''
        self.assertIsNone(member.crunchbase)

    def testSetRepoNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        member.repo_url = ''
        self.assertIsNone(member.repo_url)
    
    def testSetRepoGitlab(self):
        member = Member()
        member.orgname = 'test'
        member.repo_url = 'https://gitlab.com/foo/bar'
        self.assertEqual(member.repo_url,'https://gitlab.com/foo/bar')

    def testSetCrunchbaseNotValid(self):
        invalidCrunchbaseURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidCrunchbaseURL in invalidCrunchbaseURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError):
                member.crunchbase = invalidCrunchbaseURL
            self.assertIsNone(member.crunchbase)

    def testSetWebsiteValid(self):
        validWebsiteURLs = [
            {'before':'https://crunchbase.com/','after':'https://crunchbase.com/'},
            {'before':'sony.com/en','after':'https://sony.com/en'}
        ]

        for validWebsiteURL in validWebsiteURLs:
            member = Member()
            member.website = validWebsiteURL['before']
            self.assertEqual(member.website,validWebsiteURL['after'])

    def testSetWebsiteNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertRaises(ValueError,msg="Member.website must be not be blank for test") as ctx:
            member.website = ''

        self.assertIsNone(member.website)

    def testSetWebsiteNotValid(self):
        invalidWebsiteURLs = [
            'htps:/yahoo.com',
            '/dog/'
        ]

        for invalidWebsiteURL in invalidWebsiteURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError,msg="Member.website for test must be set to a valid website - '{website}' provided".format(website=invalidWebsiteURL)) as ctx:
                member.website = invalidWebsiteURL

            self.assertIsNone(member.website)

    def testSetLogoValid(self):
        validLogos = [
            'dog.svg'
        ]

        for validLogo in validLogos:
            with patch("builtins.open", mock_open(read_data="data")) as mock_file:
                member = Member()
                member.orgname = 'dog'
                member.logo = validLogo
                self.assertEqual(member.logo,validLogo)

    def testSetLogoNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertRaises(ValueError,msg="Member.logo must be not be blank for test") as ctx:
            member.logo = ''

        self.assertIsNone(member.logo)

    def testSetLogoNotValid(self):
        invalidLogos = [
            'dog.png',
            'dog.svg.png'
        ]

        for invalidLogo in invalidLogos:
            with patch("builtins.open", mock_open(read_data="<text")) as mock_file:
                member = Member()
                member.orgname = 'test'
                with self.assertRaises(ValueError,msg="Member.logo for test must be an svg file - '{logo}' provided".format(logo=invalidLogo)) as ctx:
                    member.logo = invalidLogo

                self.assertIsNone(member.logo)

    def testTwitterValid(self):
        validTwitters = [
            'dog',
            'https://twitter.com/dog',
            'http://twitter.com/dog',
            'https://www.twitter.com/dog',
            'http://twitter.com/dog'
        ]

        for validTwitter in validTwitters:
            member = Member()
            member.orgname = 'test'
            member.twitter = validTwitter
            self.assertEqual(member.twitter,'https://twitter.com/dog')

    def testSetTwitterNotValid(self):
        invalidTwitters = [
            'https://notwitter.com/dog',
            'http://facebook.com'
        ]

        for invalidTwitter in invalidTwitters:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError,msg="Member.twitter for test must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=invalidTwitter)) as ctx:
                member.twitter = invalidTwitter

            self.assertIsNone(member.twitter)

    def testSetTwitterNull(self):
        member = Member()
        member.orgname = 'test'
        member.twitter = None
        self.assertIsNone(member.twitter)

    def testToLandscapeItemAttributes(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict['name'],member.orgname)
        self.assertEqual(dict['homepage_url'],member.website)
        self.assertEqual(dict['crunchbase'],member.crunchbase)
        self.assertNotIn('membership',dict)
        self.assertIsNone(dict['logo'])
        self.assertIsNone(dict['item'])

    def testToLandscapeItemAttributesEmptyCrunchbase(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict['name'],member.orgname)
        self.assertEqual(dict['homepage_url'],member.website)
        self.assertEqual(dict['organization']['name'],member.orgname)
        self.assertIsNone(dict['logo'])
        self.assertIsNone(dict['item'])
        self.assertNotIn('crunchbase',dict)
    
    def testToLandscapeItemAttributesWithSuffix(self):
        member = Member()
        member.entrysuffix = ' (testme)'
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        dict = member.toLandscapeItemAttributes()

        self.assertEqual(dict['name'],member.orgname+" (testme)")
        self.assertEqual(dict['homepage_url'],member.website)
        self.assertEqual(dict['crunchbase'],member.crunchbase)
        self.assertIsNone(dict['logo'])
        self.assertIsNone(dict['item'])
        self.assertNotIn('membership',dict)

    def testIsValidLandscapeItem(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyCrunchbase(self):
        member = Member()
        member.orgname = 'test3'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'

        self.assertTrue(member.isValidLandscapeItem())
    
    def testIsValidLandscapeItemEmptyOrgname(self):
        member = Member()
        member.orgname = ''
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('orgname',member.invalidLandscapeItemAttributes())
    
    def testIsValidLandscapeItemEmptyWebsiteLogo(self):
        member = Member()
        member.orgname = 'foo'
        with self.assertRaises(ValueError):
            member.website = ''
        with self.assertRaises(ValueError):
            with patch("builtins.open", mock_open(read_data="data")) as mock_file:
                member.logo = ''
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())
        self.assertIn('logo',member.invalidLandscapeItemAttributes())
        self.assertIn('website',member.invalidLandscapeItemAttributes())

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            membertooverlay.overlay(member)

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'gold.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})

    def testOverlayOnlyKeys(self):
        membertooverlay = Member()
        membertooverlay.orgname = 'test'
        membertooverlay.homepage_url = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'silver.svg'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        membertooverlay.overlay(member,['website'])

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'silver.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertEqual(member.organization,{})

    def testOverlayItemThrowsException(self):
        membertooverlay = Member()
        membertooverlay.name = 'test2'
        membertooverlay.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        membertooverlay.organization = {'name':'foo'} 

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            membertooverlay.overlay(member)

    @responses.activate
    def testHostLogo(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tmpfilename = tempfile.NamedTemporaryFile(dir=tempdir,mode='w',delete=False,suffix='.svg')
            tmpfilename.write('this is a file')
            tmpfilename.close()

            member = Member()
            member.orgname = 'dog'
            member.logo = SVGLogo(name='dog')
            member.hostLogo(tempdir)
            self.assertTrue(os.path.exists(os.path.join(tempdir,'dog.svg')))

class TestMembers(unittest.TestCase):

    @patch("landscape_tools.members.Members.__abstractmethods__", set())
    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members()
        members.members.append(member)

        self.assertTrue(members.find(member.orgname,member.website))
        self.assertTrue(members.find('dog',member.website))
        self.assertTrue(members.find(member.orgname,'https://bar.com'))

    @patch("landscape_tools.members.Members.__abstractmethods__", set())
    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members()
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    @patch("landscape_tools.members.Members.__abstractmethods__", set())
    def testFindMultiple(self):
        members = Members()
        
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        members.members.append(member)
        
        self.assertEqual(len(members.find(member.orgname,member.website)),2)
    
    @patch("landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeCompanyEmptyOrg(self):
        members = Members(loadData=False)
        self.assertEqual(members.normalizeCompany(None),'')

    @patch("landscape_tools.members.Members.__abstractmethods__", set())
    def testNormalizeCompany(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members(loadData=False)
            self.assertEqual(members.normalizeCompany(company["name"]),company["normalized"])

class TestLFXMembers(unittest.TestCase):

    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = LFXMembers(loadData=False)
        members.members.append(member)

        self.assertTrue(members.find(member.orgname,member.website,member.membership))
        self.assertTrue(members.find('dog',member.website,member.membership))
        self.assertTrue(members.find(member.orgname,'https://bar.com',member.membership))

    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = LFXMembers(loadData=False)
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.orgname,member.website,'Silver'))

    @responses.activate
    def testLoadData(self):
        members = LFXMembers(loadData = False, project = 'tlf2')
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"https://yahoo.com","Website":"hitachi-systems.com"}]"""
            )
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="-1.99 -1.86 96.85 23.60"><title>Consensys AG logo</title><path fill="#121212" d="M27.5277.00058c-2.4923 0-3.9142 1.41132-3.9142 3.74775l.0006.00057c0 2.26319 1.4218 3.72353 3.8652 3.72353 2.2491 0 3.5615-1.15582 3.7805-2.99336h-1.7019c-.1584 1.04681-.8025 1.67951-2.0665 1.67951-1.3977 0-2.2244-.81495-2.2244-2.42179S26.0084 1.315 27.4914 1.315c1.2156 0 1.8476.6079 2.0175 1.66682h1.6898c-.2189-1.7764-1.3735-2.98124-3.671-2.98124z"/><path fill="#121212" fill-rule="evenodd" d="M35.6106 7.47243c2.3823 0 3.841-1.44823 3.841-3.76044 0-2.4091-1.5924-3.71141-3.841-3.71141-2.3822 0-3.841 1.35133-3.841 3.76043 0 2.40911 1.5924 3.71142 3.841 3.71142zm0-6.15801c1.313 0 2.1881.76651 2.1881 2.44602 0 1.63048-.8025 2.39699-2.1881 2.39699-1.3129 0-2.1881-.81553-2.1881-2.44602 0-1.63048.8026-2.39699 2.1881-2.39699z" clip-rule="evenodd"/><path fill="#121212" d="M41.9675.1217h-1.6287v7.22903h1.6287V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C47.3036.99778 46.3558 0 44.6782 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7019l.0006.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643 2.3338 0 3.3184-.96145 3.3184-2.25107 0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3888-.90031 1.6287-.90031 1.2398 0 1.6649.41353 1.7623 1.04623h1.6898C54.6214.95049 53.7336.00115 51.4246.00115c-2.3091 0-3.2453.98568-3.2453 2.2753 0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M55.5208 3.76044c0 2.11726 1.3129 3.71141 3.7684 3.71141 2.0544 0 3.3184-.97356 3.6831-2.45812h-1.6656c-.2431.71805-.863 1.1437-1.9691 1.1437-1.2278 0-2.0176-.71806-2.1634-2.00768h5.8465C63.0328 1.61837 61.9387 0 59.3013 0c-2.3708 0-3.7805 1.52148-3.7805 3.76044zm5.7859-.71806h-4.1083c.2069-1.15582.9604-1.76429 2.0908-1.76429 1.2882 0 1.9081.69326 2.0175 1.76429z" clip-rule="evenodd"/><path fill="#121212" d="M65.4513.1217h-1.6286v7.22903h1.6286V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C70.7874.99778 69.8397 0 68.162 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7018l.0005.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643s3.3184-.96145 3.3184-2.25107c0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C78.1053.95049 77.2175.00115 74.9084.00115s-3.2453.98568-3.2453 2.2753c0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892zm9.9542 3.99172L86.1513.12227h-1.7024l-2.0907 6.32757-2.176-6.32757h-1.7987l2.3702 6.43716h1.5682l-.401 1.22906H79.174v1.33865h3.9504zm4.704-3.99114h-1.7018l.0006.00057c.182 1.44823 1.264 2.33643 3.5978 2.33643 2.3339 0 3.3185-.96144 3.3185-2.25107 0-1.09468-.5226-1.84965-2.1029-2.0319l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C92.7635.95107 91.8757.00173 89.5666.00173s-3.2453.98567-3.2453 2.2753c0 1.13159.5957 1.81331 2.1881 1.99557l2.0907.24339c.6931.08536.8752.37719.8752.7665 0 .52312-.4742.91243-1.714.91243s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M19.856 10.0614V7.35062h-.0006l.0006-.00057V.12216H9.9277C4.44477.12216 0 4.57182 0 10.0608 0 15.5498 4.44534 20 9.92828 20c5.48292 0 9.92772-4.4497 9.92772-9.9386zM7.67162 5.09148L12.6355.12216v7.22846h7.2199L14.891 12.3222H7.67162V5.09148z" clip-rule="evenodd"/></svg>""")
        
        members.loadData()
        self.assertEqual(members.project,'tlf2')
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].website,"https://consensys.net/")
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)
    
    @responses.activate
    def testLoadDataMissingLogo(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":""},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertIsNone(members.members[0].website)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataMissingWebsite(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":""},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="-1.99 -1.86 96.85 23.60"><title>Consensys AG logo</title><path fill="#121212" d="M27.5277.00058c-2.4923 0-3.9142 1.41132-3.9142 3.74775l.0006.00057c0 2.26319 1.4218 3.72353 3.8652 3.72353 2.2491 0 3.5615-1.15582 3.7805-2.99336h-1.7019c-.1584 1.04681-.8025 1.67951-2.0665 1.67951-1.3977 0-2.2244-.81495-2.2244-2.42179S26.0084 1.315 27.4914 1.315c1.2156 0 1.8476.6079 2.0175 1.66682h1.6898c-.2189-1.7764-1.3735-2.98124-3.671-2.98124z"/><path fill="#121212" fill-rule="evenodd" d="M35.6106 7.47243c2.3823 0 3.841-1.44823 3.841-3.76044 0-2.4091-1.5924-3.71141-3.841-3.71141-2.3822 0-3.841 1.35133-3.841 3.76043 0 2.40911 1.5924 3.71142 3.841 3.71142zm0-6.15801c1.313 0 2.1881.76651 2.1881 2.44602 0 1.63048-.8025 2.39699-2.1881 2.39699-1.3129 0-2.1881-.81553-2.1881-2.44602 0-1.63048.8026-2.39699 2.1881-2.39699z" clip-rule="evenodd"/><path fill="#121212" d="M41.9675.1217h-1.6287v7.22903h1.6287V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C47.3036.99778 46.3558 0 44.6782 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7019l.0006.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643 2.3338 0 3.3184-.96145 3.3184-2.25107 0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3888-.90031 1.6287-.90031 1.2398 0 1.6649.41353 1.7623 1.04623h1.6898C54.6214.95049 53.7336.00115 51.4246.00115c-2.3091 0-3.2453.98568-3.2453 2.2753 0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M55.5208 3.76044c0 2.11726 1.3129 3.71141 3.7684 3.71141 2.0544 0 3.3184-.97356 3.6831-2.45812h-1.6656c-.2431.71805-.863 1.1437-1.9691 1.1437-1.2278 0-2.0176-.71806-2.1634-2.00768h5.8465C63.0328 1.61837 61.9387 0 59.3013 0c-2.3708 0-3.7805 1.52148-3.7805 3.76044zm5.7859-.71806h-4.1083c.2069-1.15582.9604-1.76429 2.0908-1.76429 1.2882 0 1.9081.69326 2.0175 1.76429z" clip-rule="evenodd"/><path fill="#121212" d="M65.4513.1217h-1.6286v7.22903h1.6286V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C70.7874.99778 69.8397 0 68.162 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7018l.0005.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643s3.3184-.96145 3.3184-2.25107c0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C78.1053.95049 77.2175.00115 74.9084.00115s-3.2453.98568-3.2453 2.2753c0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892zm9.9542 3.99172L86.1513.12227h-1.7024l-2.0907 6.32757-2.176-6.32757h-1.7987l2.3702 6.43716h1.5682l-.401 1.22906H79.174v1.33865h3.9504zm4.704-3.99114h-1.7018l.0006.00057c.182 1.44823 1.264 2.33643 3.5978 2.33643 2.3339 0 3.3185-.96144 3.3185-2.25107 0-1.09468-.5226-1.84965-2.1029-2.0319l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C92.7635.95107 91.8757.00173 89.5666.00173s-3.2453.98567-3.2453 2.2753c0 1.13159.5957 1.81331 2.1881 1.99557l2.0907.24339c.6931.08536.8752.37719.8752.7665 0 .52312-.4742.91243-1.714.91243s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M19.856 10.0614V7.35062h-.0006l.0006-.00057V.12216H9.9277C4.44477.12216 0 4.57182 0 10.0608 0 15.5498 4.44534 20 9.92828 20c5.48292 0 9.92772-4.4497 9.92772-9.9386zM7.67162 5.09148L12.6355.12216v7.22846h7.2199L14.891 12.3222H7.67162V5.09148z" clip-rule="evenodd"/></svg>""")

        members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertIsNone(members.members[0].website)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"hitachi_ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataDuplicates(self):
        members = LFXMembers(loadData = False)
        responses.add(
            url=members.endpointURL.format(members.project),
            method=responses.GET,
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="-1.99 -1.86 96.85 23.60"><title>Consensys AG logo</title><path fill="#121212" d="M27.5277.00058c-2.4923 0-3.9142 1.41132-3.9142 3.74775l.0006.00057c0 2.26319 1.4218 3.72353 3.8652 3.72353 2.2491 0 3.5615-1.15582 3.7805-2.99336h-1.7019c-.1584 1.04681-.8025 1.67951-2.0665 1.67951-1.3977 0-2.2244-.81495-2.2244-2.42179S26.0084 1.315 27.4914 1.315c1.2156 0 1.8476.6079 2.0175 1.66682h1.6898c-.2189-1.7764-1.3735-2.98124-3.671-2.98124z"/><path fill="#121212" fill-rule="evenodd" d="M35.6106 7.47243c2.3823 0 3.841-1.44823 3.841-3.76044 0-2.4091-1.5924-3.71141-3.841-3.71141-2.3822 0-3.841 1.35133-3.841 3.76043 0 2.40911 1.5924 3.71142 3.841 3.71142zm0-6.15801c1.313 0 2.1881.76651 2.1881 2.44602 0 1.63048-.8025 2.39699-2.1881 2.39699-1.3129 0-2.1881-.81553-2.1881-2.44602 0-1.63048.8026-2.39699 2.1881-2.39699z" clip-rule="evenodd"/><path fill="#121212" d="M41.9675.1217h-1.6287v7.22903h1.6287V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C47.3036.99778 46.3558 0 44.6782 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7019l.0006.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643 2.3338 0 3.3184-.96145 3.3184-2.25107 0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3888-.90031 1.6287-.90031 1.2398 0 1.6649.41353 1.7623 1.04623h1.6898C54.6214.95049 53.7336.00115 51.4246.00115c-2.3091 0-3.2453.98568-3.2453 2.2753 0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M55.5208 3.76044c0 2.11726 1.3129 3.71141 3.7684 3.71141 2.0544 0 3.3184-.97356 3.6831-2.45812h-1.6656c-.2431.71805-.863 1.1437-1.9691 1.1437-1.2278 0-2.0176-.71806-2.1634-2.00768h5.8465C63.0328 1.61837 61.9387 0 59.3013 0c-2.3708 0-3.7805 1.52148-3.7805 3.76044zm5.7859-.71806h-4.1083c.2069-1.15582.9604-1.76429 2.0908-1.76429 1.2882 0 1.9081.69326 2.0175 1.76429z" clip-rule="evenodd"/><path fill="#121212" d="M65.4513.1217h-1.6286v7.22903h1.6286V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C70.7874.99778 69.8397 0 68.162 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7018l.0005.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643s3.3184-.96145 3.3184-2.25107c0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C78.1053.95049 77.2175.00115 74.9084.00115s-3.2453.98568-3.2453 2.2753c0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892zm9.9542 3.99172L86.1513.12227h-1.7024l-2.0907 6.32757-2.176-6.32757h-1.7987l2.3702 6.43716h1.5682l-.401 1.22906H79.174v1.33865h3.9504zm4.704-3.99114h-1.7018l.0006.00057c.182 1.44823 1.264 2.33643 3.5978 2.33643 2.3339 0 3.3185-.96144 3.3185-2.25107 0-1.09468-.5226-1.84965-2.1029-2.0319l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C92.7635.95107 91.8757.00173 89.5666.00173s-3.2453.98567-3.2453 2.2753c0 1.13159.5957 1.81331 2.1881 1.99557l2.0907.24339c.6931.08536.8752.37719.8752.7665 0 .52312-.4742.91243-1.714.91243s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M19.856 10.0614V7.35062h-.0006l.0006-.00057V.12216H9.9277C4.44477.12216 0 4.57182 0 10.0608 0 15.5498 4.44534 20 9.92828 20c5.48292 0 9.92772-4.4497 9.92772-9.9386zM7.67162 5.09148L12.6355.12216v7.22846h7.2199L14.891 12.3222H7.67162V5.09148z" clip-rule="evenodd"/></svg>""")

        members.loadData()
        self.assertEqual(members.project,'tlf')
        self.assertEqual(len(members.members),2)


class TestLandscapeMembers(unittest.TestCase):

    @responses.activate
    def testLoadData(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/academy_of_motion_picture_arts_and_sciences.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/blender_foundation.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            members.loadData()
        self.assertEqual(members.members[0].orgname,"Academy of Motion Picture Arts and Sciences")
        self.assertEqual(members.members[1].orgname,"Blender Foundation")
    
    @responses.activate
    def testLoadDataSpecifyLandscapeYAML(self):
        members = LandscapeMembers(loadData = False, landscapeListYAML = 'https://dog.com')
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/academy_of_motion_picture_arts_and_sciences.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://raw.githubusercontent.com/AcademySoftwareFoundation/aswf-landscape/master/hosted_logos/blender_foundation.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            members.loadData()
        self.assertEqual(members.members[0].orgname,"Academy of Motion Picture Arts and Sciences")
        self.assertEqual(members.members[1].orgname,"Blender Foundation")
    
    @responses.activate
    def testLoadDataSkipLandscape(self):
        members = LandscapeMembers(loadData = False)
        members.skipLandscapes = ['aswf']
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        members.loadData()
        self.assertEqual(members.members,[])

    @responses.activate
    def testLoadDataInvalidYAML(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
  membership: ASWF Members
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://aswf.io
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        self.assertRaises(Exception,members.loadData())
    
    @responses.activate
    def testLoadDataBadLandscape(self):
        members = LandscapeMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.landscapeListYAML,
            body="""
landscapes:
  # name: how we name a landscape project, used on a build server for logs and settings
  # repo: a github repo for a specific landscape
  # netlify: full | skip - do we build it on a netlify build or not
  # hook: - id for a build hook, so it will be triggered after a master build
  - landscape:
    name: aswf
    repo: AcademySoftwareFoundation/aswf-landscape
    hook: 5d5c7ca6dc2c51cf02381f63
    required: true
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeSettingsYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
global:
"""
            )
        responses.add(
            method=responses.GET,
            url=members.landscapeLandscapeYAML.format(repo="AcademySoftwareFoundation/aswf-landscape"),
            body="""
landscape:
  - category:
    name: ASWF Members
    subcategories:
      - subcategory:
        name: Premier
        items:
          - item:
            name: Academy of Motion Picture Arts and Sciences
            homepage_url: https://oscars.org/
            logo: academy_of_motion_picture_arts_and_sciences.svg
            twitter: https://twitter.com/TheAcademy
            crunchbase: https://www.crunchbase.com/organization/the-academy-of-motion-picture-arts-and-sciences
      - subcategory:
        name: Associate
        items:
          - item:
            name: Blender Foundation
            homepage_url: https://blender.org/
            logo: blender_foundation.svg
            twitter: https://twitter.com/Blender_Cloud
            crunchbase: https://www.crunchbase.com/organization/blender-org
"""
                )
        members.loadData()
        self.assertEqual(len(members.members),0)

    def testNormalizeLogo(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            'https://raw.githubusercontent.com/dog/cat/master/hosted_logos/mouse.svg',
            members.normalizeLogo('mouse.svg','dog/cat')
        )

    def testNormalizeLogoIsEmpty(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            '',
            members.normalizeLogo('','dog/cat')
        )
        self.assertEqual(
            '',
            members.normalizeLogo(None,'dog/cat')
        )

    def testNormalizeLogoIsURL(self):
        members = LandscapeMembers(loadData = False)
        self.assertEqual(
            'https://foo.com/mouse.svg',
            members.normalizeLogo('https://foo.com/mouse.svg','dog/cat')
        )

class TestLandscapeOutput(unittest.TestCase):

    def testNewLandscape(self):
        config = Config()
        config.landscapeMembersCategory = 'test me'
        config.landscapeMembersSubcategories = [
            {"name": "Good Membership", "category": "Good"},
            {"name": "Bad Membership", "category": "Bad"}
            ]

        landscape = LandscapeOutput(config=config, newLandscape=True)

        self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
        self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
        self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][1]['name'],"Bad")

    def testLoadLandscape(self):
        testlandscape = """
landscape:
- category:
  name: test me
  subcategories:
  - subcategory:
    name: Good
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://here.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['items'][0]['name'],"HERE Global B.V.")
            self.assertEqual(landscape.landscapeItems[0]['name'],"Good")

    def testLoadLandscapeReset(self):
        testlandscape = """
landscape:
- category:
  name: test me
  subcategories:
  - subcategory:
    name: Good
    items:
    - item:
      crunchbase: https://www.crunchbase.com/organization/here-technologies
      homepage_url: https://here.com/
      logo: https://raw.githubusercontent.com/ucfoundation/ucf-landscape/master/hosted_logos/here.svg
      name: HERE Global B.V.
      twitter: https://twitter.com/here
"""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config, resetCategory=True)
            
            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(len(landscape.landscape['landscape'][0]['subcategories'][0]['items']),0)
            self.assertEqual(landscape.landscapeItems[0]['name'],"Good")

    def testLoadLandscapeEmpty(self):
        testlandscape = ""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            config = Config()
            config.landscapeMembersCategory = 'test me'
            config.landscapeMembersSubcategories = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            config.landscapefile = tmpfilename.name

            landscape = LandscapeOutput(config=config)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][1]['name'],"Bad")

class TestSVGLogo(unittest.TestCase):
    def testPassInContents(self):
        self.assertEqual(str(SVGLogo(contents="This is a test")),"This is a test")

    def testCreateTextLogo(self):
        self.maxDiff = None
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>',str(SVGLogo(name="This is a test")))

    @responses.activate
    def testHostLogo(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='this is image data'
            )

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"this is image data")

    @responses.activate
    def testHostLogoFileNameUnicode(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='this is image data'
            )

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('privée')),'privee.svg')
    
    @responses.activate
    def testHostLogoNonASCII(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg").filename('北京数悦铭金技术有限公司')),'bei_jing_shu_yue_ming_jin_ji_zhu_you_xian_gong_si.svg')
        
    def testHostLogoContainsPNG(self):
        self.assertFalse(SVGLogo(contents="this is image data data:image/png;base64 dfdfdf").isValid())

    @responses.activate
    def testHostLogoContainsText(self):
        self.assertFalse(SVGLogo(contents="this is image data <text /> dfdfdf").isValid())
    
    @responses.activate(registry=OrderedRegistry)
    def testHostLogoRetriesOnChunkedEncodingErrorException(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=requests.exceptions.ChunkedEncodingError("Connection broken: IncompleteRead(55849 bytes read, 19919 more expected)")
        )
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"this is image data")

    def testHostLogoLogoisNone(self):
        self.assertEqual(str(SVGLogo()),'')
    
    @responses.activate
    def testHostLogo404(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='{"error": "not found"}', status=404,
        )

        self.assertEqual(str(SVGLogo(url="https://someurl.com/boom.svg")),"")

    @responses.activate
    def testSaveLogo(self):
        with tempfile.TemporaryDirectory() as tempdir:
            self.assertEqual(SVGLogo(contents="this is a file").save('dog',tempdir),'dog.svg')
    
    @responses.activate
    def testAutocropLogo(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": True, "result": "this is a file"})
        )

        logo = SVGLogo(contents="this is a dog")
        logo.autocrop()
        self.assertEqual(str(logo),'this is a file')

    @responses.activate
    def testAutocropLogoFail(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": False, "error": "this is a file"})
        )

        with self.assertRaises(RuntimeError) as cm:
            logo = SVGLogo(contents="this is a dog")
            logo.autocrop()
        
        self.assertEqual(str(cm.exception),'Autocrop failed: this is a file')
    
    @responses.activate
    def testCaptionLogo(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": True, "result": "this is a file"})
        )

        logo = SVGLogo(contents="this is a dog")
        logo.addCaption("Dog")
        self.assertEqual(str(logo),'this is a file')

    @responses.activate
    def testCaptionLogoFail(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": False, "error": "this is a file"})
        )

        with self.assertRaises(RuntimeError) as cm:
            logo = SVGLogo(contents="this is a dog")
            logo.addCaption("Dog")
        
        self.assertEqual(str(cm.exception),'Adding caption failed: this is a file')

class TestLFXProjects(unittest.TestCase):
        
    def testFindBySlug(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.slug = 'aswf'

        members = LFXProjects(loadData=False)
        members.members.append(member)

        self.assertEqual(members.findBySlug(member.slug).orgname,'test')
        self.assertTrue(members.find(member.orgname,'https://bar.com',repo_url=member.repo_url))
    
    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"

        members = LFXProjects(loadData=False)
        members.members.append(member)

        self.assertTrue(members.find(member.orgname,member.website))
        self.assertTrue(members.find(member.orgname,member.website,member.membership))
        self.assertTrue(members.find('dog',member.website,member.membership))
        self.assertTrue(members.find(member.orgname,'https://bar.com',member.membership))
        self.assertTrue(members.find(member.orgname,'https://bar.com',repo_url=member.repo_url))

    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        with patch("builtins.open", mock_open(read_data="data")) as mock_file:
            member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'
        member.repo_url = "https://github.com/foo/bar"

        members = LFXProjects(loadData=False)
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.orgname,member.website,'Silver'))
        self.assertFalse(members.find('dog','https://bar.com',repo_url='https://github.com/bar/foo'))
    
    @responses.activate
    def testLoadData(self):
        members = LFXProjects(project='aswf',loadData=False)
       
        responses.add(
            method=responses.GET,
            url=members.singleSlugEndpointURL.format('aswfs'),
            json={
              "Data": [ ],
              "Metadata": {
                "Offset": 0,
                "PageSize": 100,
                "TotalSize": 0
              }
            })
        responses.add(
            method=responses.GET,
            url=members.singleSlugEndpointURL.format(members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Model": [
                            "Membership"
                        ],
                        "Name": "Academy Software Foundation (ASWF)",
                        "ProjectID": "a09410000182dD2AAI",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/aswf.svg",
                        "ProjectType": "Project Group",
                        "RepositoryURL": "https://github.com/academysoftwarefoundation",
                        "Slug": "aswf",
                        "StartDate": "2018-08-10",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Website": "https://www.aswf.io/"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 1
                }
            })
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenTimelineIO (OTIO) is an API and interchange format for editorial cut information. You can think of it as a modern Edit Decision List (EDL) that also includes an API for reading, writing, and manipulating editorial data. It also includes a plugin system for translating to/from existing editorial formats as well as a plugin system for linking to proprietary media storage schemas.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenTimelineIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswfs",
                        "ProjectID": "a092M00001If9uZQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/PixarAnimationStudios/OpenTimelineIO",
                        "Slug": "open-timeline-io",
                        "StartDate": "2021-03-08",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": False,
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The goal of the OpenEXR project is to keep the format reliable and modern and to maintain its place as the preferred image format for entertainment content creation.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenEXR",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001If9ujQAB",
                        "ProjectType": "Project",
                        "Slug": "openexr",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": False,
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The mission of the Project is to develop an open-source interoperability standard for tools and content management systems used in media production.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "",
                        "Name": "OpenAssetIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ProjectID": "a092M00001L17vCQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/OpenAssetIO",
                        "Slug": "openassetio",
                        "StartDate": "2022-11-01",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Twitter": "https://yahoo.com",
                        "Website": "openassetio.org"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "The mission of the Project is to develop an open-source interoperability standard for tools and content management systems used in media production.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "",
                        "Name": "OpenAssetIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ProjectID": "a092M00001L17vCQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/OpenAssetIO",
                        "Slug": "openassetio",
                        "StartDate": "2022-11-01",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Website": "openassetio.org"
                    },
                    {
                        "AutoJoinEnabled": True,
                        "Description": "The mission of the Academy Software Foundation (ASWF) is to increase the quality and quantity of contributions to the content creation industry’s open source software base; to provide a neutral forum to coordinate cross-project efforts; to provide a common build and test infrastructure; and to provide individuals and organizations a clear path to participation in advancing our open source ecosystem.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": True,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Model": [
                            "Membership"
                        ],
                        "Name": "Academy Software Foundation (ASWF)",
                        "ProjectID": "a09410000182dD2AAI",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/aswf.svg",
                        "ProjectType": "Project Group",
                        "RepositoryURL": "https://github.com/academysoftwarefoundation",
                        "Slug": "aswf",
                        "StartDate": "2018-08-10",
                        "Status": "Active",
                        "TechnologySector": "Visual Effects",
                        "TestRecord": False,
                        "Website": "https://www.aswf.io/"
                    }
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 3
                }
            })
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/openassetio.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="-1.99 -1.86 96.85 23.60"><title>Consensys AG logo</title><path fill="#121212" d="M27.5277.00058c-2.4923 0-3.9142 1.41132-3.9142 3.74775l.0006.00057c0 2.26319 1.4218 3.72353 3.8652 3.72353 2.2491 0 3.5615-1.15582 3.7805-2.99336h-1.7019c-.1584 1.04681-.8025 1.67951-2.0665 1.67951-1.3977 0-2.2244-.81495-2.2244-2.42179S26.0084 1.315 27.4914 1.315c1.2156 0 1.8476.6079 2.0175 1.66682h1.6898c-.2189-1.7764-1.3735-2.98124-3.671-2.98124z"/><path fill="#121212" fill-rule="evenodd" d="M35.6106 7.47243c2.3823 0 3.841-1.44823 3.841-3.76044 0-2.4091-1.5924-3.71141-3.841-3.71141-2.3822 0-3.841 1.35133-3.841 3.76043 0 2.40911 1.5924 3.71142 3.841 3.71142zm0-6.15801c1.313 0 2.1881.76651 2.1881 2.44602 0 1.63048-.8025 2.39699-2.1881 2.39699-1.3129 0-2.1881-.81553-2.1881-2.44602 0-1.63048.8026-2.39699 2.1881-2.39699z" clip-rule="evenodd"/><path fill="#121212" d="M41.9675.1217h-1.6287v7.22903h1.6287V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C47.3036.99778 46.3558 0 44.6782 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7019l.0006.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643 2.3338 0 3.3184-.96145 3.3184-2.25107 0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3888-.90031 1.6287-.90031 1.2398 0 1.6649.41353 1.7623 1.04623h1.6898C54.6214.95049 53.7336.00115 51.4246.00115c-2.3091 0-3.2453.98568-3.2453 2.2753 0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M55.5208 3.76044c0 2.11726 1.3129 3.71141 3.7684 3.71141 2.0544 0 3.3184-.97356 3.6831-2.45812h-1.6656c-.2431.71805-.863 1.1437-1.9691 1.1437-1.2278 0-2.0176-.71806-2.1634-2.00768h5.8465C63.0328 1.61837 61.9387 0 59.3013 0c-2.3708 0-3.7805 1.52148-3.7805 3.76044zm5.7859-.71806h-4.1083c.2069-1.15582.9604-1.76429 2.0908-1.76429 1.2882 0 1.9081.69326 2.0175 1.76429z" clip-rule="evenodd"/><path fill="#121212" d="M65.4513.1217h-1.6286v7.22903h1.6286V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C70.7874.99778 69.8397 0 68.162 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7018l.0005.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643s3.3184-.96145 3.3184-2.25107c0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C78.1053.95049 77.2175.00115 74.9084.00115s-3.2453.98568-3.2453 2.2753c0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892zm9.9542 3.99172L86.1513.12227h-1.7024l-2.0907 6.32757-2.176-6.32757h-1.7987l2.3702 6.43716h1.5682l-.401 1.22906H79.174v1.33865h3.9504zm4.704-3.99114h-1.7018l.0006.00057c.182 1.44823 1.264 2.33643 3.5978 2.33643 2.3339 0 3.3185-.96144 3.3185-2.25107 0-1.09468-.5226-1.84965-2.1029-2.0319l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C92.7635.95107 91.8757.00173 89.5666.00173s-3.2453.98567-3.2453 2.2753c0 1.13159.5957 1.81331 2.1881 1.99557l2.0907.24339c.6931.08536.8752.37719.8752.7665 0 .52312-.4742.91243-1.714.91243s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M19.856 10.0614V7.35062h-.0006l.0006-.00057V.12216H9.9277C4.44477.12216 0 4.57182 0 10.0608 0 15.5498 4.44534 20 9.92828 20c5.48292 0 9.92772-4.4497 9.92772-9.9386zM7.67162 5.09148L12.6355.12216v7.22846h7.2199L14.891 12.3222H7.67162V5.09148z" clip-rule="evenodd"/></svg>""")
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO",
            json={
                "login": "OpenAssetIO",
                "id": 105730218,
                "node_id": "O_kgDOBk1Qqg",
                "url": "https://api.github.com/orgs/OpenAssetIO",
                "repos_url": "https://api.github.com/orgs/OpenAssetIO/repos",
                "events_url": "https://api.github.com/orgs/OpenAssetIO/events",
                "hooks_url": "https://api.github.com/orgs/OpenAssetIO/hooks",
                "issues_url": "https://api.github.com/orgs/OpenAssetIO/issues",
                "members_url": "https://api.github.com/orgs/OpenAssetIO/members{/member}",
                "public_members_url": "https://api.github.com/orgs/OpenAssetIO/public_members{/member}",
                "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                "name": None,
                "company": None,
                "blog": None,
                "location": None,
                "email": None,
                "twitter_username": None,
                "is_verified": False,
                "has_organization_projects": True,
                "has_repository_projects": True,
                "public_repos": 11,
                "public_gists": 0,
                "followers": 44,
                "following": 0,
                "html_url": "https://github.com/OpenAssetIO",
                "created_at": "2022-05-17T14:16:16Z",
                "updated_at": "2022-05-17T15:29:44Z",
                "archived_at": None,
                "type": "Organization"
            })
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO/repos?per_page=1",
            json=[
                {
                    "id": 399068104,
                    "node_id": "MDEwOlJlcG9zaXRvcnkzOTkwNjgxMDQ=",
                    "name": "OpenAssetIO",
                    "full_name": "OpenAssetIO/OpenAssetIO",
                    "private": False,
                    "owner": {
                        "login": "OpenAssetIO",
                        "id": 105730218,
                        "node_id": "O_kgDOBk1Qqg",
                        "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/OpenAssetIO",
                        "html_url": "https://github.com/OpenAssetIO",
                        "followers_url": "https://api.github.com/users/OpenAssetIO/followers",
                        "following_url": "https://api.github.com/users/OpenAssetIO/following{/other_user}",
                        "gists_url": "https://api.github.com/users/OpenAssetIO/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/OpenAssetIO/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/OpenAssetIO/subscriptions",
                        "organizations_url": "https://api.github.com/users/OpenAssetIO/orgs",
                        "repos_url": "https://api.github.com/users/OpenAssetIO/repos",
                        "events_url": "https://api.github.com/users/OpenAssetIO/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/OpenAssetIO/received_events",
                        "type": "Organization",
                        "site_admin": False
                    },
                    "html_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                    "fork": False,
                    "url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO",
                    "forks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/forks",
                    "keys_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/teams",
                    "hooks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/hooks",
                    "issue_events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/events",
                    "assignees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/tags",
                    "blobs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/languages",
                    "stargazers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/stargazers",
                    "contributors_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contributors",
                    "subscribers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscribers",
                    "subscription_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscription",
                    "commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/merges",
                    "archive_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/downloads",
                    "issues_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/labels{/name}",
                    "releases_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/deployments",
                    "created_at": "2021-08-23T10:54:50Z",
                    "updated_at": "2024-06-07T11:32:08Z",
                    "pushed_at": "2024-06-10T15:36:44Z",
                    "git_url": "git://github.com/OpenAssetIO/OpenAssetIO.git",
                    "ssh_url": "git@github.com:OpenAssetIO/OpenAssetIO.git",
                    "clone_url": "https://github.com/OpenAssetIO/OpenAssetIO.git",
                    "svn_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "homepage": "",
                    "size": 14943,
                    "stargazers_count": 268,
                    "watchers_count": 268,
                    "language": "C++",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": True,
                    "has_discussions": True,
                    "forks_count": 28,
                    "mirror_url": None,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 153,
                    "license": {
                        "key": "apache-2.0",
                        "name": "Apache License 2.0",
                        "spdx_id": "Apache-2.0",
                        "url": "https://api.github.com/licenses/apache-2.0",
                        "node_id": "MDc6TGljZW5zZTI="
                    },
                    "allow_forking": True,
                    "is_template": False,
                    "web_commit_signoff_required": True,
                    "topics": [
                        "asset-pipeline",
                        "assetmanager",
                        "cg",
                        "openassetio",
                        "vfx",
                        "vfx-pipeline"
                    ],
                    "visibility": "public",
                    "forks": 28,
                    "open_issues": 153,
                    "watchers": 268,
                    "default_branch": "main",
                    "permissions": {
                        "admin": False,
                        "maintain": False,
                        "push": False,
                        "triage": False,
                        "pull": True
                    }
                }
            ]
        )
        responses.add(
            method=responses.GET,
            url="https://api.github.com:443/orgs/OpenAssetIO/repos?per_page=1000",
            json=[
                {
                    "id": 399068104,
                    "node_id": "MDEwOlJlcG9zaXRvcnkzOTkwNjgxMDQ=",
                    "name": "OpenAssetIO",
                    "full_name": "OpenAssetIO/OpenAssetIO",
                    "private": False,
                    "owner": {
                        "login": "OpenAssetIO",
                        "id": 105730218,
                        "node_id": "O_kgDOBk1Qqg",
                        "avatar_url": "https://avatars.githubusercontent.com/u/105730218?v=4",
                        "gravatar_id": "",
                        "url": "https://api.github.com/users/OpenAssetIO",
                        "html_url": "https://github.com/OpenAssetIO",
                        "followers_url": "https://api.github.com/users/OpenAssetIO/followers",
                        "following_url": "https://api.github.com/users/OpenAssetIO/following{/other_user}",
                        "gists_url": "https://api.github.com/users/OpenAssetIO/gists{/gist_id}",
                        "starred_url": "https://api.github.com/users/OpenAssetIO/starred{/owner}{/repo}",
                        "subscriptions_url": "https://api.github.com/users/OpenAssetIO/subscriptions",
                        "organizations_url": "https://api.github.com/users/OpenAssetIO/orgs",
                        "repos_url": "https://api.github.com/users/OpenAssetIO/repos",
                        "events_url": "https://api.github.com/users/OpenAssetIO/events{/privacy}",
                        "received_events_url": "https://api.github.com/users/OpenAssetIO/received_events",
                        "type": "Organization",
                        "site_admin": False
                    },
                    "html_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "description": "An open-source interoperability standard for tools and content management systems used in media production.",
                    "fork": False,
                    "url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO",
                    "forks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/forks",
                    "keys_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/keys{/key_id}",
                    "collaborators_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/collaborators{/collaborator}",
                    "teams_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/teams",
                    "hooks_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/hooks",
                    "issue_events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/events{/number}",
                    "events_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/events",
                    "assignees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/assignees{/user}",
                    "branches_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/branches{/branch}",
                    "tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/tags",
                    "blobs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/blobs{/sha}",
                    "git_tags_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/tags{/sha}",
                    "git_refs_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/refs{/sha}",
                    "trees_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/trees{/sha}",
                    "statuses_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/statuses/{sha}",
                    "languages_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/languages",
                    "stargazers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/stargazers",
                    "contributors_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contributors",
                    "subscribers_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscribers",
                    "subscription_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/subscription",
                    "commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/commits{/sha}",
                    "git_commits_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/git/commits{/sha}",
                    "comments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/comments{/number}",
                    "issue_comment_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues/comments{/number}",
                    "contents_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/contents/{+path}",
                    "compare_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/compare/{base}...{head}",
                    "merges_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/merges",
                    "archive_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/{archive_format}{/ref}",
                    "downloads_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/downloads",
                    "issues_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/issues{/number}",
                    "pulls_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/pulls{/number}",
                    "milestones_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/milestones{/number}",
                    "notifications_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/notifications{?since,all,participating}",
                    "labels_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/labels{/name}",
                    "releases_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/releases{/id}",
                    "deployments_url": "https://api.github.com/repos/OpenAssetIO/OpenAssetIO/deployments",
                    "created_at": "2021-08-23T10:54:50Z",
                    "updated_at": "2024-06-07T11:32:08Z",
                    "pushed_at": "2024-06-10T15:36:44Z",
                    "git_url": "git://github.com/OpenAssetIO/OpenAssetIO.git",
                    "ssh_url": "git@github.com:OpenAssetIO/OpenAssetIO.git",
                    "clone_url": "https://github.com/OpenAssetIO/OpenAssetIO.git",
                    "svn_url": "https://github.com/OpenAssetIO/OpenAssetIO",
                    "homepage": "",
                    "size": 14943,
                    "stargazers_count": 268,
                    "watchers_count": 268,
                    "language": "C++",
                    "has_issues": True,
                    "has_projects": True,
                    "has_downloads": True,
                    "has_wiki": True,
                    "has_pages": True,
                    "has_discussions": True,
                    "forks_count": 28,
                    "mirror_url": None,
                    "archived": False,
                    "disabled": False,
                    "open_issues_count": 153,
                    "license": {
                        "key": "apache-2.0",
                        "name": "Apache License 2.0",
                        "spdx_id": "Apache-2.0",
                        "url": "https://api.github.com/licenses/apache-2.0",
                        "node_id": "MDc6TGljZW5zZTI="
                    },
                    "allow_forking": True,
                    "is_template": False,
                    "web_commit_signoff_required": True,
                    "topics": [
                        "asset-pipeline",
                        "assetmanager",
                        "cg",
                        "openassetio",
                        "vfx",
                        "vfx-pipeline"
                    ],
                    "visibility": "public",
                    "forks": 28,
                    "open_issues": 153,
                    "watchers": 268,
                    "default_branch": "main",
                    "permissions": {
                        "admin": False,
                        "maintain": False,
                        "push": False,
                        "triage": False,
                        "pull": True
                    }
                }
            ]
        )
          
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.members[0].orgname,"OpenCue")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/linux-foundation")
        self.assertEqual(members.members[0].logo,"opencue.svg")
        self.assertEqual(members.members[0].membership,"All")
        self.assertEqual(members.members[0].website,"https://opencue.io/")
        self.assertIsNone(members.members[0].twitter)
        self.assertIn("Project Group / Academy Software Foundation (ASWF)",members.members[0].second_path)
        self.assertEqual(members.members[1].orgname,"OpenTimelineIO")
        self.assertEqual(members.members[1].crunchbase,"https://www.crunchbase.com/organization/linux-foundation")
        self.assertEqual(members.members[1].logo,"opentimelineio.svg")
        self.assertEqual(members.members[1].membership,"All")
        self.assertEqual(members.members[1].repo_url,"https://github.com/PixarAnimationStudios/OpenTimelineIO")
        self.assertEqual(members.members[1].website,"https://github.com/PixarAnimationStudios/OpenTimelineIO")
        self.assertIsNone(members.members[1].twitter)
        self.assertIn("PMO Managed / All", members.members[1].second_path)
        self.assertNotIn("Project Group / Academy Software Foundation (ASWF)",members.members[1].second_path)
        self.assertIsNone(members.members[2].website)
        self.assertIsNone(members.members[2].repo_url)
        self.assertEqual(members.members[2].logo,"openexr.svg")
        self.assertEqual(members.members[3].repo_url,"https://github.com/OpenAssetIO/OpenAssetIO")
        self.assertEqual(members.members[3].parent_slug,members.project)
        self.assertIsNone(members.members[3].twitter)
        self.assertEqual(len(members.members),4)

    @responses.activate
    def testLoadDataSkippedRecords(self):
        members = LFXProjects(project='aswf',loadData=False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            json={
                "Data": [
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "DisplayOnWebsite": False,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Active",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenCue is an open source render management system. You can use OpenCue in visual effects and animation production to break down complex jobs into individual tasks. You can submit jobs to a configurable dispatch queue that allocates the necessary computational resources.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenCue",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001IV3znQAD",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/opencue.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/AcademySoftwareFoundation/OpenCue",
                        "Slug": "opencue",
                        "StartDate": "2020-04-24",
                        "Status": "Formation - Exploratory",
                        "TechnologySector": "DevOps, CI/CD & Site Reliability;Web & Application Development;Visual Effects",
                        "TestRecord": False,
                        "Website": "https://opencue.io"
                    },
                    {
                        "AutoJoinEnabled": False,
                        "Description": "OpenTimelineIO (OTIO) is an API and interchange format for editorial cut information. You can think of it as a modern Edit Decision List (EDL) that also includes an API for reading, writing, and manipulating editorial data. It also includes a plugin system for translating to/from existing editorial formats as well as a plugin system for linking to proprietary media storage schemas.",
                        "DisplayOnWebsite": True,
                        "HasProgramManager": False,
                        "Industry": [
                            "Motion Pictures"
                        ],
                        "IndustrySector": "Motion Pictures",
                        "Name": "OpenTimelineIO",
                        "ParentID": "a09410000182dD2AAI",
                        "ParentSlug": "aswf",
                        "ProjectID": "a092M00001If9uZQAR",
                        "ProjectLogo": "https://lf-master-project-logos-prod.s3.us-east-2.amazonaws.com/open-timeline-io.svg",
                        "ProjectType": "Project",
                        "RepositoryURL": "https://github.com/PixarAnimationStudios/OpenTimelineIO",
                        "Slug": "open-timeline-io",
                        "StartDate": "2021-03-08",
                        "Status": "Active",
                        "TechnologySector": "Web & Application Development;Visual Effects",
                        "TestRecord": True,
                        "Website": "http://opentimeline.io/"
                    },
                ],
                "Metadata": {
                    "Offset": 0,
                    "PageSize": 100,
                    "TotalSize": 2
                }
            })
        
        with unittest.mock.patch('requests_cache.CachedSession', requests.Session):
            members.loadData()
        self.assertEqual(members.members,[])

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    
    unittest.main()
