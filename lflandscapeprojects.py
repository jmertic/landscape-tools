#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

from landscape_tools.config import Config
from landscape_tools.lfxprojects import LFXProjects
from landscape_tools.landscapeoutput import LandscapeOutput

import logging
import sys
from datetime import datetime
from argparse import ArgumentParser,FileType

def main():
    startTime = datetime.now()
   
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            #logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    lfxprojects = LFXProjects()

    config = Config()
    config.landscapeCategory = 'Projects'
    config.landscapeSubcategories = [{"name": "All", "category": "All"}]

    lflandscape = LandscapeOutput(config, resetCategory=True)
    lflandscape.processIntoLandscape(lfxprojects.members)
    lflandscape.updateLandscape()
    
    logging.getLogger().info("Successfully added {} members and skipped {} members".format(lflandscape.itemsAdded,lflandscape.itemsErrors))
    logging.getLogger().info("This took {} seconds".format(datetime.now() - startTime))

if __name__ == '__main__':
    main()

