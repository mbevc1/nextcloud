#
# spec file for package nextcloud
#
# Author: Marko Bevc <marko.bevc@gmail.com>
# Based on SuSE packaging: https://build.opensuse.org/package/show/server:php:applications/nextcloud
#

%{!?_with_apache: %{!?_without_apache: %define _with_apache --with-apache}}

%if 0%{?fedora_ver} || 0%{?rhel_ver} || 0%{?centos_ver}
%define apache_serverroot /var/www/html
%define apache_confdir /etc/httpd/conf.d
%define apache_user apache
%define apache_group apache
%define __jar_repack 0
%define _binary_payload w9.xzdio
%else
%define apache_serverroot /var/www
%define apache_confdir /etc/httpd/conf.d
%define apache_user www
%define apache_group www
%endif

%define oc_user         %{apache_user}
%define oc_dir          %{apache_serverroot}/%{name}
%define ocphp_bin	/usr/bin

%if 0%{?rhel} == 600 || 0%{?rhel_version} == 600 || 0%{?centos_version} == 600
%define statedir	/var/run
%else
%define statedir	/run
%endif

%{!?_version: %define _version 21.0.0}
%{!?_release: %define _release 1}

%define rel %(echo 1)

Name:           nextcloud
Version:        %{_version}
Release:        %{_release}%{?dist}
Summary:        File hosting service
License:        AGPL-3.0
Group:          Productivity/Networking/Web/Utilities
Url:            http://www.nextcloud.com
Source0:        https://download.nextcloud.com/server/releases/%{name}-%{version}.tar.bz2
Source1:        apache_secure_data
Source2:        README
Source3:        README.SELinux
Source4:        robots.txt
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

# For the systemd macros
%{?systemd_requires}
BuildRequires:  systemd

BuildRequires:  unzip
#
Requires:       curl
Requires:       mysql
Requires:       php-gd
Requires:       php-json
Requires:       php-mbstring
Requires:       php-mysqlnd
Requires:       php-posix
Requires:       php-zip
#
%if 0%{?fedora_version} || 0%{?rhel} || 0%{?rhel_version} || 0%{?centos_version}
Requires:       php >= 5.6.0
Requires:       php-process
Requires:       php-xml
#
#Recommends:     sqlite
%endif
#
#
#Recommends:     php-imagick
#Recommends:     php-sqlite

%description
Nextcloud is a suite of client-server software for creating file
hosting services and using them.
It gives you universal access to your files through a web interface or
WebDAV. It also provides a platform to easily view & sync your contacts,
calendars and bookmarks across all your devices and enables basic editing right
on the web. NextCloud is extendable via a simple but powerful API for
applications and plugins.

%prep
%setup -q -n %{name}
cp %{SOURCE2} .
cp %{SOURCE3} .
cp %{SOURCE4} .

%build

%install
idir=$RPM_BUILD_ROOT/%{apache_serverroot}/%{name}
mkdir -p $idir
mkdir -p $idir/data
mkdir -p $idir/search
cp -aRf * $idir
cp -aRf .htaccess $idir
cp -aRf .user.ini $idir
# $idir/l10n to disappear in future
#rm -f $idir/l10n/l10n.pl

if [ ! -f $idir/robots.txt ]; then
  install -p -D -m 644 %{SOURCE4} $idir/robots.txt
fi

%if %{?_with_apache:1}%{!?_with_apache:0}

# create the AllowOverride directive
install -p -D -m 644 %{SOURCE1} $RPM_BUILD_ROOT/%{apache_confdir}/nextcloud.conf
ocpath="%{apache_serverroot}/%{name}"
sed -i -e"s|@DATAPATH@|${ocpath}|g" $RPM_BUILD_ROOT/%{apache_confdir}/nextcloud.conf

%endif

# not needed for distro packages
rm -f ${idir}/indie.json

