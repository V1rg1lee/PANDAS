#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt update -y

# Install Maven
echo "Installing Maven..."
sudo apt install -y maven

# Install OpenJDK 17 (JRE and JDK)
echo "Installing OpenJDK 17 (JRE and JDK)..."
sudo apt install -y openjdk-17-jre openjdk-17-jdk

# Verify installations
echo "Verifying installations..."
java -version
mvn -version

# Run Maven build
echo "Running Maven build..."
mvn clean install

echo "✅ Setup and build complete!"
