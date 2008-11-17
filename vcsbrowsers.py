# convenience wrappers to construct links 
# into the webinterfaces of different VCSs

class VCSBrowser:
    def __init__(self, url):
        self.url = url.rstrip('/')

    def commit(self, commtid):
        raise NotImplemented

    def branch(self, branch):
        raise NotImplemented


class GitWebBrowser(VCSBrowser):
    """
    URLs for gitweb:
    e.g. http://git.debian.org/?p=pkg-libvirt/gtk-vnc.git
    """
    def commit(self, commitid):
        return "%s;a=commitdiff;h=%s" % (self.url, commitid)

    def branch(self, branch):
        return "%s;a=shortlog;h=refs/heads/%s" % (self.url, branch)


class HgBrowser(VCSBrowser):
    """
    URLs for Mercurial:
    e.g. http://hg.et.redhat.com/virt/applications/virtinst--devel
    """

    def commit(self, commitid):
        return "%s?cs=%s" % (self.url, commitid)


