#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from landscape_tools.config import Config
from landscape_tools.lfxmembers import LFXMembers
from landscape_tools.lfxprojects import LFXProjects
from landscape_tools.landscapemembers import LandscapeMembers
from landscape_tools.landscapeoutput import LandscapeOutput
from landscape_tools.svglogo import SVGLogo

from datetime import datetime
from argparse import ArgumentParser,FileType
import os
from os import path
import logging
import sys

class Cli:

    _startTime = None

    def __init__(self):
        self._startTime = datetime.now()

        parser = ArgumentParser("Collection of tools for working with a landscape")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-s", "--silent", dest="silent", action="store_true", help="Suppress all messages")
        group.add_argument("-v", "--verbose", dest="verbose", action='store_true', help="Verbose output ( i.e. show all INFO level messages in addition to WARN and above )")
        subparsers = parser.add_subparsers(help='sub-command help')
        
        buildlandscapemembers_parser = subparsers.add_parser("buildmembers", help="Replace current project members with latest from LFX")
        buildlandscapemembers_parser.add_argument("-c", "--config", dest="configfile", default="config.yml", type=FileType('r'), help="name of YAML config file")
        buildlandscapemembers_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        buildlandscapemembers_parser.set_defaults(func=self.buildmembers)
        
        buildlandscapeprojects_parser = subparsers.add_parser("buildprojects", help="Replace current project projects with latest from LFX")
        buildlandscapeprojects_parser.add_argument("-c", "--config", dest="configfile", default="config.yml", type=FileType('r'), help="name of YAML config file")
        buildlandscapeprojects_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        buildlandscapeprojects_parser.set_defaults(func=self.buildprojects)
        
        synclandscapeprojects_parser = subparsers.add_parser("syncprojects", help="Sync current project projects with latest from LFX")
        synclandscapeprojects_parser.add_argument("-c", "--config", dest="configfile", default="config.yml", type=FileType('r'), help="name of YAML config file")
        synclandscapeprojects_parser.add_argument("-d", "--dir", dest="basedir", default=".", type=self._dir_path, help="path to where landscape directory is")
        synclandscapeprojects_parser.set_defaults(func=self.syncprojects)
        
        maketextlogo_parser = subparsers.add_parser("maketextlogo", help="Create a text pure SVG logo")
        maketextlogo_parser.add_argument("-n", "--name", dest="orgname", required=True, help="Name to appear in logo")
        maketextlogo_parser.add_argument("--autocrop", dest="autocrop", action='store_true', help="Process logo with autocrop")
        maketextlogo_parser.add_argument("-o", "--output", dest="filename", help="Filename to save created logo to")
        maketextlogo_parser.set_defaults(func=self.maketextlogo)
        
        args = parser.parse_args()

        logging.basicConfig(
            level=logging.INFO if args.verbose else logging.WARN,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler("debug.log"),
                logging.StreamHandler(sys.stdout) if not args.silent else None
            ]
        )

        args.func(args)

    def _dir_path(self,path):
        if os.path.isdir(path):
            return path
        else:
            raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")
    
    def buildmembers(self,args):
        config = Config(args.configfile)

        # load member data sources
        lfxmembers = LFXMembers(project=config.project)

        landscapeoutput = LandscapeOutput(config, resetCategory=True, baseDir=args.basedir)
        landscapeoutput.processIntoLandscape(lfxmembers.members)
        landscapeoutput.updateLandscape()
        
        logging.getLogger().info("Successfully added {} members and skipped {} members".format(landscapeoutput.itemsAdded,landscapeoutput.itemsErrors))
        logging.getLogger().info("This took {} seconds".format(datetime.now() - self._startTime))

    def buildprojects(self,args):
        config = Config(args.configfile,view='projects')

        lfxprojects = LFXProjects(project=config.slug)
        landscapeoutput = LandscapeOutput(config, resetCategory=True, baseDir=args.basedir)
        landscapeoutput.processIntoLandscape(lfxprojects.members)
        landscapeoutput.updateLandscape()
        
        logging.getLogger().info("Successfully added {} projects and skipped {} projects".format(landscapeoutput.itemsAdded,landscapeoutput.itemsErrors))
        logging.getLogger().info("This took {} seconds".format(datetime.now() - self._startTime))

    def syncprojects(self,args):
        config = Config(args.configfile,view='projects')

        lfxprojects = LFXProjects(project=config.slug)
        landscapeoutput = LandscapeOutput(config=config, resetCategory=True, baseDir=args.basedir)
        landscapeoutput.processIntoLandscape(lfxprojects.members)
        landscapeoutput.updateLandscape()
        
        logging.getLogger().info("Successfully added {} projects and skipped {} projects".format(landscapeoutput.itemsAdded,landscapeoutput.itemsErrors))
        logging.getLogger().info("This took {} seconds".format(datetime.now() - self._startTime))

    def maketextlogo(self,args):
        svglogo = SVGLogo.createTextLogo(args.orgname)

        if args.autocrop:
            svglogo.autocrop()

        if args.filename:
            svglogo.save(args.filename)
        else:
            print(svglogo)
