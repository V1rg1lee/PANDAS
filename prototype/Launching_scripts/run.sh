#!/usr/bin/env bash
set -Eeuo pipefail

# Launch a GossipSub node process on the current Grid5000 host.
#
#   1 topology CSV
#   2 key directory
#   3 log directory   (passed to libp2p-das -log and used for sar logs)
#   4 local IP        (the IP for this Grid5000 host)
#   5 duration        (seconds)
#   6 experiment root (used for per-node stdout under Log/)

usage() {
    echo "Usage: $0 <topology.csv> <key_dir> <log_dir> <local_ip> <duration_s> <experiment_root>" >&2
}

die() {
    echo "run.sh: $*" >&2
    exit 1
}

if [ "$#" -lt 6 ]; then
    usage
    exit 1
fi

topo_file=$1
key_directory=$2
log_directory=$3
local_ip=$4
duration=$5
experiment_root=$6

case "$duration" in
    ''|*[!0-9]*) die "duration must be an integer number of seconds, got '$duration'" ;;
esac

[ -f "$topo_file" ] || die "topology file does not exist: $topo_file"
[ -d "$key_directory" ] || die "key directory does not exist: $key_directory"
[ -n "$local_ip" ] || die "local IP must not be empty"

source_dir=${GOSSIPSUB_SOURCE_DIR:-"$PWD"}
work_dir=${GOSSIPSUB_WORK_DIR:-"/tmp/gossipsub"}
binary_path=${GOSSIPSUB_BINARY_PATH:-"${work_dir}/libp2p-das"}
sleep_margin=${GOSSIPSUB_SLEEP_MARGIN:-15}
node_stdout_dir=${GOSSIPSUB_NODE_STDOUT_DIR:-"${experiment_root%/}/Log"}
gossip_topic=${GOSSIPSUB_TOPIC:-"gossipsub-smoke"}
gossip_interval=${GOSSIPSUB_INTERVAL:-5}
gossip_message_bytes=${GOSSIPSUB_MESSAGE_BYTES:-512}
connect_timeout=${GOSSIPSUB_CONNECT_TIMEOUT:-30}

case "$sleep_margin" in
    ''|*[!0-9]*) die "GOSSIPSUB_SLEEP_MARGIN must be an integer number of seconds, got '$sleep_margin'" ;;
esac
case "$gossip_interval" in
    ''|*[!0-9]*) die "GOSSIPSUB_INTERVAL must be an integer number of seconds, got '$gossip_interval'" ;;
esac
case "$gossip_message_bytes" in
    ''|*[!0-9]*) die "GOSSIPSUB_MESSAGE_BYTES must be an integer number of bytes, got '$gossip_message_bytes'" ;;
esac
case "$connect_timeout" in
    ''|*[!0-9]*) die "GOSSIPSUB_CONNECT_TIMEOUT must be an integer number of seconds, got '$connect_timeout'" ;;
esac

[ -d "$source_dir" ] || die "source directory does not exist: $source_dir"

if [ ! -f "${source_dir}/go.mod" ] && [ -f "${source_dir}/prototype/go.mod" ]; then
    source_dir="${source_dir}/prototype"
fi

mkdir -p "$log_directory" "$node_stdout_dir" || die "failed to create output directories"
[ -d "$log_directory" ] || die "log directory does not exist: $log_directory"
[ -d "$node_stdout_dir" ] || die "node stdout directory does not exist: $node_stdout_dir"

echo "========== Launch GossipSub =========="
echo "local_ip=${local_ip}"
echo "duration=${duration}s"
echo "source_dir=${source_dir}"
echo "work_dir=${work_dir}"

if [ "$source_dir" != "$work_dir" ]; then
    mkdir -p "$work_dir" || die "failed to create work directory: $work_dir"
    cp -a "${source_dir%/}/." "$work_dir/" || die "failed to copy source into work directory"
fi

cd "$work_dir"
[ -x "$binary_path" ] || die "expected executable binary does not exist: $binary_path"

if command -v systemctl >/dev/null 2>&1; then
    systemctl start sysstat >/dev/null 2>&1 || true
fi

if command -v sar >/dev/null 2>&1; then
    sar -A -o "${log_directory%/}/sar_logs_${local_ip}" 1 "$duration" >/dev/null 2>&1 &
else
    echo "run.sh: sar not found; continuing without sysstat capture" >&2
fi

started=0

while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue

    IFS=',' read -r nick port _csv_udp_port ip _csv_multiaddr _csv_role <<< "$line"

    if [ "$ip" != "$local_ip" ]; then
        continue
    fi

    key_file="${key_directory%/}/${ip}-${nick}.key"
    [ -f "$key_file" ] || die "key file does not exist for ${nick} at ${ip}: $key_file"

    "$binary_path" \
        -duration="$duration" \
        -ip="$ip" \
        -port="$port" \
        -debug=true \
        -nick="${nick}-${ip}" \
        -key="$key_file" \
        -log="$log_directory" \
        -node="$topo_file" \
        -gossipTopic="$gossip_topic" \
        -gossipInterval="$gossip_interval" \
        -gossipMessageBytes="$gossip_message_bytes" \
        -connTimeout="$connect_timeout" \
        >> "${node_stdout_dir}/${ip}-${nick}.txt" 2>&1 &
    started=$((started + 1))
done < "$topo_file"

[ "$started" -gt 0 ] || die "no topology rows matched local IP ${local_ip}"

sleep $((duration + sleep_margin))

fail=0
for job in $(jobs -p); do
    if ! wait "$job"; then
        fail=1
    fi
done

if [ "$fail" -eq 0 ]; then
    echo "All jobs finished successfully" >&2
else
    die "some jobs failed"
fi
