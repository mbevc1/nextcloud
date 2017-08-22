#
# spec file for package nextcloud
#
# Author: Marko Bevc <marko.bevc@gmail.com>
# Based on SuSE packaging: https://build.opensuse.org/package/show/server:php:applications/nextcloud
#

%if 0%{?fedora_ver} || 0%{?rhel_ver} || 0%{?centos_ver}
%define apache_serverroot /var/www/html
%define apache_confdir /etc/httpd/conf.d
%define apache_user apache
%define apache_group apache
%define __jar_repack 0
%else
%define apache_serverroot /var/www
%define apache_confdir /etc/httpd/conf.d
%define apache_user www
%define apache_group www
%endif

%define oc_user 	%{apache_user}
%define oc_dir  	%{apache_serverroot}/%{name}
%define ocphp_bin	/usr/bin

%if 0%{?rhel} == 600 || 0%{?rhel_version} == 600 || 0%{?centos_version} == 600
%define statedir	/var/run
%else
%define statedir	/run
%endif

%define base_version 12.0.2
%define rel %(echo 2)

Name:           nextcloud
Version:        %{base_version}
Release:        %{rel}%{?dist}
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

%prep
%setup -q -n %{name}
cp %{SOURCE2} .
cp %{SOURCE3} .
cp %{SOURCE4} .
#cp %{SOURCE5} .
#%%patch0 -p0
# git files should not be removed, otherwise nextcloud rise up ntegrity check failure.
#rm `find . -name ".gitignore" -or -name ".gitkeep"`
# delete unneeded gitfiles 
rm -r `find . -name ".gitignore" -or -name ".gitkeep" -or -name ".github"`
# remove entries in signature.json to prevent integrity check failure
find . -iname signature.json \
    -exec sed -i "/\/.gitignore\": ./d" "{}" \;  \
    -exec sed -i "/\/.gitkeep\": ./d" "{}" \; \
    -exec sed -i "/\/.github\": ./d" "{}" \;

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

# create the AllowOverride directive
install -p -D -m 644 %{SOURCE1} $RPM_BUILD_ROOT/%{apache_confdir}/nextcloud.conf
ocpath="%{apache_serverroot}/%{name}"
sed -i -e"s|@DATAPATH@|${ocpath}|g" $RPM_BUILD_ROOT/%{apache_confdir}/nextcloud.conf

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

%files
%defattr(644,root,root,755)
%exclude %{apache_serverroot}/%{name}/README
%exclude %{apache_serverroot}/%{name}/README.SELinux
%doc README README.SELinux
#%{apache_serverroot}/%{name}
%attr(-,%{apache_user},%{apache_group}) %{apache_serverroot}/%{name}/occ
%{apache_serverroot}/%{name}/3rdparty
%{apache_serverroot}/%{name}/core
%{apache_serverroot}/%{name}/l10n
%{apache_serverroot}/%{name}/lib
%{apache_serverroot}/%{name}/ocs
%{apache_serverroot}/%{name}/ocs-provider
%{apache_serverroot}/%{name}/resources
%{apache_serverroot}/%{name}/settings
%{apache_serverroot}/%{name}/themes
%{apache_serverroot}/%{name}/updater
%{apache_serverroot}/%{name}/AUTHORS
%{apache_serverroot}/%{name}/db_structure.xml
%{apache_serverroot}/%{name}/*.php
%{apache_serverroot}/%{name}/index.html
%{apache_serverroot}/%{name}/robots.txt
%{apache_serverroot}/%{name}/.htaccess
%config(noreplace) %{apache_confdir}/nextcloud.conf
%config(noreplace) %{apache_serverroot}/%{name}/.user.ini
%defattr(664,%{apache_user},%{apache_group},775)
%{apache_serverroot}/%{name}/apps
%defattr(660,%{apache_user},%{apache_group},770)
%attr(770,,%{apache_user},%{apache_group}) %{apache_serverroot}/%{name}/config
%{apache_serverroot}/%{name}/data

%changelog

