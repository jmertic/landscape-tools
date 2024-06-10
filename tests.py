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
from landscape_tools.member import Member
from landscape_tools.members import Members
from landscape_tools.lfxmembers import LFXMembers
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.crunchbasemembers import CrunchbaseMembers
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
landscapeMemberCategory: ASWF Member Company
memberSuffix: " (help)"
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        config = Config(tmpfilename.name)

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
landscapefile: foo.yml
missingcsvfile: foo.csv
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        config = Config(tmpfilename.name)

        self.assertEqual(config.project,"a09410000182dD2AAI")
        self.assertEqual(config.landscapefile,"foo.yml")
        self.assertEqual(config.missingcsvfile,"foo.csv")

        os.unlink(tmpfilename.name)
    def testLoadConfigDefaults(self):
        testconfigfilecontents = """
project: a09410000182dD2AAI # Academy Software Foundation
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testconfigfilecontents)
        tmpfilename.close()

        config = Config(tmpfilename.name)

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

class TestMember(unittest.TestCase):

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

    def testSetCrunchbaseNotValid(self):
        invalidCrunchbaseURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidCrunchbaseURL in invalidCrunchbaseURLs:
            member = Member()
            member.orgname = 'test'
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
            self.assertTrue(member._validWebsite)

    def testSetWebsiteNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertRaises(ValueError,msg="Member.website must be not be blank for test") as ctx:
            member.website = ''

        self.assertFalse(member._validWebsite)

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

            self.assertFalse(member._validWebsite)

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
                self.assertTrue(member._validLogo)

    def testSetLogoNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertRaises(ValueError,msg="Member.logo must be not be blank for test") as ctx:
            member.logo = ''

        self.assertFalse(member._validLogo)

    def testSetLogoNotValid(self):
        invalidLogos = [
            'dog.png',
            'dog.svg.png'
        ]

        for invalidLogo in invalidLogos:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError,msg="Member.logo for test must be an svg file - '{logo}' provided".format(logo=invalidLogo)) as ctx:
                member.logo = invalidLogo

            self.assertFalse(member._validLogo)

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
            self.assertTrue(member._validTwitter)

    def testSetLogoNotValid(self):
        invalidTwitters = [
            'https://notwitter.com/dog',
            'http://facebook.com'
        ]

        for invalidTwitter in invalidTwitters:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError,msg="Member.twitter for test must be either a Twitter handle, or the URL to a twitter handle - '{twitter}' provided".format(twitter=invalidTwitter)) as ctx:
                member.twitter = invalidTwitter

            self.assertFalse(member._validTwitter)

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

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.orgname = 'test2'
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
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="21.88 16.88 864.24 167.74"><title>Hitachi, Ltd. logo</title><g fill="#231f20" fill-opacity="1" fill-rule="nonzero" stroke="none" transform="matrix(1.33333 0 0 -1.33333 0 204.84) scale(.1)"><path d="M5301.18 1258.82V875.188h513.3c0-1.372-.43 383.632 0 383.632h254.16s.9-958.422 0-959.461h-254.16V721.57c0-1.25-513.3 0-513.3 0 .45-1.621 0-422.461 0-422.211h-254.12s1.6 959.461 0 959.461h254.12"/><path d="M2889.38 1258.82v-163.28h-388.51V299.359h-254.16v796.181h-388.48s.52 163.16 0 163.28c.52-.12 1031.15 0 1031.15 0"/><path d="M3877.23 299.359h-282.89c.42 0-83.32 206.289-83.32 206.289h-476.2s-81.72-206.519-83.17-206.289c.19-.23-282.82 0-282.82 0l448.28 959.461c0-.64 311.7 0 311.7 0zm-604.28 796.181l-176.76-436.216h353.76l-177 436.216"/><path d="M6269.85 299.359h254.3v959.461h-254.3V299.359"/><path d="M544.422 1258.82s-.137-386.449 0-383.632h512.968c0-1.372-.15 383.632 0 383.632h254.32s.63-958.422 0-959.461h-254.32V721.57c0-1.25-512.968 0-512.968 0 .109-1.621-.137-422.461 0-422.211H290.223s1.425 959.461 0 959.461h254.199"/><path d="M1513.27 299.359h253.93v959.461h-253.93V299.359"/><path d="M3868.11 565.32c-22.26 64.336-34.24 132.27-34.24 204.239 0 100.742 17.93 198.476 66.25 279.391 49.59 83.52 125.86 148.17 218.05 182.62 87.95 32.89 182.36 51.07 281.6 51.07 114.14 0 222.29-25.05 320.69-67.71 91.64-39.25 160.88-122.01 181.25-221.735 4.08-19.652 7.42-40.097 9.12-60.55h-266.68c-1.04 25.375-5.18 50.898-13.97 73.845-20.09 53.07-64.22 94.21-119.1 110.87-35.29 10.84-72.58 16.58-111.31 16.58-44.24 0-86.58-7.8-125.8-21.74-65.04-22.77-115.88-75.55-138.65-140.63-22.25-63.203-35-131.304-35-202.011 0-58.438 9.51-114.922 24.51-168.438 19.12-70.019 71.62-126.051 138.62-151.461 42.57-15.941 88.26-25.469 136.32-25.469 41.02 0 80.35 6.289 117.6 18.297 49.57 15.703 90.02 52.481 111.06 99.551 14.02 31.469 20.87 66.27 20.87 103.051H4917c-1.52-31.117-5.8-62.133-12.83-91.098-22.83-94.863-89.32-174.371-177.68-211.621-100.54-42.242-210.54-66.699-326.72-66.699-89.92 0-176.48 14.219-257.73 39.668-123.97 39.199-231.31 128.398-273.93 249.98"/></g></svg>""")
        responses.add(
            method=responses.GET,
            url="https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg",
            body="""<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="-1.99 -1.86 96.85 23.60"><title>Consensys AG logo</title><path fill="#121212" d="M27.5277.00058c-2.4923 0-3.9142 1.41132-3.9142 3.74775l.0006.00057c0 2.26319 1.4218 3.72353 3.8652 3.72353 2.2491 0 3.5615-1.15582 3.7805-2.99336h-1.7019c-.1584 1.04681-.8025 1.67951-2.0665 1.67951-1.3977 0-2.2244-.81495-2.2244-2.42179S26.0084 1.315 27.4914 1.315c1.2156 0 1.8476.6079 2.0175 1.66682h1.6898c-.2189-1.7764-1.3735-2.98124-3.671-2.98124z"/><path fill="#121212" fill-rule="evenodd" d="M35.6106 7.47243c2.3823 0 3.841-1.44823 3.841-3.76044 0-2.4091-1.5924-3.71141-3.841-3.71141-2.3822 0-3.841 1.35133-3.841 3.76043 0 2.40911 1.5924 3.71142 3.841 3.71142zm0-6.15801c1.313 0 2.1881.76651 2.1881 2.44602 0 1.63048-.8025 2.39699-2.1881 2.39699-1.3129 0-2.1881-.81553-2.1881-2.44602 0-1.63048.8026-2.39699 2.1881-2.39699z" clip-rule="evenodd"/><path fill="#121212" d="M41.9675.1217h-1.6287v7.22903h1.6287V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C47.3036.99778 46.3558 0 44.6782 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7019l.0006.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643 2.3338 0 3.3184-.96145 3.3184-2.25107 0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3888-.90031 1.6287-.90031 1.2398 0 1.6649.41353 1.7623 1.04623h1.6898C54.6214.95049 53.7336.00115 51.4246.00115c-2.3091 0-3.2453.98568-3.2453 2.2753 0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M55.5208 3.76044c0 2.11726 1.3129 3.71141 3.7684 3.71141 2.0544 0 3.3184-.97356 3.6831-2.45812h-1.6656c-.2431.71805-.863 1.1437-1.9691 1.1437-1.2278 0-2.0176-.71806-2.1634-2.00768h5.8465C63.0328 1.61837 61.9387 0 59.3013 0c-2.3708 0-3.7805 1.52148-3.7805 3.76044zm5.7859-.71806h-4.1083c.2069-1.15582.9604-1.76429 2.0908-1.76429 1.2882 0 1.9081.69326 2.0175 1.76429z" clip-rule="evenodd"/><path fill="#121212" d="M65.4513.1217h-1.6286v7.22903h1.6286V2.44659c.4258-.81553 1.0088-1.19273 1.945-1.19273 1.1667 0 1.7624.53581 1.7624 1.70374v4.39256h1.6287V2.72574C70.7874.99778 69.8397 0 68.162 0c-1.4829 0-2.2976.76708-2.7107 2.04459V.12169zm7.7189 5.01372h-1.7018l.0005.00058c.1821 1.44823 1.264 2.33643 3.5979 2.33643s3.3184-.96145 3.3184-2.25107c0-1.09468-.5225-1.84965-2.1028-2.03191l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C78.1053.95049 77.2175.00115 74.9084.00115s-3.2453.98568-3.2453 2.2753c0 1.13159.5957 1.81332 2.1881 1.99557l2.0907.24339c.6931.08536.8751.3772.8751.76651 0 .52311-.4741.91242-1.7139.91242s-1.7992-.34086-1.9329-1.05892zm9.9542 3.99172L86.1513.12227h-1.7024l-2.0907 6.32757-2.176-6.32757h-1.7987l2.3702 6.43716h1.5682l-.401 1.22906H79.174v1.33865h3.9504zm4.704-3.99114h-1.7018l.0006.00057c.182 1.44823 1.264 2.33643 3.5978 2.33643 2.3339 0 3.3185-.96144 3.3185-2.25107 0-1.09468-.5226-1.84965-2.1029-2.0319l-2.176-.2555c-.6441-.07325-.8751-.32875-.8751-.7544 0-.511.3889-.90031 1.6287-.90031s1.665.41353 1.7623 1.04623h1.6898C92.7635.95107 91.8757.00173 89.5666.00173s-3.2453.98567-3.2453 2.2753c0 1.13159.5957 1.81331 2.1881 1.99557l2.0907.24339c.6931.08536.8752.37719.8752.7665 0 .52312-.4742.91243-1.714.91243s-1.7992-.34086-1.9329-1.05892z"/><path fill="#121212" fill-rule="evenodd" d="M19.856 10.0614V7.35062h-.0006l.0006-.00057V.12216H9.9277C4.44477.12216 0 4.57182 0 10.0608 0 15.5498 4.44534 20 9.92828 20c5.48292 0 9.92772-4.4497 9.92772-9.9386zM7.67162 5.09148L12.6355.12216v7.22846h7.2199L14.891 12.3222H7.67162V5.09148z" clip-rule="evenodd"/></svg>""")
        
        members = LFXMembers()
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

        members = LFXMembers()
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

        members = LFXMembers()
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
        config.landscapeCategory = 'test me'
        config.landscapeSubcategories = [
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
            config.landscapeCategory = 'test me'
            config.landscapeSubcategories = [
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
            config.landscapeCategory = 'test me'
            config.landscapeSubcategories = [
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
            config.landscapeCategory = 'test me'
            config.landscapeSubcategories = [
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
        self.assertEqual(str(SVGLogo(name="This is a test")),"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="560" height="320" viewBox="0 0 560 320">
<defs>
<g>
<g id="glyph-0-0">
<path d="M 15.554688 0 L 15.554688 -37.882812 L 1.40625 -37.882812 L 1.40625 -42.949219 L 35.449219 -42.949219 L 35.449219 -37.882812 L 21.242188 -37.882812 L 21.242188 0 Z M 15.554688 0 "/>
</g>
<g id="glyph-0-1">
<path d="M 3.953125 0 L 3.953125 -42.949219 L 9.226562 -42.949219 L 9.226562 -27.539062 C 11.6875 -30.390625 14.796875 -31.816406 18.546875 -31.816406 C 20.851562 -31.816406 22.851562 -31.363281 24.550781 -30.453125 C 26.25 -29.546875 27.464844 -28.289062 28.199219 -26.6875 C 28.929688 -25.085938 29.296875 -22.765625 29.296875 -19.71875 L 29.296875 0 L 24.023438 0 L 24.023438 -19.71875 C 24.023438 -22.355469 23.453125 -24.273438 22.308594 -25.472656 C 21.167969 -26.675781 19.550781 -27.273438 17.460938 -27.273438 C 15.898438 -27.273438 14.429688 -26.871094 13.050781 -26.058594 C 11.675781 -25.25 10.695312 -24.148438 10.109375 -22.765625 C 9.523438 -21.378906 9.226562 -19.460938 9.226562 -17.023438 L 9.226562 0 Z M 3.953125 0 "/>
</g>
<g id="glyph-0-2">
<path d="M 3.984375 -36.882812 L 3.984375 -42.949219 L 9.257812 -42.949219 L 9.257812 -36.882812 Z M 3.984375 0 L 3.984375 -31.113281 L 9.257812 -31.113281 L 9.257812 0 Z M 3.984375 0 "/>
</g>
<g id="glyph-0-3">
<path d="M 1.84375 -9.289062 L 7.0625 -10.109375 C 7.355469 -8.019531 8.167969 -6.414062 9.507812 -5.304688 C 10.84375 -4.191406 12.714844 -3.632812 15.117188 -3.632812 C 17.539062 -3.632812 19.335938 -4.125 20.507812 -5.113281 C 21.679688 -6.097656 22.265625 -7.257812 22.265625 -8.585938 C 22.265625 -9.777344 21.75 -10.710938 20.710938 -11.398438 C 19.988281 -11.867188 18.195312 -12.460938 15.320312 -13.183594 C 11.453125 -14.160156 8.773438 -15.003906 7.28125 -15.71875 C 5.785156 -16.429688 4.652344 -17.417969 3.882812 -18.675781 C 3.109375 -19.9375 2.726562 -21.328125 2.726562 -22.851562 C 2.726562 -24.238281 3.042969 -25.523438 3.675781 -26.703125 C 4.3125 -27.886719 5.175781 -28.867188 6.269531 -29.648438 C 7.089844 -30.253906 8.207031 -30.765625 9.625 -31.1875 C 11.039062 -31.605469 12.558594 -31.816406 14.179688 -31.816406 C 16.621094 -31.816406 18.765625 -31.464844 20.609375 -30.761719 C 22.457031 -30.058594 23.820312 -29.105469 24.695312 -27.90625 C 25.574219 -26.703125 26.179688 -25.097656 26.515625 -23.085938 L 21.359375 -22.382812 C 21.125 -23.984375 20.445312 -25.234375 19.320312 -26.132812 C 18.199219 -27.03125 16.609375 -27.480469 14.5625 -27.480469 C 12.140625 -27.480469 10.410156 -27.078125 9.375 -26.28125 C 8.339844 -25.480469 7.820312 -24.539062 7.820312 -23.46875 C 7.820312 -22.785156 8.039062 -22.167969 8.46875 -21.621094 C 8.898438 -21.054688 9.570312 -20.585938 10.488281 -20.214844 C 11.015625 -20.019531 12.570312 -19.570312 15.148438 -18.867188 C 18.878906 -17.871094 21.480469 -17.054688 22.953125 -16.421875 C 24.429688 -15.785156 25.585938 -14.863281 26.425781 -13.652344 C 27.265625 -12.441406 27.6875 -10.9375 27.6875 -9.140625 C 27.6875 -7.382812 27.171875 -5.726562 26.148438 -4.175781 C 25.121094 -2.621094 23.640625 -1.421875 21.710938 -0.570312 C 19.777344 0.277344 17.585938 0.703125 15.148438 0.703125 C 11.105469 0.703125 8.023438 -0.136719 5.902344 -1.816406 C 3.785156 -3.496094 2.429688 -5.984375 1.84375 -9.289062 Z M 1.84375 -9.289062 "/>
</g>
<g id="glyph-0-4">
<path d="M 24.257812 -3.835938 C 22.304688 -2.175781 20.425781 -1.007812 18.617188 -0.320312 C 16.8125 0.363281 14.875 0.703125 12.804688 0.703125 C 9.386719 0.703125 6.757812 -0.132812 4.921875 -1.800781 C 3.085938 -3.472656 2.167969 -5.605469 2.167969 -8.203125 C 2.167969 -9.726562 2.515625 -11.117188 3.207031 -12.378906 C 3.902344 -13.636719 4.808594 -14.648438 5.933594 -15.410156 C 7.054688 -16.171875 8.320312 -16.75 9.726562 -17.140625 C 10.761719 -17.414062 12.324219 -17.675781 14.414062 -17.929688 C 18.671875 -18.4375 21.804688 -19.042969 23.820312 -19.746094 C 23.839844 -20.46875 23.847656 -20.929688 23.847656 -21.125 C 23.847656 -23.273438 23.351562 -24.785156 22.351562 -25.664062 C 21.003906 -26.855469 19.003906 -27.453125 16.347656 -27.453125 C 13.867188 -27.453125 12.035156 -27.015625 10.855469 -26.148438 C 9.671875 -25.277344 8.796875 -23.742188 8.234375 -21.53125 L 3.078125 -22.234375 C 3.546875 -24.441406 4.316406 -26.226562 5.390625 -27.582031 C 6.464844 -28.941406 8.015625 -29.984375 10.046875 -30.71875 C 12.078125 -31.449219 14.433594 -31.816406 17.109375 -31.816406 C 19.765625 -31.816406 21.921875 -31.503906 23.585938 -30.878906 C 25.246094 -30.253906 26.464844 -29.46875 27.246094 -28.519531 C 28.027344 -27.574219 28.574219 -26.375 28.886719 -24.929688 C 29.0625 -24.03125 29.148438 -22.414062 29.148438 -20.070312 L 29.148438 -13.039062 C 29.148438 -8.136719 29.261719 -5.035156 29.488281 -3.734375 C 29.710938 -2.4375 30.15625 -1.191406 30.820312 0 L 25.3125 0 C 24.765625 -1.09375 24.414062 -2.375 24.257812 -3.835938 Z M 23.820312 -15.617188 C 21.90625 -14.835938 19.03125 -14.171875 15.203125 -13.625 C 13.035156 -13.3125 11.503906 -12.960938 10.605469 -12.570312 C 9.707031 -12.179688 9.015625 -11.605469 8.523438 -10.855469 C 8.035156 -10.101562 7.792969 -9.265625 7.792969 -8.351562 C 7.792969 -6.945312 8.324219 -5.773438 9.390625 -4.835938 C 10.453125 -3.898438 12.011719 -3.429688 14.0625 -3.429688 C 16.09375 -3.429688 17.898438 -3.871094 19.484375 -4.761719 C 21.066406 -5.648438 22.226562 -6.867188 22.96875 -8.40625 C 23.535156 -9.597656 23.820312 -11.359375 23.820312 -13.679688 Z M 23.820312 -15.617188 "/>
</g>
<g id="glyph-0-5">
<path d="M 15.46875 -4.71875 L 16.230469 -0.0585938 C 14.746094 0.253906 13.417969 0.410156 12.246094 0.410156 C 10.332031 0.410156 8.847656 0.109375 7.792969 -0.5 C 6.738281 -1.105469 5.996094 -1.898438 5.566406 -2.886719 C 5.136719 -3.871094 4.921875 -5.945312 4.921875 -9.109375 L 4.921875 -27.011719 L 1.054688 -27.011719 L 1.054688 -31.113281 L 4.921875 -31.113281 L 4.921875 -38.820312 L 10.164062 -41.984375 L 10.164062 -31.113281 L 15.46875 -31.113281 L 15.46875 -27.011719 L 10.164062 -27.011719 L 10.164062 -8.820312 C 10.164062 -7.316406 10.257812 -6.347656 10.445312 -5.917969 C 10.628906 -5.488281 10.933594 -5.148438 11.351562 -4.890625 C 11.773438 -4.636719 12.375 -4.511719 13.15625 -4.511719 C 13.742188 -4.511719 14.511719 -4.578125 15.46875 -4.71875 Z M 15.46875 -4.71875 "/>
</g>
<g id="glyph-0-6">
<path d="M 25.253906 -10.019531 L 30.703125 -9.34375 C 29.84375 -6.160156 28.25 -3.691406 25.929688 -1.933594 C 23.605469 -0.175781 20.632812 0.703125 17.023438 0.703125 C 12.472656 0.703125 8.863281 -0.699219 6.195312 -3.5 C 3.53125 -6.304688 2.195312 -10.234375 2.195312 -15.292969 C 2.195312 -20.527344 3.546875 -24.589844 6.242188 -27.480469 C 8.9375 -30.371094 12.429688 -31.816406 16.726562 -31.816406 C 20.886719 -31.816406 24.289062 -30.398438 26.921875 -27.570312 C 29.558594 -24.738281 30.878906 -20.75 30.878906 -15.617188 C 30.878906 -15.304688 30.867188 -14.835938 30.851562 -14.210938 L 7.648438 -14.210938 C 7.84375 -10.792969 8.808594 -8.171875 10.546875 -6.359375 C 12.285156 -4.542969 14.453125 -3.632812 17.050781 -3.632812 C 18.984375 -3.632812 20.632812 -4.140625 22 -5.15625 C 23.367188 -6.171875 24.453125 -7.792969 25.253906 -10.019531 Z M 7.9375 -18.546875 L 25.3125 -18.546875 C 25.078125 -21.164062 24.414062 -23.125 23.320312 -24.433594 C 21.640625 -26.464844 19.460938 -27.480469 16.789062 -27.480469 C 14.367188 -27.480469 12.328125 -26.671875 10.679688 -25.046875 C 9.027344 -23.425781 8.117188 -21.257812 7.9375 -18.546875 Z M 7.9375 -18.546875 "/>
</g>
</g>
</defs>
<g fill="rgb(0%, 0%, 0%)" fill-opacity="1">
<use xlink:href="#glyph-0-0" x="0" y="50"/>
<use xlink:href="#glyph-0-1" x="36.650391" y="50"/>
<use xlink:href="#glyph-0-2" x="70.019531" y="50"/>
<use xlink:href="#glyph-0-3" x="83.349609" y="50"/>
</g>
<g fill="rgb(0%, 0%, 0%)" fill-opacity="1">
<use xlink:href="#glyph-0-2" x="0" y="120"/>
<use xlink:href="#glyph-0-3" x="13.330078" y="120"/>
</g>
<g fill="rgb(0%, 0%, 0%)" fill-opacity="1">
<use xlink:href="#glyph-0-4" x="0" y="180"/>
</g>
<g fill="rgb(0%, 0%, 0%)" fill-opacity="1">
<use xlink:href="#glyph-0-5" x="0" y="240"/>
<use xlink:href="#glyph-0-6" x="16.669922" y="240"/>
<use xlink:href="#glyph-0-3" x="50.039062" y="240"/>
<use xlink:href="#glyph-0-5" x="80.039062" y="240"/>
</g>
</svg>
""")

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
            tmpfilename = tempfile.NamedTemporaryFile(dir=tempdir,mode='w',delete=False,suffix='.svg')
            tmpfilename.write('')
            tmpfilename.close()

            self.assertEqual(SVGLogo(contents="this is a file").save('dog',tempdir),'dog.svg')
    
    @responses.activate
    def testSaveLogo(self):
        responses.add(
            method=responses.POST,
            url='https://autocrop.cncf.io/autocrop',
            body=json.dumps({"success": "true", "result": "this is a file"})
        )

        logo = SVGLogo(contents="this is a dog")
        logo.autocrop()
        self.assertEqual(str(logo),'this is a file')

'''
    def testRemoveHostedLogo(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tmpfilename = tempfile.NamedTemporaryFile(dir=tempdir,mode='w',delete=False)
            tmpfilename.write('')
            tmpfilename.close()
            landscape = LandscapeOutput()
            landscape.hostedLogosDir = tempdir
            landscape.removeHostedLogo(os.path.basename(tmpfilename.name))

            self.assertFalse(os.path.exists(tmpfilename.name))

'''

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )
    

    unittest.main()
