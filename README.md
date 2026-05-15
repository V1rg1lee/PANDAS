# GossipSub Grid5000 Runner

This repository is a minimal libp2p GossipSub runner extracted from the original
PANDAS prototype.

It intentionally does not run the PANDAS application protocol anymore. The
binary only:

- creates one libp2p host per process;
- loads a static peer list from `nodes.csv`;
- connects to those peers;
- joins a GossipSub topic;
- periodically publishes fixed-size messages;
- records the libp2p-pubsub JSON trace for topology analysis.

The remaining code lives in `prototype/`.

## Build

```sh
cd prototype
go build -o libp2p-das .
```

## Grid5000

Use the launch notes in:

```sh
prototype/Launching_scripts/grid5000_smoke_test_gossipsub.md
```
