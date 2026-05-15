#!/usr/bin/env bash
set -Eeuo pipefail

# Build the GossipSub/PANDAS binary expected by run.sh.

die() {
    echo "server_install.sh: $*" >&2
    exit 1
}

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <login>" >&2
    exit 1
fi

echo "========== Prerequisites Install =========="

login=$1
source_dir=${PANDAS_SOURCE_DIR:-"/home/${login}/PANDAS"}
go_version=${PANDAS_GO_VERSION:-"1.21.6"}
go_tarball="go${go_version}.linux-amd64.tar.gz"
go_url="https://go.dev/dl/${go_tarball}"

[ -d "$source_dir" ] || die "source directory does not exist: $source_dir"

sudo-g5k

if ! command -v go >/dev/null 2>&1; then
    cd /tmp
    if [ ! -f "$go_tarball" ]; then
        wget "$go_url"
    fi
    sudo tar -C /usr/local -xzf "$go_tarball"
fi

export PATH=$PATH:/usr/local/go/bin
command -v go >/dev/null 2>&1 || die "go is not available after installation"

if [ ! -f "${source_dir}/go.mod" ] && [ -f "${source_dir}/prototype/go.mod" ]; then
    source_dir="${source_dir}/prototype"
fi

[ -f "${source_dir}/go.mod" ] || die "go.mod not found in $source_dir"

cd "$source_dir"
go build -o libp2p-das .
[ -x "${source_dir}/libp2p-das" ] || die "failed to build expected binary: ${source_dir}/libp2p-das"
