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

## third party modules
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import cairo

class SVGLogo:

    __contents = ''    

    def __init__(self, contents = None, filename = None, url = None):
        if contents:
            self.__contents = contents
        elif filename:
            with open(filename,'w') as f:
                self.__contents = f.read()
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
                self.__contents = r.content

    def __str__(self):
        return self.__contents.decode('utf-8')

    def filename(self, name):
        return "{}.svg".format(slugify(os.path.splitext(name)[0]))

    def save(self, name, path = './'):
        filename = self.filename(name)
        filenamepath = os.path.normpath("{}/{}".format(path,filename))
        
        with open(filenamepath, 'wb') as fp:
            fp.write(self.__contents)

        return filename

    @staticmethod
    def createTextLogo(name):
        width = len(name) * 40
        x = width / 2
        fp = tempfile.TemporaryFile()
        with cairo.SVGSurface(fp, width, 80) as surface:
            Context = cairo.Context(surface)
            Context.set_source_rgb(0,0,0)
            Context.set_font_size(60)
            Context.select_font_face(
                "Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            Context.move_to(0,50)
            Context.show_text(name)
            Context.stroke()
            Context.save()

        fp.seek(0)
        contents = fp.read()
        return SVGLogo(contents)

    def isValid(self):
        return True
        return self.__contents.find(b'base64') == -1 and self.__contents.find(b'<text') == -1 and self.__contents.find(b'<image') == -1 and self.__contents.find(b'<tspan') == -1

    def autocrop(self, title=''):
        postJson = {
            'svg': self.__contents.decode("utf-8"), 
            'title': title
        }
        x = requests.post("https://autocrop.cncf.io/autocrop", json=postJson)
        response = x.json()
        if response['success']:
            self.__contents = response['result'].encode("utf-8")
        else:
            raise RuntimeError("Autocrop failed: {}".format(response['error']))
