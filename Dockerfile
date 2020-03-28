# vim:ft=dockerfile
ARG VER=8
FROM centos:$VER AS builder
LABEL maintainer="DevOps <ops@bevc.net>"

RUN yum update -y && yum clean all && rm -rf /var/cache/{yum,dnf}
