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

        members = LFXMembers()
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].website,"https://consensys.net/")
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataNormalizeMembershipName(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"LF Energy - Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        members = LFXMembers()
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].website,"https://consensys.net/")
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataNormalizeMembershipName2(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"LF Energy - Premier Membership ( 10000 - 20000 )","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        members = LFXMembers()
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertEqual(members.members[0].website,"https://consensys.net/")
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)

    @responses.activate
    def testLoadDataNormalizeMembershipName3(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Silver Membership - MPSF","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        members = LFXMembers()
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Silver Membership - MPSF")
        self.assertEqual(members.members[0].website,"https://consensys.net/")
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg")
        self.assertEqual(members.members[1].membership,"Premier Membership")
        self.assertEqual(members.members[1].website,"https://hitachi-systems.com/")
        self.assertIsNone(members.members[1].twitter)
    
    @responses.activate
    def testLoadDataMissingWebsite(self):
        members = LFXMembers(loadData = False)
        responses.add(
            method=responses.GET,
            url=members.endpointURL.format(members.project),
            body="""[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"LF Energy - Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":""},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]"""
            )

        members = LFXMembers()
        self.assertEqual(members.members[0].orgname,"ConsenSys AG")
        self.assertEqual(members.members[0].crunchbase,"https://www.crunchbase.com/organization/consensus-systems--consensys-")
        self.assertEqual(members.members[0].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg")
        self.assertEqual(members.members[0].membership,"Premier Membership")
        self.assertIsNone(members.members[0].website)
        self.assertIsNone(members.members[0].twitter)
        self.assertEqual(members.members[1].orgname,"Hitachi, Ltd.")
        self.assertIsNone(members.members[1].crunchbase)
        self.assertEqual(members.members[1].logo,"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg")
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

class TestCrunchbaseMembers(unittest.TestCase):

    def testLoadDataBulkData(self):
        testcsvfilecontents = """
uuid,name,type,permalink,cb_url,rank,created_at,updated_at,legal_name,roles,domain,homepage_url,country_code,state_code,region,city,address,postal_code,status,short_description,category_list,category_groups_list,num_funding_rounds,total_funding_usd,total_funding,total_funding_currency_code,founded_on,last_funding_on,closed_on,employee_count,email,phone,facebook_url,linkedin_url,twitter_url,logo_url,alias1,alias2,alias3,primary_role,num_exits
e1393508-30ea-8a36-3f96dd3226033abd,Wetpaint,organization,wetpaint,https://www.crunchbase.com/organization/wetpaint,145154,2007-05-25 13:51:27,2019-06-24 22:19:25,,company,wetpaint.com,http://www.wetpaint.com/,USA,NY,New York,New York,902 Broadway 11th Floor New,10010,acquired,Wetpaint offers an online social publishing platform that helps digital publishers grow their customer base.,"Publishing,Social Media,Social Media Management","Content and Publishing,Internet Services,Media and Entertainment,Sales and Marketing",3,39750000,39750000,USD,2005-06-01,2008-05-19,,51-100,info@wetpaint.com,206-859-6300,https://www.facebook.com/Wetpaint,https://www.linkedin.com/company/wetpaint,https://twitter.com/wetpainttv,"https://crunchbase-production-res.cloudinary.com/image/upload/c_lpad,h_120,w_120,f_jpg/v1397180177/2036b3394a37152e0ff69f27c71bc883.jpg",,,,company,
"""
        tmpfilename = tempfile.NamedTemporaryFile(mode='w',delete=False)
        tmpfilename.write(testcsvfilecontents)
        tmpfilename.close()

        members = CrunchbaseMembers(bulkdatafile = tmpfilename.name, loadData = True)
        self.assertTrue(members.find('Wetpaint','http://www.wetpaint.com/'))
        self.assertTrue(members.find('Wetpaint','http://www.foo.com/'))
        self.assertFalse(members.find('Wetpainter','http://www.foo.com/'))

        members = CrunchbaseMembers()
        members.bulkdatafile = tmpfilename.name
        members.loadData()
        self.assertTrue(members.find('Wetpaint','http://www.wetpaint.com/'))
        self.assertTrue(members.find('Wetpaint','http://www.foo.com/'))
        self.assertFalse(members.find('Wetpainter','http://www.foo.com/'))

        os.unlink(tmpfilename.name)

class TestLandscapeOutput(unittest.TestCase):

    def testNewLandscape(self):
        landscape = LandscapeOutput()
        landscape.landscapeMemberCategory = 'test me'
        landscape.landscapeMemberClasses = [
            {"name": "Good Membership", "category": "Good"},
            {"name": "Bad Membership", "category": "Bad"}
            ]
        landscape.newLandscape()

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

            landscape = LandscapeOutput()
            landscape.landscapeMemberCategory = 'test me'
            landscape.landscapeMemberClasses = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            landscape.landscapefile = tmpfilename.name
            landscape.loadLandscape()

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['items'][0]['name'],"HERE Global B.V.")
            self.assertEqual(landscape.landscapeMembers[0]['name'],"Good")

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

            landscape = LandscapeOutput()
            landscape.landscapeMemberCategory = 'test me'
            landscape.landscapeMemberClasses = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            landscape.landscapefile = tmpfilename.name
            landscape.loadLandscape(reset=True)

            self.assertEqual(landscape.landscape['landscape'][0]['name'],'test me')
            self.assertEqual(landscape.landscape['landscape'][0]['subcategories'][0]['name'],"Good")
            self.assertEqual(len(landscape.landscape['landscape'][0]['subcategories'][0]['items']),0)
            self.assertEqual(landscape.landscapeMembers[0]['name'],"Good")

    def testLoadLandscapeEmpty(self):
        testlandscape = ""
        with tempfile.NamedTemporaryFile(mode='w') as tmpfilename:
            tmpfilename.write(testlandscape)
            tmpfilename.flush()

            landscape = LandscapeOutput()
            landscape.landscapeMemberCategory = 'test me'
            landscape.landscapeMemberClasses = [
                {"name": "Good Membership", "category": "Good"},
                {"name": "Bad Membership", "category": "Bad"}
                ]
            landscape.landscapefile = tmpfilename.name
            landscape.loadLandscape(reset=True)

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