%pre
# avoid fatal php errors, while we are changing files
# https://github.com/nextcloud
#
# We don't do this for new installs. Only for updates.
# If the first argument to pre is 1, the RPM operation is an initial installation. If the argument is 2,
# the operation is an upgrade from an existing version to a new one.
if [ $1 -gt 1 -a ! -s %{statedir}/apache_stopped_during_nextcloud_install ]; then
  echo "%{name} update: Checking for running Apache"
  # FIXME: this above should make it idempotent --
  # it does not work.
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
  service httpd status | grep running > %{statedir}/apache_stopped_during_nextcloud_install
  service httpd stop
%endif
fi
if [ -s %{statedir}/apache_stopped_during_nextcloud_install ]; then
  echo "%{name} pre-install: Stopping Apache"
fi

if [ $1 -eq 1 ]; then
    echo "%{name}-server: First install starting"
else
    echo "%{name}-server: installing upgrade ..."
fi
# https://github.com/nextcloud
if [ -x %{ocphp_bin}/php -a -f %{oc_dir}/occ ]; then
  echo "%{name}: occ maintenance:mode --on"
  su %{oc_user} -s /bin/sh -c "cd %{oc_dir}; PATH=%{ocphp_bin}:$PATH php ./occ maintenance:mode --on" || true
  echo yes > %{statedir}/occ_maintenance_mode_during_nextcloud_install
fi

%post
if [ $1 -eq 1 ]; then
    echo "%{name} First install complete"
else
    echo "%{name} Upgrade complete"
fi

if [ -s %{statedir}/apache_stopped_during_nextcloud_install ]; then
  echo "%{name} post-install: Restarting Apache"
  ## If we stopped apache in pre section, we now should restart. -- but *ONLY* then!
  ## Maybe delegate that task to occ upgrade? They also need to handle this, somehow.
%if 0%{?fedora_version} || 0%{?rhel_version} || 0%{?centos_version}
  service httpd start
%endif
fi

if [ -s %{statedir}/occ_maintenance_mode_during_nextcloud_install ]; then
echo "%{name}: occ upgrade"
su %{oc_user} -s /bin/sh -c "cd %{oc_dir}; PATH=%{ocphp_bin}:$PATH php ./occ upgrade" || true
echo "%{name}: occ maintenance:mode --off"
su %{oc_user} -s /bin/sh -c "cd %{oc_dir}; PATH=%{ocphp_bin}:$PATH php ./occ maintenance:mode --off" || true
fi

rm -f %{statedir}/apache_stopped_during_nextcloud_install
rm -f %{statedir}/occ_maintenance_mode_during_nextcloud_install

# the selinux policies only cover owncloud right now
# once this package is accepted pull request for selinux-policy to add
# these will be made
#semanage fcontext -a -t httpd_sys_rw_content_t '%{_sysconfdir}/%{name}/config.php' 2>/dev/null || :
#semanage fcontext -a -t httpd_sys_rw_content_t '%{_sysconfdir}/%{name}' 2>/dev/null || :
#semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name}(/.*)?' 2>/dev/null || :
#restorecon -R %{_sysconfdir}/%{name} || :
#restorecon -R %{_localstatedir}/lib/%{name} || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{oc_dir}/data(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{oc_dir}/config(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{oc_dir}/apps(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{oc_dir}/.htaccess' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{oc_dir}/.user.ini' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_content_t '%{oc_dir}/3rdparty(/.*)?' 2>/dev/null || :

restorecon -Rv '%{oc_dir}' || :

%postun
if [ $1 -eq 0  ] ; then
#semanage fcontext -d -t httpd_sys_rw_content_t '%{_sysconfdir}/%{name}/config.php' 2>/dev/null || :
#semanage fcontext -d -t httpd_sys_rw_content_t '%{_sysconfdir}/%{name}' 2>/dev/null || :
#semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name}(/.*)?' 2>/dev/null || :
semanage fcontext -d '%{oc_dir}/data(/.*)?'
semanage fcontext -d '%{oc_dir}/config(/.*)?'
semanage fcontext -d '%{oc_dir}/apps(/.*)?'
semanage fcontext -d '%{oc_dir}/.htaccess'
semanage fcontext -d '%{oc_dir}/.user.ini'
semanage fcontext -d '%{oc_dir}/3rdparty(/.*)?'

