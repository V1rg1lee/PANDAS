# GossipSub - Grid5000 20-node scoring experiment

This document records the command sequence used to launch a minimal real
libp2p GossipSub deployment on Grid5000 with 20 nodes, peer scoring enabled,
and 20% degraded peers.

Goal:
- reserve 20 Grid5000 nodes;
- mark 16 nodes as honest and 4 nodes as degraded;
- launch libp2p GossipSub with explicit mesh parameters;
- make degraded peers publish invalid messages and drop some received messages;
- collect GossipSub JSON traces, score snapshots, logs, and topology metrics.

---

## 1. Connect to Grid5000

From the local machine:
```sh
ssh g5k
```

Then connect to the <city> site frontend:
```sh
ssh <city>
```

---

## 2. Clone the repository on the site frontend

Do not clone the repository directly on access.grid5000.fr.

On the site frontend:
```sh
cd ~
git clone https://github.com/V1rg1lee/GossipSub-Minimal.git
cd ~/GossipSub-Minimal/prototype
```

---

## 3. Reserve 20 nodes

From the site frontend:
```sh
oarsub -I -l nodes=20,walltime=0:45:00
```

Inside the OAR interactive session:
```sh
hostname
echo "$OAR_NODEFILE"
cat "$OAR_NODEFILE"
```

---

## 4. Define experiment variables

```sh
LOGIN=$USER
NODE_COUNT=20
DEGRADED_PERCENT=20
DEGRADED_COUNT=$(((NODE_COUNT * DEGRADED_PERCENT + 99) / 100))
HONEST_COUNT=$((NODE_COUNT - DEGRADED_COUNT))

SRC=/home/$LOGIN/GossipSub-Minimal/prototype
EXP=/home/$LOGIN/results/gossipsub-scoring-$(date +%Y%m%d-%H%M%S)
NODES=$EXP/NodesFiles/nodes.csv
KEYS=$EXP/NodesFiles/keys
RESULTS=$EXP/results
TOPIC=gossipsub-scoring

mkdir -p "$KEYS" "$RESULTS/nodeLog" "$EXP/Log"

echo "LOGIN=$LOGIN"
echo "NODE_COUNT=$NODE_COUNT"
echo "DEGRADED_PERCENT=$DEGRADED_PERCENT"
echo "DEGRADED_COUNT=$DEGRADED_COUNT"
echo "HONEST_COUNT=$HONEST_COUNT"
echo "SRC=$SRC"
echo "EXP=$EXP"
echo "NODES=$NODES"
echo "KEYS=$KEYS"
echo "RESULTS=$RESULTS"
echo "TOPIC=$TOPIC"
```

---

## 5. Extract reserved hosts and IPs

```sh
mapfile -t HOSTS < <(sort -u "$OAR_NODEFILE" | head -"$NODE_COUNT")
printf '%s\n' "${HOSTS[@]}"

mapfile -t IPS < <(for h in "${HOSTS[@]}"; do getent hosts "$h" | awk '{print $1; exit}'; done)
printf '%s\n' "${IPS[@]}"
```

Check:
```sh
echo "HOSTS:"
printf '%s\n' "${HOSTS[@]}"

echo "IPS:"
printf '%s\n' "${IPS[@]}"

test "${#HOSTS[@]}" -eq "$NODE_COUNT"
test "${#IPS[@]}" -eq "$NODE_COUNT"
```

---

## 6. Install Go if needed

If go is not available:
```sh
cd /tmp
sudo-g5k

wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz

export PATH=$PATH:/usr/local/go/bin
```

---

## 7. Build keygen

```sh
cd "$SRC/keygen"
go build -o keygen .
ls -lh "$SRC/keygen/keygen"
```

Important: keygen must be executed on the node that owns the IP/port, because
it creates a temporary libp2p host listening on that address to obtain the peer
ID.

---

## 8. Clean old processes

Before a new run:

```sh
for h in "${HOSTS[@]}"; do
    echo "Killing old processes on $h"
    ssh "$h" "pkill -f libp2p-das || true"
done
```

Optional check:
```sh
for h in "${HOSTS[@]}"; do
    echo "=== $h ==="
    ssh "$h" "pgrep -af 'libp2p-das|keygen' || true"
done
```

---

## 9. Generate keys and nodes.csv

Use high ports to avoid conflicts with previous runs.
```sh
BASE_PORT=20000
BASE_UDP=22000

: > "$NODES"
rm -f "$KEYS"/*.key

for i in $(seq 0 $((NODE_COUNT - 1))); do
    h=${HOSTS[$i]}
    ip=${IPS[$i]}
    port=$((BASE_PORT + i))
    udp=$((BASE_UDP + i))

    type=node
    if [ "$i" -ge "$HONEST_COUNT" ]; then
    type=degraded
    fi

    nick="${type}${port}"
    key="$KEYS/${ip}-${nick}.key"

    echo "Generating key for $nick on $h / $ip:$port"

    maddr=$(ssh "$h" "export PATH=\$PATH:/usr/local/go/bin; '$SRC/keygen/keygen' '$key' '$ip' '$port'")

    if [ -z "$maddr" ]; then
    echo "ERROR: empty multiaddr for $h"
    exit 1
    fi

    printf "%s,%s,%s,%s,%s,%s\n" "$nick" "$port" "$udp" "$ip" "$maddr" "$type" >> "$NODES"
done
```

