#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import unittest

from LandscapeTools import Config, Member, Members, SFDCMembers, LandscapeMembers, CrunchbaseMembers, LFWebsiteMembers, CsvMembers, LandscapeOutput

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

class TestMembers(unittest.TestCase):

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

    def testFindFail(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = Members()
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com'))

    def testNormalizeCompanyEmptyOrg(self):
        members = Members()
        self.assertEqual(members.normalizeCompany(None),'')

    def testNormalizeCompany(self):
        companies = [
            {"name":"Foo","normalized":"Foo"},
            {"name":"Foo Inc.","normalized":"Foo"}
        ]

        for company in companies:
            members = Members()
            self.assertEqual(members.normalizeCompany(company["name"]),company["normalized"])

class TestSFDCMembers(unittest.TestCase):

    def testFind(self):
        member = Member()
        member.orgname = 'test'
        member.website = 'https://foo.com'
        member.logo = 'Gold.svg'
        member.membership = 'Gold'
        member.crunchbase = 'https://www.crunchbase.com/organization/visual-effects-society'

        members = SFDCMembers()
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

        members = SFDCMembers()
        members.members.append(member)

        self.assertFalse(members.find('dog','https://bar.com',member.membership))
        self.assertFalse(members.find(member.orgname,member.website,'Silver'))

if __name__ == '__main__':
    unittest.main()
