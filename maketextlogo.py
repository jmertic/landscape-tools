#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

import sys

from argparse import ArgumentParser,FileType

import requests

from landscape_tools.svglogo import SVGLogo
    
def main():
    # load config
    parser = ArgumentParser()
    parser.add_argument("-n", "--name", dest="orgname", required=True, help="Name to appear in logo")
    parser.add_argument("--autocrop", dest="autocrop", action='store_true', help="Process logo with autocrop")
    parser.add_argument("-o", "--output", dest="filename", help="Filename to save created logo to")
    args = parser.parse_args()

    svglogo = SVGLogo.createTextLogo(args.orgname)

    if args.autocrop:
        svglogo.autocrop()

    if args.filename:
        svglogo.save(args.filename)
    else:
        print(svglogo)
        
if __name__ == '__main__':
    main()
