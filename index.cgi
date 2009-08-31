#!/usr/bin/python -u
# vim: set fileencoding=utf-8 :
#
# (C) 2008 Guido Guenther <agx@sigxcpu.org>
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

import cgi
import os
import re
import sys
#import cgitb; cgitb.enable(display=0, logdir='/tmp')
import urlgrabber
from lxml import etree
from genshi.template import TemplateLoader
import vcsbrowsers
from htmlchangelog import HTMLChangelog

VERSION="0.0.3"
XMLNS='http://www.w3.org/1999/xhtml'
PTS='http://packages.qa.debian.org'
PKGNAMERE="[a-zA-Z0-9.+\-]+$"


def fetch_changelog(cl_url):
    changelog = urlgrabber.urlread(cl_url, timeout=5.0).decode('utf-8')
    return changelog


def fetch_pts_page(package):
    pts = None
    try:
        url = "%s/%s" % (PTS, package)
        pts = urlgrabber.urlopen(url, timeout=5.0)
    except urlgrabber.grabber.URLGrabError, (code, msg):
        if code == 14:
            raise Exception, "Can't find package '%s' on '%s'" % (package, PTS)
        else:
            raise
    return pts


def parse_pts_xhtml(pts):
    cl_url = None
    vcs_url = None
    vcs = None

    tree = etree.parse(pts)
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
        return vcsbrowsers.GitWebBrowser(vcs_url)
    elif vcs == "Mercurial":
        return vcsbrowsers.HgBrowser(vcs_url)


def render_search_page(title, pkg=None, err=None):
    loader = TemplateLoader('templates')
    tmpl = loader.load('index.html')
    print tmpl.generate(title=title, pkg=pkg,
                        err=err).render('xhtml', doctype='xhtml-strict')


def render_changelog_page(cl):
    print cl


def main(argv):
    title = "cl2vcs %s" % VERSION
    err = ""

    print "Content-Type: text/html; charset=utf-8"
    print

    try:
        form = cgi.FieldStorage()

        if form.has_key('pkg'):
            pkg = form.getfirst('pkg').decode('utf-8').strip()
        else:
            pkg = None

        if pkg:
            if not re.match(PKGNAMERE, pkg):
                return render_search_page(title=title, err=u"Invalid package name: '%s'" % pkg)
        else:
            return render_search_page(title=title, err=err)

        try:
            pts = fetch_pts_page(pkg)
        except Exception, exc_err:
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
        except urlgrabber.grabber.URLGrabError, (errcode, errmsg):
            return render_search_page(title=title,
                                      err="Cannot fetch '%s': %s" % (cl_url, errmsg))
        if vcs and vcs_url:
            vcsbrowser = get_vcsbrowser(vcs, vcs_url)
        else:
            vcsbrowser = None
        cl = HTMLChangelog(cl_text, vcsbrowser=vcsbrowser)
        if cl:
            render_changelog_page(cl)
    except Exception, err:
        import traceback
        traceback.print_exc(file=sys.stderr)
        render_search_page(title=title, err="Unknown error")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

