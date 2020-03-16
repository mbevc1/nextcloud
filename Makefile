.DEFAULT: help

ifndef VERBOSE
.SILENT:
endif

SHELL=bash
CWD:=$(shell pwd -P)
NAME=nextcloud
VERSION:=$(shell cat nextcloud.spec | grep "define base_version" | awk '{print $$3}')
BUILD_NUMBER?=1
RELEASE?=$(BUILD_NUMBER)

SPEC:=$(shell ls *.spec)
PKG:=$(shell if [ -d pkg ]; then ls pkg/$(NAME)-$(VERSION)*.noarch.rpm; else echo 0; fi)

DONE = echo -e "\e[31m✓\e[0m \e[33m$@\e[0m \e[32mdone\e[0m"
NO_COLOR=\033[0m
GREEN=\033[32;01m
YELLOW=\033[33;01m
RED=\033[31;01m

SYS_ID_U := $(shell id -u)
ID_U ?= $(SYS_ID_U)
SYS_ID_G := $(shell id -g)
ID_G ?= $(SYS_ID_G)

ifeq ($(BUILD_ENVIRONMENT),ci)
    DOCKER := docker
    DOCKER_OPTS := -i #-u $(ID_U)
else
    DOCKER := docker
    DOCKER_OPTS := -it #-u $(ID_U)
endif

DOCKER_NET := --network host

ifdef SELINUX
    MOUNT = $(CURDIR):/src:Z
else
    MOUNT = $(CURDIR):/src
endif

IMAGE ?= rpmbuild
REGISTRY ?= mbevc1
IMG_NAME := $(REGISTRY)/$(IMAGE)

# Try to fetch branch info from git, if not provided
BRANCHTAG:=$(or $(TAG),$(shell if [ -d .git ]; then git describe --all --exact-match 2>/dev/null | sed 's=.*/=='; else echo 0; fi))

ifeq (, $(shell which docker))
    $(error "No docker in $(PATH), consider doing yum/dnf install -y docker")
endif

.PHONY: help
help:: ## Show this help
	echo -e "\n$(NAME) packaging: Version \033[32m$(VERSION)\033[0m Release: \033[1m$(BUILD_NUMBER)\033[0m\n"
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: ## Clean up also packages
	echo -e "==> $(GREEN)Cleaning up packages$(NO_COLOR)"
	rm -rf pkg
	$(DONE)

.PHONY: devbuild
devbuild: prepare ## Build a dev version, bypassing mock (useful for debugging RPM build issues)
	rpmbuild -ba --define "%_topdir $(CWD)" --define "__version $(VERSION)" --define "__release $(BRANCH).$(COMMIT).$(BUILD_NUMBER)" $(CWD)/$(SPEC)
	$(DONE)

.PHONY: signrpm
signrpm: ## Sign the rpm with the gpg key
	rpmsign --addsign $(CWD)/$(PKG)
	mv -f $(CWD)/$(PKG) pkg/
	$(DONE)

.PHONY: signrepo
signrepo: ## Sign the repo key
	gpg --detach-sign --armor --yes repodata/repomd.xml
	$(DONE)

.PHONY: pull
pull: ## Update Docker image from repository
	echo -e "==> $(GREEN)Update Docker image $(IMG_NAME) from registry$(NO_COLOR)"
	$(DOCKER) pull $(IMG_NAME)
	$(DONE)

.PHONY: package
package: pull clean-docker ## Build RPM package
	@echo "==> $(GREEN)Build the RPM package$(NO_COLOR)"
	# Build RPM package
	$(DOCKER) run --rm $(DOCKER_NET) -e VERBOSE=0 \
	    -e VERSION=$(VERSION) \
	    -e RELEASE=$(RELEASE) \
	    --rm -v $(MOUNT) --workdir=/src \
	    $(IMG_NAME) $(SPEC) pkg
	$(DONE)

.PHONY: clean-docker
clean-docker: ## Clean-up unused docker bits
	echo -e "==> $(YELLOW)Clean Docker system$(NO_COLOR)"
	#docker rmi $$(docker images | grep "^<none>" | awk "{print $$3}")
	#if [ $$(docker ps -q --filter ancestor=$$(docker images -f dangling=true -q) | wc -l) -gt 0 ]; then echo "Cleaning up letftover containers!"; docker rm -f $$(docker ps -q --filter ancestor=$$(docker images -f dangling=true -q)); fi
	#if [ $$(docker images -f "dangling=true" -q | wc -l) -gt 0 ]; then docker rmi -f $$(docker images -f "dangling=true" -q); else echo "No orphan Docker images found ;)"; fi
	# Clean up leftover containers from old images
	#docker container prune -f
	# Clean up old unused images
	#docker image prune -f
	docker system prune -f
	$(DONE)
