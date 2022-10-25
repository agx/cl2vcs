#!/usr/bin/python3 -u
# vim: set fileencoding=utf-8 :
#
# (C) 2008,2015,2022 Guido Guenther <agx@sigxcpu.org>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""Link Debian changelog entries to the VCS"""

from builtins import str
import cgi
import os
import re
import sys
import requests
from lxml import etree
from genshi.template import TemplateLoader
import vcsbrowsers
from htmlchangelog import HTMLChangelog
from io import BytesIO

VERSION="0.0.5"
XMLNS='http://www.w3.org/1999/xhtml'
PTS='http://packages.qa.debian.org'
PKGNAMERE="[a-zA-Z0-9.+\-]+$"
TITLE = "cl2vcs %s" % VERSION


def fetch_changelog(cl_url):
    resp = requests.get(cl_url, timeout=5.0)
    resp.raise_for_status()
    return resp.content


def fetch_pts_page(package):
    pts = None
    url = "%s/%s" % (PTS, package)
    resp = requests.get(url, timeout=5.0)
    if resp.status_code == 404:
        raise Exception("Can't find package '%s' on '%s'" % (package, PTS))
    resp.raise_for_status()
    return resp.content


def parse_pts_xhtml(pts):
    cl_url = None
    vcs_url = None
    vcs = None

    tree = etree.parse(BytesIO(pts))
    searcher = etree.ETXPath('/{%s}html/{%s}body//{%s}a[@href]' % (XMLNS, XMLNS, XMLNS))
    result = searcher(tree)

    for r in result:
        if not r.text:
            continue
        if r.text.lower() == "changelog":
            cl_url = r.attrib['href']
        elif r.text.lower() == "browse":
            vcs_url = r.attrib['href']
            parent = r.getparent()
            vcs = parent.getchildren()[0].text.lower()
    return cl_url, vcs_url, vcs


def get_vcsbrowser(vcs, vcs_url):
    if vcs == "git":
        return vcsbrowsers.guess_git_repo(vcs_url)
    elif vcs == "Mercurial":
        return vcsbrowsers.HgBrowser(vcs_url)


def render_search_page(title, pkg=None, err=None):
    loader = TemplateLoader('templates')
    tmpl = loader.load('index.html', encoding='utf-8')
    t = tmpl.generate(title=title, pkg=pkg, err=err)
    print(t.render('xhtml', doctype='xhtml-strict'))



def render_changelog_page(cl):
    print(cl)


def handle_pkg(pkg, title):
    if pkg:
        if not re.match(PKGNAMERE, pkg):
            return render_search_page(title=title, err=u"Invalid package name: '%s'" % pkg)
        else:
            pkg = str(pkg)
    else:
        return render_search_page(title=title, err="")

    try:
        pts = fetch_pts_page(pkg)
    except Exception as exc_err:
        err = exc_err
        pts = None

    if not pts:
        return render_search_page(title=title, pkg=pkg, err=err)

    cl_url, vcs_url, vcs = parse_pts_xhtml(pts)
    if cl_url == None:
        return render_search_page(title=title, pkg=pkg,
                                  err="Cannot parse changelog from PTS page.")
    try:
        cl_text = fetch_changelog(cl_url)
    except urlgrabber.grabber.URLGrabError as e:
        (errcode, errmsg) = e.args
        return render_search_page(title=title,
                                  err="Cannot fetch '%s': %s" % (cl_url, errmsg))
    if vcs and vcs_url:
        vcsbrowser = get_vcsbrowser(vcs, vcs_url)
    else:
        vcsbrowser = None
    cl = HTMLChangelog(cl_text, vcsbrowser=vcsbrowser)
    if cl:
        render_changelog_page(cl)


def main(argv):
    err = ""

    print("Content-Type: text/html; charset=utf-8")
    print()

    try:
        form = cgi.FieldStorage()

        if 'pkg' in form:
            pkg = form.getfirst('pkg').strip()
        else:
            pkg = None

        handle_pkg(pkg, TITLE)
    except Exception as err:
        import traceback
        traceback.print_exc(file=sys.stderr)
        render_search_page(title=TITLE, err="Unknown error")
    return 0

