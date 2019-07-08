FROM centos:7
LABEL maintainer="DevOps <ops@bevc.net>"

ARG UNAME=builder
ARG UID=1000

RUN yum -y --setopt="tsflags=nodocs" update && \
	yum -y --setopt="tsflags=nodocs" install epel-release mock rpm-sign expect \
        bash ca-certificates git make yum-utils rpmdevtools && \
	yum clean all && \
	rm -rf /var/cache/yum/

#Configure users
RUN useradd -u $UID -G mock $UNAME && \
	chmod g+w /etc/mock/*.cfg

VOLUME ["/rpmbuild"]

ONBUILD COPY mock /etc/mock
ADD ./site-defaults-extra.cfg /etc/mock/

# create mock cache on external volume to speed up build
RUN install -g mock -m 2775 -d /rpmbuild/cache/mock
RUN echo "config_opts['cache_topdir'] = '/rpmbuild/cache/mock'" >> /etc/mock/site-defaults.cfg

RUN cat /etc/mock/site-defaults-extra.cfg >> /etc/mock/site-defaults.cfg

ADD ./build-rpm.sh /build-rpm.sh
RUN chmod +x /build-rpm.sh
#RUN setcap cap_sys_admin+ep /usr/sbin/mock
ADD ./rpm-sign.exp /rpm-sign.exp
RUN chmod +x /rpm-sign.exp

USER $UNAME
ENV HOME /home/$UNAME
CMD ["/build-rpm.sh"]
