#!/usr/bin/env python3
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#
# encoding=utf8

## built in modules
import os
import tempfile
from pathlib import Path
from slugify import slugify
from typing import Self

## third party modules
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cairo

class SVGLogo:

    __contents = ''
    __filename = None

    def __init__(self, contents = None, filename = None, url = None, name = None):
        if contents:
            self.__contents = contents
        elif filename:
            with open(filename,'w') as f:
                self.__contents = f.read()
                self.__filename = filename
        elif url:
            session = requests.Session()
            retry = Retry(backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)        
            while True:
                try:
                    r = session.get(url, allow_redirects=True)
                    break
                except requests.exceptions.ChunkedEncodingError:
                    pass
            if r.status_code == 200:
                self.__contents = r.content.decode('utf-8')
        elif name:
           width = len(name) * 40
           height = len(name.split(" ")) * 80 
           with tempfile.TemporaryFile() as fp:
                with cairo.SVGSurface(fp, width, height) as surface:
                    context = cairo.Context(surface)
                    context.set_source_rgb(0,0,0)
                    context.set_font_size(60)
                    context.select_font_face(
                        "Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                    context.move_to(0,50)
                    parts = name.split(" ")
                    n = 2
                    for part in parts:
                        context.show_text(part)
                        context.move_to(0,n*60)
                        n += 1
                    context.stroke()
                    context.save()

                fp.seek(0)
                self.__contents = fp.read().decode('utf-8')

    def __str__(self):
        return self.__contents

    def filename(self, name):
        return self.__filename if self.__filename else "{}.svg".format(slugify(os.path.splitext(name)[0],separator='_'))

    def save(self, name, path = './'):
        filename = self.filename(name)
        filenamepath = os.path.normpath("{}/{}".format(path,filename))
        
        with open(filenamepath, 'w') as fp:
            fp.write(self.__contents)

        return filename

    def isValid(self):
        return self.__contents.find('base64') == -1 and self.__contents.find('<text') == -1 and self.__contents.find('<image') == -1 and self.__contents.find('<tspan') == -1

    def addCaption(self, caption="", title=""):
        postJson = {
            'svg': self.__contents, 
            'title': title,
            'caption': caption
        }
        x = requests.post("https://autocrop.cncf.io/autocrop", json=postJson)
        response = x.json()
        if response['success']:
            self.__contents = response['result']
        else:
            raise RuntimeError("Adding caption failed: {}".format(response['error']))

    def autocrop(self, title=''):
        postJson = {
            'svg': self.__contents, 
            'title': title
        }
        x = requests.post("https://autocrop.cncf.io/autocrop", json=postJson)
        response = x.json()
        if response['success']:
            self.__contents = response['result']
        else:
            raise RuntimeError("Autocrop failed: {}".format(response['error']))
