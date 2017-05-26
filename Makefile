.PHONY: help clean clean-all srpm rpm prepare devbuild signrpm signrepo
.DEFAULT: help
ifndef VERBOSE
.SILENT:
endif
SHELL=bash
CWD:=$(shell pwd -P)
NAME=nextcloud
VERSION:=$(shell cat SPECS/nextcloud.spec | grep "define base_version" | awk '{print $$3}')
BUILD_NUMBER?=DEV
DONE = echo -e "\e[31m✓\e[0m \e[33m$@\e[0m \e[32mdone\e[0m"
TOOLS="rpmdevtools mock"
NTOOLS:=$(shell rpm -qa "$(TOOLS)" | wc -l)
PKG:=$(shell if [ -d pkg ]; then ls RPMS/$(NAME)-$(VERSION)*.noarch.rpm; else echo 0; fi)

help:: ## Show this help
	echo -e "\n$(NAME) packaging: Version \033[32m$(VERSION)\033[0m Release: \033[1m$(BUILD_NUMBER)\033[0m\n"
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-20s\033[0m %s\n", $$1, $$2}'

prepare: clean # $(NAME)-$(VERSION).tgz
ifneq ($(NTOOLS), 2)
	@yum install -y "$(TOOLS)"
endif
	mkdir -p SRPMS RPMS pkg
	spectool -C SOURCES/ -g $(CWD)/SPECS/$(NAME).spec
	$(DONE)

srpm: prepare ## Build a source rpm
	mock --buildsrpm --spec=$(CWD)/SPECS/$(NAME).spec --sources=$(CWD)/SOURCES/ --resultdir=$(CWD)/SRPMS --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)"
	rm -rf SRPMS/*.log
	echo -e "Package saved to: \e[31m`ls SRPMS/$(NAME)-$(VERSION)*.src.rpm`\e[0m"
	$(DONE)

rpm: srpm ## Build an rpm from the sourcerpm
	mock --rebuild $(CWD)/SRPMS/$(NAME)*.src.rpm --resultdir=$(CWD)/RPMS/ --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)"
	cp RPMS/$(NAME)-$(VERSION)*.noarch.rpm pkg/
	echo -e "Package saved to: \e[31m`ls RPMS/$(NAME)-$(VERSION)*.noarch.rpm`\e[0m"
	$(DONE)

clean: ## Clean up the workspace
	rm -rf RPMS SRPMS SOURCES/*.{gz,bz2}
	$(DONE)

clean-all: clean ## Clean up also packages
	rm -rf pkg
	$(DONE)

devbuild: prepare ## Build a dev version, bypassing mock (useful for debugging RPM build issues)
	rpmbuild -ba --define "%_topdir $(CWD)" --define "__version $(VERSION)" --define "__release $(BRANCH).$(COMMIT).$(BUILD_NUMBER)" $(CWD)/SPECS/$(NAME).spec
	$(DONE)

signrpm: ## Sign the rpm with the gpg key
	rpmsign --addsign $(CWD)/$(PKG)
	mv -f $(CWD)/$(PKG) pkg/
	$(DONE)

signrepo: ## Sign the repo key
	gpg --detach-sign --armor --yes repodata/repomd.xml
	$(DONE)
