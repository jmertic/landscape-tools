#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest
import unittest.mock
from unittest.mock import Mock, MagicMock, patch
from unittest import mock
import tempfile
import os

from LandscapeTools import Config, Member, Members, SFDCMembers, LandscapeMembers, CrunchbaseMembers, LandscapeOutput

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self):
            self.content = b'this is image data'
            self.status_code = 200

    return MockResponse()


class TestMember(unittest.TestCase):

    def testSetCrunchbaseValid(self):
        validCrunchbaseURLs = [
            'https://www.crunchbase.com/organization/visual-effects-society'
        ]

        for validCrunchbaseURL in validCrunchbaseURLs:
            member = Member()
            member.crunchbase = validCrunchbaseURL
            self.assertEqual(member.crunchbase,validCrunchbaseURL)
            self.assertTrue(member._validCrunchbase)

    def testSetCrunchbaseNotValidOnEmpty(self):
        member = Member()
        member.orgname = 'test'
        with self.assertRaises(ValueError,msg="Member.crunchbase must be not be blank for test") as ctx:
            member.crunchbase = ''

        self.assertFalse(member._validCrunchbase)

    def testSetCrunchbaseNotValid(self):
        invalidCrunchbaseURLs = [
            'https://yahoo.com',
            'https://www.crunchbase.com/person/johndoe'
        ]

        for invalidCrunchbaseURL in invalidCrunchbaseURLs:
            member = Member()
            member.orgname = 'test'
            with self.assertRaises(ValueError,msg="Member.crunchbase for test must be set to a valid crunchbase url - '{crunchbase}' provided".format(crunchbase=invalidCrunchbaseURL)) as ctx:
                member.crunchbase = invalidCrunchbaseURL

            self.assertFalse(member._validCrunchbase)

    def testSetWebsiteValid(self):
        validWebsiteURLs = [
            'https://crunchbase.com/'
        ]

        for validWebsiteURL in validWebsiteURLs:
            member = Member()
            member.website = validWebsiteURL
            self.assertEqual(member.website,validWebsiteURL)
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
            member = Member()
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
        self.assertEqual(dict.popitem(),('crunchbase', member.crunchbase))
        self.assertEqual(dict.popitem(),('logo', None))
        self.assertEqual(dict.popitem(),('homepage_url', member.website))
        self.assertEqual(dict.popitem(),('name', member.orgname))
        self.assertEqual(dict.popitem(),('item', None))

    def testIsValidLandscapeItem(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertTrue(member.isValidLandscapeItem())

    def testIsValidLandscapeItemEmptyOrgname(self):
        member = Member()
        member.orgname = ''
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        self.assertFalse(member.isValidLandscapeItem())

    def testOverlay(self):
        membertooverlay = Member()
        membertooverlay.orgname = 'test2'
        membertooverlay.website = 'https://foo.com'
        membertooverlay.logo = 'gold.svg'
        membertooverlay.membership = 'Gold'
        membertooverlay.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.org'
        member.membership = 'Silver'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society-bad'
        member.twitter = 'https://twitter.com/mytwitter'
        member.stock_ticker = None

        membertooverlay.overlay(member)

        self.assertEqual(member.orgname,'test')
        self.assertEqual(member.website,'https://foo.org/')
        self.assertEqual(member.logo,'gold.svg')
        self.assertEqual(member.membership,'Silver')
        self.assertEqual(member.crunchbase, 'https://www.crunchbase.com/organization/visual-effects-society')
        self.assertEqual(member.twitter,'https://twitter.com/mytwitter')
        self.assertEqual(member.stock_ticker,None)
        


class TestMembers(unittest.TestCase):

    @patch("LandscapeTools.Members.__abstractmethods__", set())
    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members()
        members.members.append(member)

        self.assertTrue(members.find(member.orgname,member.website))
        self.assertTrue(members.find('dog',member.website))
        self.assertTrue(members.find(member.orgname,'https://bar.com'))

    @patch("LandscapeTools.Members.__abstractmethods__", set())
    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members()
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    @patch("LandscapeTools.Members.__abstractmethods__", set())
    def testNormalizeCompanyEmptyOrg(self):
        members = Members(loadData=False)
        self.assertEqual(members.normalizeCompany(None),'')

    @patch("LandscapeTools.Members.__abstractmethods__", set())
    def testNormalizeCompany(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members(loadData=False)
            self.assertEqual(members.normalizeCompany(company["name"]),company["normalized"])

class TestSFDCMembers(unittest.TestCase):

    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = SFDCMembers(loadData=False)
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

        members = SFDCMembers(loadData=False)
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.orgname,member.website,'Silver'))

    @patch('urllib.request.urlopen')
    def testLoadData(self,mock_urlopen):
        mock = MagicMock()
        mock.getcode.return_value = 200
        mock.read.return_value = '[{"ID":"0014100000Te1TUAAZ","Name":"ConsenSys AG","CNCFLevel":"","CrunchBaseURL":"https://crunchbase.com/organization/consensus-systems--consensys-","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/consensys_ag.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"consensys.net"},{"ID":"0014100000Te04HAAR","Name":"Hitachi, Ltd.","CNCFLevel":"","LinkedInURL":"www.linkedin.com/company/hitachi-data-systems","Logo":"https://lf-master-organization-logos-prod.s3.us-east-2.amazonaws.com/hitachi-ltd.svg","Membership":{"Family":"Membership","ID":"01t41000002735aAAA","Name":"Premier Membership","Status":"Active"},"Slug":"hyp","StockTicker":"","Twitter":"","Website":"hitachi-systems.com"}]'.encode()
        mock.__enter__.return_value = mock
        mock_urlopen.return_value = mock

        members = SFDCMembers()
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



class TestLandscapeMembers(unittest.TestCase):

    def testNormalizeLogo(self):
        members = LandscapeMembers()
        self.assertEqual(
            'https://raw.githubusercontent.com/dog/cat/master/hosted_logos/mouse.svg',
            members.normalizeLogo('mouse.svg','dog/cat')
        )

    def testNormalizeLogoIsEmpty(self):
        members = LandscapeMembers()
        self.assertEqual(
            '',
            members.normalizeLogo('','dog/cat')
        )
        self.assertEqual(
            '',
            members.normalizeLogo(None,'dog/cat')
        )

    def testNormalizeLogoIsURL(self):
        members = LandscapeMembers()
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


    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def testHostLogo(self,mock_get):
        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','dog'),'dog.svg')

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def testHostLogoUnicode(self,mock_get):
        landscape = LandscapeOutput()
        with tempfile.TemporaryDirectory() as tempdir: 
            landscape.hostedLogosDir = tempdir
            self.assertEqual(landscape.hostLogo('https://someurl.com/boom.svg','privée'),'privee.svg')
    
    def testHostLogoNotURL(self):
        landscape = LandscapeOutput()
        self.assertEqual(landscape.hostLogo('boom','dog'),'boom')

if __name__ == '__main__':
    unittest.main()
