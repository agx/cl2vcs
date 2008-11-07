VERSION=$(shell grep ^VERSION index.cgi | sed -e s'/.*\="\([0-9.]\+\)".*/\1/')
PKG=cl2vcs

all:

clean:
	rm -f *.pyc

dist: clean
	git-archive --format=tar --prefix=$(PKG)-$(VERSION)/ HEAD | gzip -c > ../$(PKG)-$(VERSION).tar.gz