Check:
```sh
echo "=== nodes.csv ==="
cat "$NODES"

echo "=== role counts ==="
cut -d, -f6 "$NODES" | sort | uniq -c

echo "=== keys ==="
ls -lh "$KEYS"
```

Expected role count:
```sh
4 degraded
16 node
```

Do not continue if a multiaddr field is empty.

---

## 10. Install/build GossipSub on each reserved node

```sh
for h in "${HOSTS[@]}"; do
    echo "Installing on $h"
    ssh "$h" "GOSSIPSUB_SOURCE_DIR='$SRC' '$SRC/Launching_scripts/server_install.sh' '$LOGIN'" \
    > "$RESULTS/nodeLog/install_${h}.txt" 2>&1 &
done

wait
```

---

## 11. Launch the 20-node scoring experiment

```sh
for i in $(seq 0 $((NODE_COUNT - 1))); do
    echo "Starting node ${HOSTS[$i]} / ${IPS[$i]}"

    ssh "${HOSTS[$i]}" \
        "GOSSIPSUB_SOURCE_DIR='$SRC' \
        GOSSIPSUB_WORK_DIR='/tmp/gossipsub-scoring' \
        GOSSIPSUB_SLEEP_MARGIN=10 \
        GOSSIPSUB_TOPIC='$TOPIC' \
        GOSSIPSUB_INTERVAL=5 \
        GOSSIPSUB_MESSAGE_BYTES=512 \
        GOSSIPSUB_ENABLE_PEER_SCORE=true \
        GOSSIPSUB_D=6 \
        GOSSIPSUB_DLO=5 \
        GOSSIPSUB_DHI=12 \
        GOSSIPSUB_DSCORE=4 \
        GOSSIPSUB_DOUT=2 \
        GOSSIPSUB_SCORE_INSPECT=5 \
        GOSSIPSUB_APP_DEGRADED_SCORE=-50 \
        GOSSIPSUB_INVALID_PENALTY=-20 \
        GOSSIPSUB_INVALID_PENALTY_TTL=60 \
        GOSSIPSUB_DEGRADED_INVALID_PUBLISH_PCT=50 \
        GOSSIPSUB_DEGRADED_DROP_PCT=50 \
        '$SRC/Launching_scripts/run.sh' \
        '$NODES' \
        '$KEYS/' \
        '$RESULTS/' \
        '${IPS[$i]}' \
        180 \
        '$EXP' \
        >> '$RESULTS/nodeLog/run_sh_output_${IPS[$i]}.txt' 2>&1" &
done

wait
```

---

## 12. Verify the run

Check run.sh outputs:
```sh
cat "$RESULTS"/nodeLog/run_sh_output_*.txt
```

Expected:
```sh
All jobs finished successfully
```

Check generated files:
```sh
find "$EXP" -maxdepth 4 -type f | sort
```

Check node logs:
```sh
ls -lh "$EXP"/Log/
head -120 "$EXP"/Log/*.txt
```

Check GossipSub traces:
```sh
ls -lh "$RESULTS"/*.trace
head -20 "$RESULTS"/*.trace
```

Check score snapshots:
```sh
ls -lh "$RESULTS"/*.scores.csv
head "$RESULTS"/*.scores.csv
```

Search for severe errors:
```sh
grep -RniE "panic|fatal|failed to listen|address already in use|empty multiaddr|division by zero|permission denied|no such file" "$EXP" || true
```

Search for positive/degraded indicators:
```sh
grep -RniE "Running GossipSub node|role=degraded|Connected static peer|GossipSub publish|GossipSub message received|GossipSub validator rejected|GossipSub degraded drop|GossipSub node done" "$EXP"/Log/*.txt | head -200
```

---

## 13. Extract topology snapshots and metrics

```sh
cd "$SRC"

echo "EXP=$EXP"
echo "RESULTS=$RESULTS"
echo "NODES=$NODES"
echo "TOPIC=$TOPIC"
test -n "$EXP" && test -n "$RESULTS" && test -n "$NODES" && test -n "$TOPIC"

python3 analysis/topology_pipeline.py pipeline-traces \
    "$RESULTS" \
    --out-dir "$EXP/topology_pipeline" \
    --heartbeat-ms 1000 \
    --topic "$TOPIC"
```

Check extracted topology files:
```sh
find "$EXP/topology_pipeline" -type f | sort
cat "$EXP/topology_pipeline/snapshots/metadata.json"
head "$EXP/topology_pipeline/snapshots/snapshots.csv"
cat "$EXP/topology_pipeline/metrics/summary.json"
cat "$EXP/topology_pipeline/metrics/methodology.md"
head "$EXP/topology_pipeline/metrics/degree_timeseries.csv"
head "$EXP/topology_pipeline/metrics/churn_timeseries.csv"
head "$EXP/topology_pipeline/metrics/control_timeseries.csv"
head "$EXP/topology_pipeline/metrics/global_graph_timeseries.csv"
```

A successful run should show:
- 20 run.sh jobs finished successfully;
- 20 log files;
- 20 `.trace` files in `$RESULTS`;
- 20 `.scores.csv` files in `$RESULTS`;
- 16 `node` rows and 4 `degraded` rows in `nodes.csv`;
- invalid messages rejected by validators;
- degraded nodes dropping some received messages;
- topology snapshots under `$EXP/topology_pipeline/snapshots`;
- statistical topology metrics under `$EXP/topology_pipeline/metrics`;
- nodes shutting down cleanly after the configured duration.