restorecon -Rv '%{oc_dir}' || :
fi

%files
%defattr(644,root,root,755)
%exclude %{apache_serverroot}/%{name}/README
%exclude %{apache_serverroot}/%{name}/README.SELinux
%doc README README.SELinux
%dir %{apache_serverroot}/%{name}
%attr(755,%{apache_user},%{apache_group}) %{apache_serverroot}/%{name}/occ
%{apache_serverroot}/%{name}/3rdparty
%{apache_serverroot}/%{name}/core
%{apache_serverroot}/%{name}/lib
%{apache_serverroot}/%{name}/ocs
%{apache_serverroot}/%{name}/ocs-provider
%{apache_serverroot}/%{name}/ocm-provider
%{apache_serverroot}/%{name}/resources
%{apache_serverroot}/%{name}/themes
%{apache_serverroot}/%{name}/updater
%{apache_serverroot}/%{name}/AUTHORS
%{apache_serverroot}/%{name}/COPYING
%{apache_serverroot}/%{name}/*.php
%{apache_serverroot}/%{name}/index.html
%{apache_serverroot}/%{name}/robots.txt
%{apache_serverroot}/%{name}/.htaccess
%if %{?_with_apache:1}%{!?_with_apache:0}
%config(noreplace) %{apache_confdir}/nextcloud.conf
%endif
%config(noreplace) %{apache_serverroot}/%{name}/.user.ini
%defattr(664,%{apache_user},%{apache_group},775)
%{apache_serverroot}/%{name}/apps
%defattr(660,%{apache_user},%{apache_group},770)
%attr(770,,%{apache_user},%{apache_group}) %{apache_serverroot}/%{name}/config
%{apache_serverroot}/%{name}/data

%changelog
* Thu  Feb 25 2021 Kris Buytaert <kris@inuits.eu> - 21.0.0
- Update major version 

* Mon Jan 04 2021 Marko Bevc <marko@bevc.net> - 20.0.x
- Update minor version and upstream fixes.

* Fri Dec 18 2020 Marko Bevc <marko@bevc.net> - 20.0.4-1
- Update minor version and upstream fixes.

* Thu Dec 10 2020 Marko Bevc <marko@bevc.net> - 20.0.3-1
- Update minor version and upstream fixes.

* Mon Nov 23 2020 Marko Bevc <marko@bevc.net> - 20.0.2-1
- Update minor version and upstream fixes.

* Mon Oct 26 2020 Marko Bevc <marko@bevc.net> - 20.0.1-1
- Update minor version and upstream fixes.

* Fri Oct 09 2020 Marko Bevc <marko@bevc.net> - 20.0.0-1
- Update major version.

* Fri Sep 11 2020 Marko Bevc <marko@bevc.net> - 19.0.3-1
- Update minor version and upstream fixes.

* Thu Aug 27 2020 Marko Bevc <marko@bevc.net> - 19.0.2-1
- Update minor version and upstream fixes.

* Fri Jul 17 2020 Marko Bevc <marko@bevc.net> - 19.0.1-1
- Update minor version and upstream fixes.

* Fri Jun 12 2020 Marko Bevc <marko@bevc.net> - 19.0.0-1
- Update major version.

* Tue Jun 09 2020 Marko Bevc <marko@bevc.net> - 18.0.6-1
- Update minor version and upstream bug fixes.

* Tue Apr 28 2020 Marko Bevc <marko@bevc.net> - 18.0.4-1
- Update version and upstream bug fixes.

* Sat Mar 28 2020 Marko Bevc <marko@bevc.net> - 18.0.3-1
- Update version and upstream bug fixes.

* Mon Mar 16 2020 Marko Bevc <marko@bevc.net> - 18.0.2-1
- Major version bump https://nextcloud.com/changelog/#latest18.

* Mon Mar 16 2020 Marko Bevc <marko@bevc.net> - 17.0.4-1
- Update version and upstream bug fixes.

* Mon Feb 10 2020 Marko Bevc <marko@bevc.net> - 17.0.3-1
- Update version and upstream bug fixes.

* Sat Jan 04 2020 Marko Bevc <marko@bevc.net> - 17.0.2-1
- Update version and upstream bug fixes.

* Mon Nov 11 2019 Marko Bevc <marko@bevc.net> - 17.0.1-1
- Update version and upstream bug fixes.

* Mon Oct 14 2019 Marko Bevc <marko@bevc.net> - 17.0.0-1
- Update major version https://nextcloud.com/changelog/#latest17 and upstream
  bug fixes.

* Sun Oct 13 2019 Marko Bevc <marko@bevc.net> - 16.0.5-1
- Update version and upstream bug fixes.

* Wed Aug 28 2019 Marko Bevc <marko@bevc.net> - 16.0.4-1
- Update version and bug fixes.

* Wed Jul 10 2019 Marko Bevc <marko@bevc.net> - 16.0.3-1
- Update version and minor fixes.

* Mon Jul 08 2019 Marko Bevc <marko@bevc.net> - 16.0.2-1
- Update version.

* Mon May 20 2019 Marko Bevc <marko@bevc.net> - 16.0.1-1
- Update version.

* Mon May 6 2019 Marko Bevc <marko@bevc.net> - 16.0.0-1
- Update version.

* Mon May 6 2019 Marko Bevc <marko@bevc.net> - 15.0.7-1
- Update version.

* Fri Apr 5 2019 Marko Bevc <marko@bevc.net> - 15.0.6-1
- Update version.

* Mon Mar 4 2019 Marko Bevc <marko@bevc.net> - 15.0.5-1
- Update version.

* Mon Feb 11 2019 Marko Bevc <marko@bevc.net> - 15.0.4-1
- Update version.

* Mon Jan 14 2019 Marko Bevc <marko@bevc.net> - 15.0.2-1
- Update version.

* Thu Jan 10 2019 Marko Bevc <marko@bevc.net> - 15.0.1-1
- Update version.

* Thu Jan 10 2019 Marko Bevc <marko@bevc.net> - 14.0.5-1
- Update version.

* Thu Jan 10 2019 Marko Bevc <marko@bevc.net> - 13.0.9-1
- Update version.

* Tue Nov 27 2018 Marko Bevc <marko@bevc.net> - 14.0.4-1
- Update version.

* Sat Oct 13 2018 Marko Bevc <marko@bevc.net> - 13.0.7-1
- Update version 13.

* Fri Oct 12 2018 Marko Bevc <marko@bevc.net> - 14.0.3-1
- Update to latest version.

* Thu Oct 04 2018 Marko Bevc <marko@bevc.net> - 14.0.1-1
- Update to version 14.

* Thu Oct 04 2018 Marko Bevc <marko@bevc.net> - 13.0.6-2
- Switch to Docker build.

* Sun Sep 02 2018 Marko Bevc <marko@bevc.net> - 13.0.6-1
- Update version.

* Fri Aug 03 2018 Marko Bevc <marko@bevc.net> - 13.0.5-1
- Update version.

* Tue Jun 12 2018 Marko Bevc <marko@bevc.net> - 13.0.4-1
- Update version.

* Mon Apr 30 2018 Marko Bevc <marko@bevc.net> - 13.0.2-1
- Update version.

* Fri Mar 23 2018 Marko Bevc <marko@bevc.net> - 13.0.1-1
- Update version.

* Thu Mar 08 2018 Marko Bevc <marko@bevc.net> - 13.0.0-1
- Update version.

* Fri Jan 26 2018 Marko Bevc <marko@bevc.net> - 12.0.5-1
- Update version.

* Wed Dec 13 2017 Marko Bevc <marko@bevc.net> - 12.0.4-2
- Update SELinux context.

