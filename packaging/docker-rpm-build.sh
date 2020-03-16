#!/bin/bash

set -e ${VERBOSE:+-x}

SPEC="${1:?}"
TOPDIR="${HOME}/rpm"

# copy sources and spec into rpmbuild's work dir
#cp "${VERBOSE:+-v}" -a --reflink=auto src/* "${TOPDIR}/SOURCES/"
#cp "${VERBOSE:+-v}" -a --reflink=auto "${SPEC}" "${TOPDIR}/SPECS/"
#SPEC="${TOPDIR}/SPECS/${SPEC##*/}"

#if [ -d src ]; then
#    cp ${VERBOSE:+-v} -a --reflink=auto src/* "${TOPDIR}/"
#fi
#cp ${VERBOSE:+-v} -a --reflink=auto "${SPEC}" "${TOPDIR}/"

cd ${TOPDIR}
spectool -g -R ${SPEC}

# build the RPMs
rpmbuild ${VERBOSE:+-v} --define "debug_package %{nil}" \
    --define "_build_name_fmt %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" \
    --define "_version ${VERSION}" --define "_release ${RELEASE}" \
    -ba "${SPEC}"
