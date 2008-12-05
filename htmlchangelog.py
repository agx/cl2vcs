# vim: set fileencoding=utf-8 :

import re
import cgi
from genshi.template import TemplateLoader
import debian_bundle.changelog

_TEMPLATEDIR='templates/'

class HTMLChangelogFilter(object):
    commit_id_re = re.compile(r"(?P<s>\s+\*\s+\[)"
                              +r"(?P<commitid>[a-fA-F0-9]{7,})"
                              +r"(?P<e>\]\s+.*)")

    def __init__(self, vcsbrowser=None):
        self.vcsbrowser=vcsbrowser

    def vcs_commit_filter(self, changes):
        body = []
        for line in changes:
            line = cgi.escape(line)
            m = self.commit_id_re.match(line)
            if m:
                commitid = m.group('commitid')
                link = '<a href="%s">%s</a>' % (self.vcsbrowser.commit(commitid), commitid)
                body.append(m.group("s") + link + m.group("e"))
            else:
                body.append(line)
        return "\n".join(body)

    def markup_block(self, block):
        if self.vcsbrowser:
            block.body = self.vcs_commit_filter(block.changes())
        else:
            block.body = cgi.escape("\n".join(block.changes()))
        return block


class HTMLChangelog(debian_bundle.changelog.Changelog):
    def __init__(self, file=None, max_blocks=None, allow_empty_author=False, strict=True, templatedir=_TEMPLATEDIR, vcsbrowser=None):
        debian_bundle.changelog.Changelog.__init__(self, file=file, max_blocks=max_blocks,
                                                   allow_empty_author=allow_empty_author,
                                                   strict=strict)
        self.templatedir = templatedir
        loader = TemplateLoader(self.templatedir)
        self.html_tmpl = loader.load('cl.html')
        self.block_tmpl = loader.load('block.html')
        self.filter = HTMLChangelogFilter(vcsbrowser=vcsbrowser)

    def markup_block(self, block):
        return self.block_tmpl.generate(block=self.filter.markup_block(block))

    def stream(self):
        title = u"Changelog for %s (%s)" % (self.get_package(), self.get_version())
        return self.html_tmpl.generate(title=title, blocks=self._blocks, markup_block=self.markup_block)

    def __str__(self):
        return self.stream().render('xhtml', doctype='xhtml-strict')

