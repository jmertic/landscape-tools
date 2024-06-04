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
from landscape_tools.crunchbasemembers import CrunchbaseMembers
from landscape_tools.landscapeoutput import LandscapeOutput

from datetime import datetime
from argparse import ArgumentParser,FileType
import os
from os import path
import logging
import sys

def main():
    
    startTime = datetime.now()

    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            #logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # load config
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="configfile", type=FileType('r'), help="name of YAML config file")
    args = parser.parse_args()
    if args.configfile:
        config = Config(args.configfile)
    elif os.path.isfile("config.yml"):
        config = Config("config.yml")
    else:
        config = Config("config.yaml")

    # load member data sources
    lfxmembers = LFXMembers(project = config.project)

    lflandscape = LandscapeOutput(config, resetCategory=True)
    lflandscape.processIntoLandscape(lfxmembers.members)
    lflandscape.updateLandscape()
    
    logging.getLogger().info("Successfully added {} members and skipped {} members".format(lflandscape.itemsAdded,lflandscape.itemsErrors))
    logging.getLogger().info("This took {} seconds".format(datetime.now() - startTime))

if __name__ == '__main__':
    main()
