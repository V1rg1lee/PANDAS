#!/usr/bin/env bash

set -e

# Variables
GO_INSTALL_DIR="/usr/local"
PROFILE_FILE="$HOME/.bashrc"

# Reload profile
source ${PROFILE_FILE}
wget "https://go.dev/dl/go1.21.6.linux-amd64.tar.gz"
sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
# Verify installation
source ${PROFILE_FILE}
go version
