VERSION=$(shell grep ^VERSION cl2vcs.py | sed -e s'/.*\="\([0-9.]\+\)".*/\1/')
PKG=cl2vcs

all:
	nosetests3 --with-doctest

clean:
	rm -f *.pyc

dist: clean
	git-archive --format=tar --prefix=$(PKG)-$(VERSION)/ HEAD | gzip -c > ../$(PKG)-$(VERSION).tar.gz

