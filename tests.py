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

from landscape_tools.config import Config
from landscape_tools.member import Member
from landscape_tools.members import Members
from landscape_tools.lfxmembers import LFXMembers
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.crunchbasemembers import CrunchbaseMembers
from landscape_tools.landscapeoutput import LandscapeOutput

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

        membertooverlay.overlay(member)

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'gold.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertIsNone(member.stock_ticker)
        self.assertFalse(hasattr(member,'organization'))

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
        self.assertFalse(hasattr(member,'organization'))

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

'''
    @responses.activate
    def testHostLogo(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','dog'),'dog.svg')

    @responses.activate
    def testHostLogoUnicode(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','privée'),'privee.svg')
    
    @responses.activate
    def testHostLogoNonASCII(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            logofile = landscape.hostLogo('https://someurl.com/boom.svg','北京数悦铭金技术有限公司')
            self.assertTrue(os.path.exists(landscape.hostedLogosDir+"/"+logofile))
    
    @responses.activate
    def testHostLogoContainsPNG(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data data:image/png;base64 dfdfdf'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','privée'),'')
    
    @responses.activate
    def testHostLogoContainsText(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body=b'this is image data <text /> dfdfdf'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','privée'),'')
    
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
            body=b'this is image data <text /> dfdfdf'
            )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir:
            landscape.hostedLogosDir = tempdir
            landscape.hostLogo('https://someurl.com/boom.svg','privée')

    def testHostLogoLogoisNone(self):
        landscape = LandscapeOutput()
        self.assertEqual(landscape.hostLogo(None,'dog'),None)
    
    def testHostLogoNotURL(self):
        landscape = LandscapeOutput()
        self.assertEqual(landscape.hostLogo('boom','dog'),'boom')

    @responses.activate
    def testHostLogo404(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='{"error": "not found"}', status=404,
        )

        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','boom'),'https://someurl.com/boom.svg')

    @responses.activate
    def testHostLogo404FileExists(self):
        responses.add(
            method=responses.GET,
            url='https://someurl.com/boom.svg',
            body='{"error": "not found"}', status=404,
        )
        with tempfile.TemporaryDirectory() as tempdir:
            tmpfilename = tempfile.NamedTemporaryFile(dir=tempdir,mode='w',delete=False,suffix='.svg')
            tmpfilename.write('')
            tmpfilename.close()
            landscape = LandscapeOutput()
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg',os.path.basename(tmpfilename.name).removesuffix('.svg')),os.path.basename(tmpfilename.name))
            
            landscape.removeHostedLogo(os.path.basename(tmpfilename.name))

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
    unittest.main()
