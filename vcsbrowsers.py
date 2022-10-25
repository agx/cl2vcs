# convenience wrappers to construct links
# into the webinterfaces of different VCSs

from builtins import object
import re


class VCSBrowser(object):
    def __init__(self, url):
        self.url = url.rstrip('/')

    def commit(self, commtid):
        raise NotImplemented

    def branch(self, branch):
        raise NotImplemented

class GitlabBrowser(VCSBrowser):
    """
    Gitlab based repo browser

    URLs for gitlab:
    e.g. http://salsa.debian.org/libvirt-team/libvirt.git
    """
    repotype = "gitweb"

    def __init__(self, url):
        VCSBrowser.__init__(self, url)

    @classmethod
    def check(cls, url):
        return True if 'https://salsa.debian.org/' in url else False

    def commit(self, commitid):
        return "%s/commit/%s" % (self.url, commitid)

class GitWebBrowser(VCSBrowser):
    """
    GitWeb based repo browser

    URLs for gitweb:
    e.g. http://git.debian.org/?p=pkg-libvirt/gtk-vnc.git
    """
    repotype = "gitweb"

    def __init__(self, url):
        url = re.sub(r';a=summary$', '', url)
        VCSBrowser.__init__(self, url)

    @classmethod
    def check(cls, url):
        return True if '/?p=' in url else False

    def commit(self, commitid):
        return "%s;a=commitdiff;h=%s" % (self.url, commitid)


class CGitBrowser(VCSBrowser):
    repotype = "cgit"

    def __init__(self, url):
        VCSBrowser.__init__(self, url)

    @classmethod
    def check(cls, url):
        return True if '/cgit' in url else False

    def commit(self, commitid):
        return "%s/commit/?id=%s" % (self.url, commitid)


def guess_git_repo(url):
    """
    >>> guess_git_repo("http://example.com/?p=foo").repotype
    'gitweb'
    >>> guess_git_repo("http://example.com/cgit/foo").repotype
    'cgit'
    >>> guess_git_repo("http://example.com/bar/foo").repotype
    'cgit'
    """
    for repotype in [GitlabBrowser, CGitBrowser, GitWebBrowser]:
        if repotype.check(url):
            return repotype(url)
    return CGitBrowser(url)


class HgBrowser(VCSBrowser):
    """
    URLs for Mercurial:
    e.g. http://hg.et.redhat.com/virt/applications/virtinst--devel
    """

    def commit(self, commitid):
        return "%s?cs=%s" % (self.url, commitid)
