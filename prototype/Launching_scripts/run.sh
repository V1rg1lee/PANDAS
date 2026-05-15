#!/usr/bin/env bash
set -Eeuo pipefail

# Launch a GossipSub/PANDAS node process on the current Grid5000 host.
#
# Arguments kept for compatibility with experiment_launch.py:
#   1 topology CSV
#   2 num_blocks      (currently unused by libp2p-das)
#   3 key directory
#   4 log directory   (passed to libp2p-das -log and used for sar logs)
#   5 local IP        (the IP for this Grid5000 host)
#   6 duration        (seconds)
#   7 Grid5000 login
#   8 builder_ip      (currently unused by libp2p-das)
#   9 experiment root (used for per-node stdout under Log/)
#
# Optional for the first validation run:
#   tc_config.py and tracer.sh are not invoked here. Run them separately only
#   when latency shaping or pubsub tracing is needed.

usage() {
    echo "Usage: $0 <topology.csv> <num_blocks-unused> <key_dir> <log_dir> <local_ip> <duration_s> <login> <builder_ip-unused> <experiment_root>" >&2
}

die() {
    echo "run.sh: $*" >&2
    exit 1
}

if [ "$#" -lt 9 ]; then
    usage
    exit 1
fi

topo_file=$1
num_blocks=$2
key_directory=$3
log_directory=$4
local_ip=$5
duration=$6
login=$7
builder_ip=$8
experiment_root=$9

# Compatibility-only values. They document the legacy argument contract without
# pretending to configure the current binary.
: "$num_blocks" "$builder_ip"

case "$duration" in
    ''|*[!0-9]*) die "duration must be an integer number of seconds, got '$duration'" ;;
esac

[ -f "$topo_file" ] || die "topology file does not exist: $topo_file"
[ -d "$key_directory" ] || die "key directory does not exist: $key_directory"
[ -n "$login" ] || die "login must not be empty"
[ -n "$local_ip" ] || die "local IP must not be empty"

source_dir=${PANDAS_SOURCE_DIR:-"/home/${login}/PANDAS"}
work_dir=${PANDAS_WORK_DIR:-"/tmp/PANDAS"}
binary_path=${PANDAS_BINARY_PATH:-"${work_dir}/libp2p-das"}
sleep_margin=${PANDAS_SLEEP_MARGIN:-15}
node_stdout_dir=${PANDAS_NODE_STDOUT_DIR:-"${experiment_root%/}/Log"}

case "$sleep_margin" in
    ''|*[!0-9]*) die "PANDAS_SLEEP_MARGIN must be an integer number of seconds, got '$sleep_margin'" ;;
esac

[ -d "$source_dir" ] || die "source directory does not exist: $source_dir"

if [ ! -f "${source_dir}/go.mod" ] && [ -f "${source_dir}/prototype/go.mod" ]; then
    source_dir="${source_dir}/prototype"
fi

mkdir -p "$log_directory" "$node_stdout_dir" || die "failed to create output directories"
[ -d "$log_directory" ] || die "log directory does not exist: $log_directory"
[ -d "$node_stdout_dir" ] || die "node stdout directory does not exist: $node_stdout_dir"

echo "========== Launch GossipSub/PANDAS =========="
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

    IFS=',' read -r nick port udp_port ip _rest <<< "$line"
    node_type=${line##*,}

    if [ "$ip" != "$local_ip" ]; then
        continue
    fi

    key_file="${key_directory%/}/${ip}-${nick}.key"
    [ -f "$key_file" ] || die "key file does not exist for ${nick} at ${ip}: $key_file"

    "$binary_path" \
        -UDPport="$udp_port" \
        -duration="$duration" \
        -ip="$ip" \
        -port="$port" \
        -nodeType="$node_type" \
        -debug=true \
        -nick="${nick}-${ip}" \
        -key="$key_file" \
        -log="$log_directory" \
        -node="$topo_file" \
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
