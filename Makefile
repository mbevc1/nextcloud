.PHONY: help clean clean-build clean-cache srpm rpm prepare devbuild signrpm signrepo build-docker pkg-docker clean-docker rm-docker docker-prepare docker-cleanup docker-test

.DEFAULT: help

ifndef VERBOSE
.SILENT:
endif

SHELL=bash
CWD:=$(shell pwd -P)
NAME=nextcloud
VERSION:=$(shell cat rpmbuild/SPECS/nextcloud.spec | grep "define base_version" | awk '{print $$3}')
BUILD_NUMBER?=DEV
DONE = echo -e "\e[31m✓\e[0m \e[33m$@\e[0m \e[32mdone\e[0m"
TOOLS="rpmdevtools mock"
NTOOLS:=$(shell rpm -qa "$(TOOLS)" | wc -l)
PKG:=$(shell if [ -d pkg ]; then ls pkg/$(NAME)-$(VERSION)*.noarch.rpm; else echo 0; fi)
# default
MOCK_CONFIG=epel-7-x86_64
NO_COLOR=\033[0m
GREEN=\033[32;01m
YELLOW=\033[33;01m
RED=\033[31;01m

help:: ## Show this help
	echo -e "\n$(NAME) packaging: Version \033[32m$(VERSION)\033[0m Release: \033[1m$(BUILD_NUMBER)\033[0m\n"
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-20s\033[0m %s\n", $$1, $$2}'

prepare: clean # $(NAME)-$(VERSION).tgz
ifneq ($(NTOOLS), 2)
	@yum install -y "$(TOOLS)"
endif
	mkdir -p SRPMS RPMS pkg
	spectool -C $(CWD)/rpmbuild/SOURCES/ -g $(CWD)/rpmbuild/SPECS/$(NAME).spec
	$(DONE)

srpm: prepare ## Build a source rpm
	mock --buildsrpm --spec=$(CWD)/rpmbuild/SPECS/$(NAME).spec --sources=$(CWD)/rpmbuild/SOURCES/ --resultdir=$(CWD)/rpmbuild/output --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)"
	rm -rf rpmbuild/output/*.log
	echo -e "Package saved to: \e[31m`ls rpmbuild/output/$(NAME)-$(VERSION)*.src.rpm`\e[0m"
	$(DONE)

minimalsrpm: prepare ## Build a source rpm
	mock --buildsrpm --spec=$(CWD)/rpmbuild/SPECS/$(NAME).spec --sources=$(CWD)/rpmbuild/SOURCES/ --resultdir=$(CWD)/rpmbuild/output --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)" --rpmbuild-opts "--without apache"
	rm -rf rpmbuild/output/*.log
	echo -e "Package saved to: \e[31m`ls rpmbuild/output/$(NAME)-$(VERSION)*.src.rpm`\e[0m"
	$(DONE)

rpm: srpm ## Build an rpm from the sourcerpm
	mock --rebuild $(CWD)/rpmbuild/output/$(NAME)*.src.rpm --resultdir=$(CWD)/rpmbuild/output --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)"
	cp rpmbuild/output/$(NAME)-$(VERSION)*.noarch.rpm pkg/
	echo -e "Package saved to: \e[31m`ls rpmbuild/output/$(NAME)-$(VERSION)*.noarch.rpm`\e[0m"
	$(DONE)

minimalrpm: minimalsrpm ## Build an rpm from the sourcerpm
	mock --rebuild $(CWD)/rpmbuild/output/$(NAME)*.src.rpm --resultdir=$(CWD)/rpmbuild/output --define "__version $(VERSION)" --define "__release $(BUILD_NUMBER)" --rpmbuild-opts "--without apache"
	cp rpmbuild/output/$(NAME)-$(VERSION)*.noarch.rpm pkg/
	echo -e "Package saved to: \e[31m`ls rpmbuild/output/$(NAME)-$(VERSION)*.noarch.rpm`\e[0m"
	$(DONE)

clean-package: ## Clean-up packaging
	$(DONE)

clean-build: ## Clean up the workspace
	rm -rf src rpmbuild/output rpmbuild/SOURCES/*.{gz,bz2}
	$(DONE)

clean: clean-build clean-cache ## Clean up also packages
	rm -rf pkg
	$(DONE)

clean-cache: ## Clean up mock cache
	rm -rf rpmbuild/cache
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

build-docker: ## Build docker image
	echo -e "==> $(YELLOW)Build Docker images$(NO_COLOR)"
	docker build --network host --pull --force-rm \
	    --build-arg UID=$$(id -u) \
	    -f Dockerfile -t mbevc1/$(NAME) \
            .
	$(DONE)

pkg-docker: build-docker clean-docker clean-build ## Package RPM using docker image
	echo -e "==> $(GREEN)Build the RPM package$(NO_COLOR)"
	mkdir -p pkg 
	# Build RPM package
	docker run --cap-add=SYS_ADMIN --network host \
	    -e MOCK_CONFIG=$(MOCK_CONFIG) -e SOURCES=SOURCES/ \
	    -e SPEC_FILE=SPECS/$(NAME).spec \
	    -e MOCK_DEFINES="VERSION=$(VERSION) RELEASE=$(BUILD_NUMBER) ANYTHING_ELSE=1" \
	    --rm -v ${PWD}/rpmbuild:/rpmbuild \
	    mbevc1/$(NAME)
	    #--workdir=/src
	echo -e "==> $(GREEN)Moving artifact $(RED)$$(basename $$(ls rpmbuild/output/$(MOCK_CONFIG)/*.noarch.rpm))$(GREEN) to $(YELLOW)pkg/$(GREEN) folder...$(NO_COLOR)"
	mv rpmbuild/output/$(MOCK_CONFIG)/*.noarch.rpm pkg/
	rm -rf rpmbuild/output/$(MOCK_CONFIG) rpmbuild/SOURCES/*.bz2
	$(DONE)

clean-docker: ## Clean-up unused docker images
	#docker rmi $$(docker images | grep "^<none>" | awk "{print $$3}")
	#if [ $$(docker ps -q --filter ancestor=$$(docker images -f dangling=true -q) | wc -l) -gt 0 ]; then echo "Cleaning up letftover containers!"; docker rm -f $$(docker ps -q --filter ancestor=$$(docker images -f dangling=true -q)); fi
	#if [ $$(docker images -f "dangling=true" -q | wc -l) -gt 0 ]; then docker rmi -f $$(docker images -f "dangling=true" -q); else echo "No orphan Docker images found ;)"; fi
	# Clean up leftover containers from old images
	docker container prune -f
	# Clean up old unused images
	docker image prune -f
	$(DONE)

rm-docker: ## Remove all docker images
	docker rmi -f $$(docker images -q -a)
	$(DONE)

# Not parallel safe to prepare
docker-prepare: build-docker clean-docker ## Prepare Docker container image

# Docker clean up
docker-cleanup: ## Run tests in a Docker container
	if [ $$(docker ps -qa --no-trunc --filter "status=exited" | wc -l) -ne 0 ]; then docker rm $$(docker ps -qa --no-trunc --filter "status=exited"); fi

# Test using Docker image and clean up
docker-test: ## Run tests in a Docker container
	echo -e "==> $(YELLOW)Running test: ${TEST} in Docker$(NO_COLOR)"
	docker run --network bridge -v ${PWD}:/src --workdir=/src -e LANG=en_US.UTF-8 \
            -e DB_DATABASE=${DB_DATABASE} -e DB_USERNAME=${DB_USERNAME} -e DB_PASSWORD=${DB_PASSWORD} \
            mbevc1/nextcloud make ${TEST}
	$(MAKE) docker-cleanup
	$(DONE)
