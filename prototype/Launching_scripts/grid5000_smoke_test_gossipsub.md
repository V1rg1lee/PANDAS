# GossipSub - Grid5000 smoke test

This document records the command sequence used to launch a minimal real libp2p GossipSub deployment on Grid5000.

Goal:
- reserve 3 Grid5000 nodes;
- launch 3 libp2p hosts from a static CSV topology;
- generate valid libp2p keys and multiaddresses;
- run the GossipSub binary on each node;
- collect GossipSub JSON tracer files;
- verify that all jobs finish successfully.

---

## 1. Connect to Grid5000

From the local machine:
```sh
    ssh g5k
```

Then connect to the Lille site frontend:
```sh
    ssh lille
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

## 3. Reserve 3 nodes

From the site frontend:
```sh
    oarsub -I -l nodes=3,walltime=0:20:00
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
    SRC=/home/$LOGIN/GossipSub-Minimal/prototype
    EXP=/home/$LOGIN/results/gossipsub-smoke-$(date +%Y%m%d-%H%M%S)
    NODES=$EXP/NodesFiles/nodes.csv
    KEYS=$EXP/NodesFiles/keys
    RESULTS=$EXP/results

    mkdir -p "$KEYS" "$RESULTS/nodeLog" "$EXP/Log"

    echo "LOGIN=$LOGIN"
    echo "SRC=$SRC"
    echo "EXP=$EXP"
    echo "NODES=$NODES"
    echo "KEYS=$KEYS"
    echo "RESULTS=$RESULTS"
```

---

## 5. Extract reserved hosts and IPs

```sh
    mapfile -t HOSTS < <(sort -u "$OAR_NODEFILE" | head -3)
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
```

Example:
```sh
    HOSTS:
    chiclet-3.lille.grid5000.fr
    chiclet-6.lille.grid5000.fr
    chifflot-5.lille.grid5000.fr

    IPS:
    172.16.39.3
    172.16.39.6
    172.16.36.5
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

Important: keygen must be executed on the node that owns the IP/port, because it creates a temporary libp2p host listening on that address to obtain the peer ID.

---

## 8. Clean old processes

Before a new smoke test:

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

## 9. Generate a fresh experiment directory

```sh
    EXP=/home/$LOGIN/results/gossipsub-smoke-$(date +%Y%m%d-%H%M%S)
    NODES=$EXP/NodesFiles/nodes.csv
    KEYS=$EXP/NodesFiles/keys
    RESULTS=$EXP/results

    mkdir -p "$KEYS" "$RESULTS/nodeLog" "$EXP/Log"

    echo "EXP=$EXP"
```

---

## 10. Generate valid keys and nodes.csv

Use high ports to avoid conflicts with previous runs.
```sh
    BASE_PORT=20000
    BASE_UDP=22000
```

Generate one key and multiaddress per node:
```sh
    : > "$NODES"
    rm -f "$KEYS"/*.key

    for i in 0 1 2; do
      h=${HOSTS[$i]}
      ip=${IPS[$i]}
      port=$((BASE_PORT + i))
      udp=$((BASE_UDP + i))

      type=node

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

    echo "=== keys ==="
    ls -lh "$KEYS"
```

Expected shape:
```sh
    node20000,20000,22000,172.16.39.3,/ip4/172.16.39.3/tcp/20000/p2p/12D3KooW...,node
    node20001,20001,22001,172.16.39.6,/ip4/172.16.39.6/tcp/20001/p2p/12D3KooW...,node
    node20002,20002,22002,172.16.36.5,/ip4/172.16.36.5/tcp/20002/p2p/12D3KooW...,node
```

Do not continue if the multiaddr field is empty.

---

## 11. Install/build GossipSub on each reserved node

```sh
    for h in "${HOSTS[@]}"; do
      echo "Installing on $h"
      ssh "$h" "GOSSIPSUB_SOURCE_DIR='$SRC' '$SRC/Launching_scripts/server_install.sh' '$LOGIN'" \
        > "$RESULTS/nodeLog/install_${h}.txt" 2>&1 &
    done

    wait
```

---

## 12. Launch the 3 GossipSub nodes

```sh
    for i in 0 1 2; do
      echo "Starting node ${HOSTS[$i]} / ${IPS[$i]}"

      ssh "${HOSTS[$i]}" \
         "GOSSIPSUB_SOURCE_DIR='$SRC' \
         GOSSIPSUB_WORK_DIR='/tmp/gossipsub-smoke' \
         GOSSIPSUB_SLEEP_MARGIN=5 \
         GOSSIPSUB_TOPIC='gossipsub-smoke' \
         GOSSIPSUB_INTERVAL=5 \
         GOSSIPSUB_MESSAGE_BYTES=512 \
         '$SRC/Launching_scripts/run.sh' \
         '$NODES' \
         '$KEYS/' \
         '$RESULTS/' \
         '${IPS[$i]}' \
         45 \
         '$EXP' \
         >> '$RESULTS/nodeLog/run_sh_output_${IPS[$i]}.txt' 2>&1" &
    done

    wait
```

---

## 13. Verify the smoke test

Check run.sh outputs:
```sh
    cat "$RESULTS"/nodeLog/run_sh_output_*.txt
```

Expected:
```sh
    All jobs finished successfully
    All jobs finished successfully
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

Search for severe errors:
```sh
    grep -RniE "panic|fatal|failed to listen|address already in use|empty multiaddr|division by zero|permission denied|no such file" "$EXP" || true
```

Search for positive indicators:
```sh
    grep -RniE "Running GossipSub node|Connected static peer|GossipSub publish|GossipSub message received|GossipSub node done" "$EXP"/Log/*.txt | head -150
```

Extract topology data:
```sh
    cd "$SRC"
    python3 analysis/extract_gossipsub_topology.py \
      "$RESULTS" \
      --nodes-file "$NODES" \
      --out-dir "$EXP/topology"
```

Check extracted topology files:
```sh
    find "$EXP/topology" -type f | sort
    cat "$EXP/topology/summary.json"
    cat "$EXP/topology/mesh_final_edges.csv"
    cat "$EXP/topology/mesh_final_degrees.csv"
```

A successful smoke test should show:
- all run.sh jobs finished successfully;
- one log file per node;
- one `.trace` file per node in `$RESULTS`;
- static libp2p peer connections are established from the CSV;
- messages are published and received through GossipSub;
- topology CSV files are generated under `$EXP/topology`;
- nodes shut down cleanly after the configured duration.
