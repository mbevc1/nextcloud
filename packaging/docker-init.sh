#!/bin/bash

set -e ${VERBOSE:+-x}

BUILD=true
if [[ "$1" == "--sh" ]]; then
    BUILD=false
    shift
fi

SPEC="${1}"
OUTDIR="${2:-$PWD}"
if [[ -z ${SPEC} || ! -e ${SPEC} ]]; then
    echo "Usage: docker run [--rm]" \
        "--volume=/path/to/source:/src --workdir=/src" \
        "rpmbuild [--sh] SPECFILE [OUTDIR=.] | SPEC: ${1} OUTDIR: ${2}" >&2
    exit 2
fi

# pre-builddep hook for adding extra repos
if [[ -n ${PRE_BUILDDEP} ]]; then
    bash ${VERBOSE:+-x} -c "${PRE_BUILDDEP}"
fi

TOPDIR=$(eval echo "~builder/rpm")
if [ -d src ]; then
    cp ${VERBOSE:+-v} -a --reflink=auto src/* "${TOPDIR}/"
fi
cp ${VERBOSE:+-v} -a --reflink=auto "${SPEC}" "${TOPDIR}/"
chown builder. /home/builder -R

# install build dependencies declared in the specfile
yum-builddep -y "${SPEC}"
#spectool -g -R ${SPEC}
#rpmbuild -ba ${SPEC}

# drop to the shell for debugging manually
if ! ${BUILD}; then
    exec "${SHELL:-/bin/bash}" -l
fi

# execute the build as rpmbuild user
runuser builder /usr/local/bin/docker-rpm-build.sh "$@"

# copy the results back; done as root as builder most likely doesn't
# have permissions for OUTDIR; ensure ownership of output is consistent
# with source so that the caller of this image doesn't run into
# permission issues
mkdir -p "${OUTDIR}"
cp ${VERBOSE:+-v} -a --reflink=auto \
    ~builder/rpm/pkg/*.rpm "${OUTDIR}/"

TO_CHOWN=( "${OUTDIR}/" )
if [[ ${OUTDIR} != ${PWD} ]]; then
    TO_CHOWN=( "${OUTDIR}" )
fi

chown ${VERBOSE:+-v} -R --reference="${PWD}" "${TO_CHOWN[@]}"
