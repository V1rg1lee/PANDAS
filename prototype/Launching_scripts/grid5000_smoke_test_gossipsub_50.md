# GossipSub - Grid5000 50-node scoring experiment

Launch a minimal real libp2p GossipSub deployment on Grid5000 with 50 nodes,
peer scoring enabled, and 20% degraded peers.

Goal:
- reserve 50 Grid5000 nodes;
- mark 40 nodes as honest and 10 nodes as degraded;
- run GossipSub with explicit mesh parameters;
- collect traces, peer-score snapshots, logs, and topology metrics.

---

## 1. Connect and clone

```sh
ssh g5k
ssh <city>

cd ~
git clone https://github.com/V1rg1lee/GossipSub-Minimal.git
cd ~/GossipSub-Minimal/prototype
```

---

## 2. Reserve 50 nodes

```sh
oarsub -I -l nodes=50,walltime=00:45:00

hostname
echo "$OAR_NODEFILE"
cat "$OAR_NODEFILE"
```

---

## 3. Define variables

```sh
LOGIN=$USER
NODE_COUNT=50
DEGRADED_PERCENT=20
DEGRADED_COUNT=$(((NODE_COUNT * DEGRADED_PERCENT + 99) / 100))
HONEST_COUNT=$((NODE_COUNT - DEGRADED_COUNT))

SRC=/home/$LOGIN/GossipSub-Minimal/prototype
EXP=/home/$LOGIN/results/gossipsub-scoring-50-$(date +%Y%m%d-%H%M%S)
NODES=$EXP/NodesFiles/nodes.csv
KEYS=$EXP/NodesFiles/keys
RESULTS=$EXP/results
TOPIC=gossipsub-scoring-50

mkdir -p "$KEYS" "$RESULTS/nodeLog" "$EXP/Log"

echo "NODE_COUNT=$NODE_COUNT"
echo "DEGRADED_COUNT=$DEGRADED_COUNT"
echo "HONEST_COUNT=$HONEST_COUNT"
echo "EXP=$EXP"
```

---

## 4. Extract hosts and IPs

```sh
mapfile -t HOSTS < <(sort -u "$OAR_NODEFILE" | head -"$NODE_COUNT")
mapfile -t IPS < <(for h in "${HOSTS[@]}"; do getent hosts "$h" | awk '{print $1; exit}'; done)

printf '%s\n' "${HOSTS[@]}"
printf '%s\n' "${IPS[@]}"

test "${#HOSTS[@]}" -eq "$NODE_COUNT"
test "${#IPS[@]}" -eq "$NODE_COUNT"
```

---

## 4.5 Install Go 

If go is not available:
```sh
cd /tmp
sudo-g5k

wget https://go.dev/dl/go1.21.6.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.6.linux-amd64.tar.gz

export PATH=$PATH:/usr/local/go/bin
```

---

## 5. Build keygen

If Go is missing, install it first as in the 20-node guide.

```sh
cd "$SRC/keygen"
go build -o keygen .
ls -lh "$SRC/keygen/keygen"
```

---

## 6. Clean old processes

```sh
for h in "${HOSTS[@]}"; do
    echo "Killing old processes on $h"
    ssh "$h" "pkill -f libp2p-das || true"
done
```

---

## 7. Generate keys and nodes.csv

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

cat "$NODES"
cut -d, -f6 "$NODES" | sort | uniq -c
ls -lh "$KEYS"
```

Expected role count:
```sh
10 degraded
40 node
```

---

## 8. Install/build GossipSub

```sh
for h in "${HOSTS[@]}"; do
    echo "Installing on $h"
    ssh "$h" "GOSSIPSUB_SOURCE_DIR='$SRC' '$SRC/Launching_scripts/server_install.sh' '$LOGIN'" \
        > "$RESULTS/nodeLog/install_${h}.txt" 2>&1 &
done

wait
```

---

## 9. Launch the 50-node experiment

```sh
for i in $(seq 0 $((NODE_COUNT - 1))); do
    echo "Starting node ${HOSTS[$i]} / ${IPS[$i]}"

    ssh "${HOSTS[$i]}" \
        "GOSSIPSUB_SOURCE_DIR='$SRC' \
        GOSSIPSUB_WORK_DIR='/tmp/gossipsub-scoring-50' \
        GOSSIPSUB_SLEEP_MARGIN=15 \
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
        300 \
        '$EXP' \
        >> '$RESULTS/nodeLog/run_sh_output_${IPS[$i]}.txt' 2>&1" &
done

wait
```

---

## 10. Verify and extract metrics

```sh
cat "$RESULTS"/nodeLog/run_sh_output_*.txt
find "$EXP" -maxdepth 4 -type f | sort

ls -lh "$EXP"/Log/
ls -lh "$RESULTS"/*.trace
ls -lh "$RESULTS"/*.scores.csv

grep -RniE "panic|fatal|failed to listen|address already in use|empty multiaddr|division by zero|permission denied|no such file" "$EXP" || true
grep -RniE "Running GossipSub node|role=degraded|GossipSub validator rejected|GossipSub degraded drop|GossipSub node done" "$EXP"/Log/*.txt | head -200
```

```sh
cd "$SRC"

python3 analysis/topology_pipeline.py pipeline-traces \
    "$RESULTS" \
    --out-dir "$EXP/topology_pipeline" \
    --heartbeat-ms 1000 \
    --topic "$TOPIC"
```

```sh
find "$EXP/topology_pipeline" -type f | sort
cat "$EXP/topology_pipeline/snapshots/metadata.json"
cat "$EXP/topology_pipeline/metrics/summary.json"
head "$EXP/topology_pipeline/metrics/degree_timeseries.csv"
head "$EXP/topology_pipeline/metrics/churn_timeseries.csv"
head "$EXP/topology_pipeline/metrics/control_timeseries.csv"
head "$EXP/topology_pipeline/metrics/global_graph_timeseries.csv"
```

Expected:
- 50 `.trace` files;
- 50 `.scores.csv` files;
- 40 honest nodes and 10 degraded nodes;
- degraded nodes visible in logs and score snapshots;
- topology metrics under `$EXP/topology_pipeline/metrics`.

---

## 11. Copy results to your local machine

From your local machine:
```sh
scp <user>@access.grid5000.fr:~/<city>/results/gossipsub-scoring-50-YYYYMMDD-HHMMSS/topology_pipeline/metrics/* .

scp -J <user>@access.grid5000.fr \
    <user>@<city>.grid5000.fr:/home/<user>/results/gossipsub-scoring-50-YYYYMMDD-HHMMSS/results/* .
```