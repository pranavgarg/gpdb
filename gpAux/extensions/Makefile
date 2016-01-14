# protect the default target for this file from the targets in Makefile.global
# and Makefile.thirdparty
default: all

BLD_TOP=..

include $(BLD_TOP)/Makefile.global
include $(BLD_TOP)/Makefile.thirdparty
include $(BLD_TOP)/Makefile.windows

top_builddir = ../..
include $(top_builddir)/src/Makefile.global

ENV_JAVA_HOME:=$(shell echo $$JAVA_HOME)
ifneq (${ENV_JAVA_HOME},)
	JAVA_HOME=${ENV_JAVA_HOME}
endif

all: mkgpfdist mkdbgen mkgphdfs


.PHONY:
mkgpfdist:
	if [ "$(enable_gpfdist)" = "yes" ]; then \
		echo "gpfdist enabled"; \
		# we assume that ext only exists during an enterprise build
		if [ -d "../ext" ]; then \
			$(MAKE) -f Makefile.gpfdist INSTLOC=$(prefix); \
		else \
			cd gpfdist && ./configure --enable-transformations --prefix=$(prefix) \
			&& $(MAKE); \
		fi; \
	else \
		echo "gpfdist disabled"; \
	fi

install: mkgpfdist mkgphdfs
	if [ "$(enable_gpfdist)" = "yes" ]; then \
		if [ ! -d $(prefix)/bin ]; then \
			mkdir -p $(prefix)/bin ; \
		fi; \
		cp -p gpfdist/gpfdist$(EXE_EXT) $(prefix)/bin/ ; \
	fi

clean:
	@if [ -d gpfdist/GNUmakefile ]; then $(MAKE) -C gpfdist clean; fi
	$(MAKE) -C gphdfs JAVA_HOME=${JAVA_HOME} ANT=/opt/releng/apache-ant/bin/ant

distclean:
	@if [ -d gpfdist/GNUmakefile ]; then $(MAKE) -C gpfdist clean; fi

.PHONY:
mkdbgen:
	$(MAKE) -f Makefile.tpch INSTLOC=$(INSTLOC)

.PHONY:
mkgphdfs:
	if [ "$(enable_gphdfs)" = "yes" ]; then \
		echo "gphdfs enabled"; \
		PATH=$(prefix)/bin:$(PATH) $(MAKE) -C gphdfs USE_PGXS=1 docdir=$(prefix)/docs install \
			ANT=/opt/releng/apache-ant/bin/ant \
			JAVA_HOME=${JAVA_HOME}; \
	else \
		echo "gphdfs disabled"; \
	fi

# Use $JAVA_HOME if specified, otherwise look for java in the likely places.
# Note that Darwin's JVM layout is pretty weird.  JDK 1.6 apears to be the
# default for Snow Leopard, but JDK 1.5 is for Leopard.
# See http://developer.apple.com/qa/qa2001/qa1170.html
ifeq ($(wildcard "${JAVA_HOME}/bin/java"),)
  JDK="${JAVA_HOME}"
else
  ifeq ($(wildcard "/System/Library/Frameworks/JavaVM.framework/Versions/1.6/Home/bin/java"),)
    JDK="/System/Library/Frameworks/JavaVM.framework/Versions/1.6/Home"
  else
    ifeq ($(wildcard "/usr/java/bin/java"),)
      JDK="/usr/java"
    else
      echo JAVA_HOME not found
    endif
  endif
endif
JAVA=${JAVA_HOME}/bin/java
JAVAC=${JAVA_HOME}/bin/javac
JAVAH=${JAVA_HOME}/bin/javah
JAR=${JAVA_HOME}/bin/jar
JAVADOC=${JAVA_HOME}/bin/javadoc

.PHONY:
mkpljava:
	PATH=$(INSTLOC)/bin:$(PATH) $(MAKE) -C pljava \
		JAVA_HOME=${JAVA_HOME} JAVA=${JAVA} JAVAC=${JAVAC} JAVAH=${JAVAH} JAR=${JAR} JAVADOC=${JAVADOC}  install

.PHONY:
mkplr:
	PATH=$(INSTLOC)/bin:$(PATH) $(MAKE) -C plr install USE_PGXS=1

.PHONY:
mkorafce:
	PATH=$(INSTLOC)/bin:$(PATH) $(MAKE) -C orafce install USE_PGXS=1

installcheck:
	PATH=$(INSTLOC)/bin:$(PATH) $(MAKE) -C orafce installcheck USE_PGXS=1
	PATH=$(INSTLOC)/bin:$(PATH) $(MAKE) -C gphdfs installcheck USE_PGXS=1
