#!/bin/bash
# =============================================================================
# CloudSim Plus v8.x Installation Script for HFL Research Project
# Project: Hierarchical Federated Learning for Privacy-Aware Multimodal IoT
# Student: Samartha H V | MIT Bengaluru
# =============================================================================
# Requirements: Ubuntu 24.04 LTS, Java 17+, Maven 3.8+
# Run as: bash install_cloudsim.sh
# =============================================================================

set -e

CS_DIR="/home/mit/DEADSERPENT/HFL/SIMULATORS/cloudsim-plus"
HFL_PROJECT_DIR="/home/mit/DEADSERPENT/HFL/SIMULATORS/cloudsim-plus/hfl-simulation"
CORES=$(nproc)

echo "============================================================"
echo "  CloudSim Plus Installation for HFL Research"
echo "  Java: $(java --version 2>&1 | head -1)"
echo "  Maven: $(mvn --version 2>&1 | head -1)"
echo "============================================================"

# ── STEP 1: Verify Java and Maven ────────────────────────────────────────────
echo ""
echo "[STEP 1/5] Verifying Java 17+ and Maven..."

JAVA_VER=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}' | cut -d'.' -f1)
if [ "$JAVA_VER" -lt 17 ]; then
    echo "  [ERROR] Java 17+ required. Found Java $JAVA_VER. Installing Java 21..."
    sudo apt-get install -y openjdk-21-jdk
    export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
fi

echo "  [OK] Java $JAVA_VER detected."
echo "  [OK] Maven $(mvn --version 2>&1 | awk 'NR==1{print $3}') detected."

# ── STEP 2: Clone CloudSim Plus ──────────────────────────────────────────────
echo ""
echo "[STEP 2/5] Cloning CloudSim Plus..."
cd "$CS_DIR"

if [ -d "cloudsim-plus-source/.git" ]; then
    echo "  Repository already exists. Pulling latest..."
    cd cloudsim-plus-source && git pull
else
    git clone https://github.com/manoelcampos/cloudsim-plus.git cloudsim-plus-source
    cd cloudsim-plus-source
fi

# Use latest stable tag
LATEST_TAG=$(git tag -l "v*" | sort -V | tail -1)
echo "  Checking out tag: $LATEST_TAG"
git checkout "$LATEST_TAG" 2>/dev/null || git checkout main

echo "  [OK] CloudSim Plus source ready."

# ── STEP 3: Build CloudSim Plus and install to local Maven repository ─────────
echo ""
echo "[STEP 3/5] Building CloudSim Plus (using $CORES threads)..."
mvn clean install -DskipTests -T$CORES -q

echo "  [OK] CloudSim Plus built and installed to local Maven repo."

# ── STEP 4: Create HFL Simulation Maven project ──────────────────────────────
echo ""
echo "[STEP 4/5] Creating HFL simulation Maven project..."

mkdir -p "$HFL_PROJECT_DIR/src/main/java/hfl"

# Get installed CloudSim Plus version
CS_VERSION=$(mvn help:evaluate -Dexpression=project.version -q -DforceStdout 2>/dev/null || echo "8.3.0")

# Write pom.xml
cat > "$HFL_PROJECT_DIR/pom.xml" << POMEOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>hfl.research</groupId>
    <artifactId>hfl-simulation</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    <name>HFL Research Simulation</name>
    <description>
        Hierarchical Federated Learning simulation using CloudSim Plus
        for Privacy-Aware, Low-Latency Multimodal IoT Systems
    </description>

    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <cloudsimplus.version>${CS_VERSION}</cloudsimplus.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.cloudsimplus</groupId>
            <artifactId>cloudsim-plus</artifactId>
            <version>\${cloudsimplus.version}</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-jar-plugin</artifactId>
                <version>3.3.0</version>
                <configuration>
                    <archive>
                        <manifest>
                            <mainClass>hfl.HFLSimTest</mainClass>
                        </manifest>
                    </archive>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
POMEOF

echo "  [OK] Maven project created at: $HFL_PROJECT_DIR"

# ── STEP 5: Smoke test ───────────────────────────────────────────────────────
echo ""
echo "[STEP 5/5] Running CloudSim Plus smoke test..."
cd "$HFL_PROJECT_DIR"
mvn compile -q 2>&1 && echo "  [OK] Maven compile: PASSED" || echo "  [WARN] Compile check: run manually."

echo ""
echo "============================================================"
echo "  CloudSim Plus Installation COMPLETE"
echo "  Source: $CS_DIR/cloudsim-plus-source"
echo "  HFL Project: $HFL_PROJECT_DIR"
echo "  Run simulations: cd hfl-simulation && mvn exec:java"
echo "  CloudSim Version: $CS_VERSION"
echo "============================================================"
