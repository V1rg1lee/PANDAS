#!/bin/bash
# ========== Parameters ==========                                                             
nodes_file="./nodes.csv"
num_validators=$1
num_regular_nodes=0

while getopts v:r: flag
do
    case "${flag}" in
        v) num_validators=${OPTARG};;
        r) num_regular_nodes=${OPTARG};;
    esac
done

port_base=9100
additional_port_base=12000
ip=127.0.0.1
port_counter=$port_base
additional_port_counter=$additional_port_base

# Clean the nodes file
printf "" > "$nodes_file"
mkdir -p ./keys/

# Compile key generator
cd keygen
go build .

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Keygen code build successful"
else
    echo "Error: Keygen code build failed"
    exit 1  # Exit the script with an error status
fi

# Go back to the parent directory
cd ..

# Creating Builder
echo "Creating Builder"
nick="builder${port_counter}"
maddr=$(./keygen/keygen ./keys/${nick}.key 127.0.0.1 ${port_counter})
echo "${nick},${port_counter},${additional_port_counter},${ip},${maddr},builder" >> $nodes_file
let "port_counter++"
let "additional_port_counter++"

# Create Validators
echo "Creating Validators"
for ((; port_counter < port_base + num_validators + 1 ; port_counter++, additional_port_counter++ )); do
    nick="validator${port_counter}"
    maddr=$(./keygen/keygen ./keys/${nick}.key 127.0.0.1 ${port_counter})
    echo "${nick},${port_counter},${additional_port_counter},${ip},${maddr},validator" >> $nodes_file
done

# Create Regular Nodes
echo "Creating Regular Nodes"
for ((; port_counter < port_base + num_validators + num_regular_nodes + 1 ; port_counter++, additional_port_counter++ )); do
    nick="regular${port_counter}"
    maddr=$(./keygen/keygen ./keys/${nick}.key 127.0.0.1 ${port_counter})
    echo "${nick},${port_counter},${additional_port_counter},${ip},${maddr},regular" >> $nodes_file
done

