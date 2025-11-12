# Kademlia Simulator

## Overview
 
This is a Kademlia Simulator that was used in the research project for the new Service Discovery in Ethereum 2.0 (Discv5) (available at: https://github.com/datahop/p2p-service-discovery). The simulator is built on top of [PeerSim](http://peersim.sourceforge.net/) and it is based on the Kademlia implementation from Daniele Furlan and Maurizio Bonani that can be found [here](http://peersim.sourceforge.net/code/kademlia.zip).

## Requirements

To run the simulator it is necessary to have Java and Maven installed. For Ubuntu systems just run:

```shell
$ sudo apt install maven
$ sudo apt install openjdk-17-jre
$ sudo apt install openjdk-17-jdk
$ mvn clean install
```

## How to run it

To execute a simulation it is necessary to call the run.sh, with a configuration file as a parameter. For example:

```shell
$ ./run.sh config/3k.cfg
```

## Code Documentation

[Kademlia draft documentation](simulator/src/main/java/peersim/kademlia/docs/kademlia_draft_doc.md) 

[Javadoc generated documentation](simulator/src/main/java/peersim/kademlia/docs/apidocs/) 

## Directory Architecture

This repository is organized as follows:

- **simulator/**  
  Main simulator code and resources:
  - **dependency-reduced-pom.xml, pom.xml**: Maven build files.
  - **run.sh**: Shell script to run simulations.
  - **test_latency_create.py**: Python script to create testing latencies.
  - **config/**: Simulation configuration files, organized by scenario:
    - **gossipsub_topology.csv, latency.json**: Topology for gossipsub and latency between nodes.
    - **configPaper/**, **paper1k/**, **configPaper1K/**, **configPaperLargeScale/**, **configReel/**, **K-variation/**: Paper experiment configs.
  - **lib/**: Java library dependencies.
  - **logs/**: Log files.
  - **Results/**: Simulation results.
  - **src/**: Source code.
  - **main/**, **target/**: Build output and compiled classes.

- **visualiser/**  
  Network visualization tools:
  - **app.py, index.py, network_visualiser.py**: Visualization scripts.
  - **README.md**: Visualiser documentation.

---

This structure supports simulation, configuration, analysis, and visualization for Kademlia
