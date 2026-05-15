# How to stop

This page describes how to stop the nodes and clean up the environment after a test run.

## Stop the nodes

Verify the node processes:
```sh
    for h in "${HOSTS[@]}"; do
        echo "=== $h ==="
        ssh "$h" "pgrep -af 'libp2p-das|keygen' || true"
    done
```

If there are still node processes running, kill them:
```sh
    for h in "${HOSTS[@]}"; do
        echo "Cleaning $h"
        ssh "$h" "pkill -f libp2p-das || true"
        ssh "$h" "pkill -f keygen || true"
    done
```

## Clean up the environment

Delete files with:
```sh
    for h in "${HOSTS[@]}"; do
        echo "Removing temp dir on $h"
        ssh "$h" "rm -rf /tmp/gossipsub-smoke"
    done
```

If you want to delete the experiment results, also remove the experiment directory:
```sh
    rm -rf "$EXP"
```

## Exit the session:

```sh
    exit
```

## Verify there is no more job running on Grid5000:

```sh
    oarstat -u
```

If there are still jobs running, you can cancel them with:
```sh
    oarstat -u
    oarkill <job_id>
```
