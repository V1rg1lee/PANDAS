# 🐼 PANDAS: Simulator and Prototype Experiments

---

## 📘 Table of Contents

1. [Introduction](#introduction)
2. [Hardware](#hardware)
3. [Simulator](#simulator)
   - [Setup and Build](#setup-and-build)
   - [Running Experiments](#running-experiments)
   - [Plotting Results](#plotting-results)
4. [Prototype](#prototype)
   - [Setup and Build](#setup-and-build-1)
   - [Running Experiments](#running-experiments-1)
   - [Plotting Results](#plotting-results-1)
5. [Repository Structure](#repository-structure)

---

## 🧩 Introduction

The artifacts of this work are available at:  
👉 **[CloudLargeScale-UCLouvain/PANDAS](https://github.com/CloudLargeScale-UCLouvain/PANDAS)**

The repository includes:
- The **source code** of PANDAS
- The **scripts** to run the experiments
- The **plotting script** to plot experiments results

Both the simulator and the prototype implementations were run on **Linux-based operating systems**.

---

## Hardware

We run the simulator and a local version of the prototype on a server with 18-core Intel Xeon Gold 5220 CPU and 96 GB
of RAM.

---

## 📁 Repository Structure

```
PANDAS/
├── simulator/                      # Source code for large-scale simulator experiments
│   ├── configs/                    # Configuration files for network simulations
│   │    ├── configPaper/           # Configuration files used in the paper for perf: Figure 12 13 and 14 
│   │    ├── configAdversary/       # Configuration files for resilience against dead nodes: Figure 15
│   │    ├── configPaper1K/         # Configuration files for test of redundancy of samples: Figure 9 10 11 12
│   │    ├── configReel/            # Configuration files for validation with the prototype and validation of strategy
│   │    └── configPaper/           # Configuration files for validation with the prototype and validation of strategy
│   ├── src/                        # Code of the simulator
│   │    └── kademlia/das           # Folder containing PANDAS code used in the sumlator
│   └── python/                     # Plotting scripts
└── prototype/                      # Source code for real-world prototype experiments
    ├── results/                    # Prototype experiment results
    └── python/                     # Log processing and plotting
```

---

## 🧪 Simulator

The **simulator** is implemented in **Java 17** using **Maven** as a build tool.  
It is built on top of [Peersim](http://peersim.sourceforge.net/) and based on the Kademlia implementation by **Daniele Furlan** and **Maurizio Bonani**:  
👉 [http://peersim.sourceforge.net/code/kademlia.zip](http://peersim.sourceforge.net/code/kademlia.zip)

### 🔧 Setup and Build

To install all requirements and build the simulator:

```bash
cd simulator/
sudo chmod +x install.sh && ./install.sh
```

This script will:
- Install **Java 17** and **Maven**
- Fetch all dependencies
- Build the simulator

After this, the simulator is ready to run experiments.

---

### ▶️ Running Experiments

The simulator uses configuration files located in `simulator/configs/`.  
Each configuration file corresponds to a specific network size (e.g., `1k.cfg` simulates a network of 1,000 nodes).

To run an experiment:

```bash
cd simulator/
./run.sh <config_file>
```

🗂 Results will be stored in:
- `simulator/Results/` → Experiment results  
- `simulator/logs/` → Detailed logs

---

### 📊 Plotting Results

To plot the experiment results:

```bash
cd simulator/python
python3 plot_results.py
```

The generated plots will be saved in `simulator/python/plots/`

---

## 🌐 Prototype

The **prototype** is implemented in **Go** and built on top of [libp2p](https://libp2p.io/).

For the paper, we run the prototype on [Grid5000](https://www.grid5000.fr/), a **French distributed cluster** for experiment-driven research in computer science.  
It can also be executed locally at a smaller scale.

---

### 🔧 Setup and Build

To install requirements and build the prototype:

```bash
cd prototype/
sudo chmod +x setup.sh && ./setup.sh
```

This script installs:
- The latest version of **Go**
- All required dependencies
- The prototype binaries

After setup, the prototype is ready to run experiments.

---

### ▶️ Running Experiments

#### 1. Create a Topology File

First, generate a `nodes.csv` file defining the network topology (list of nodes and their unique peer IDs):

```bash
./create_topo.sh <number_of_nodes>
```

#### 2. Run the Prototype

Run the network using the topology file:

```bash
./run_local.sh <topology_file>
```

🗂 Results will be stored in:
- `prototype/results/` → Experiment results  
- `prototype/logs/` → Detailed logs

---

### 📊 Plotting Results

To process logs and plot results:

```bash
cd prototype/python
python3 process_logs.py <results_folder>
```

This generates visual analyses and metrics from the prototype experiments.

---
