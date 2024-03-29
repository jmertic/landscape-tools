#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import csv
import os.path

from landscape_tools.members import Members
from landscape_tools.member import Member

class CrunchbaseMembers(Members):

    bulkdatafile = 'organizations.csv'

    def __init__(self, bulkdatafile = None, loadData = False):
        if bulkdatafile:
            self.bulkdatafile = bulkdatafile
        super().__init__(loadData)

    def loadData(self):
        if os.path.isfile(self.bulkdatafile):
            print("--Loading Crunchbase bulk export data--")
            with open(self.bulkdatafile, newline='') as csvfile:
                memberreader = csv.reader(csvfile, delimiter=',', quotechar='"')
                fields = next(memberreader)
                for row in memberreader:
                    member = Member()
                    try:
                        member.membership = ''
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.orgname = row[1]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.website = row[11]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo
                    try:
                        member.crunchbase = row[4]
                    except ValueError as e:
                        pass # avoids all the Exceptions for logo

                    self.members.append(member)


