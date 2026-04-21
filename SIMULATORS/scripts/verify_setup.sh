#!/bin/bash
# =============================================================================
# Environment Verification Script — HFL Research Project
# Verifies NS-3 + CloudSim Plus installation and research reproducibility
# =============================================================================

set -e

NS3_HOME="/home/mit/DEADSERPENT/HFL/SIMULATORS/ns3/ns-3-dev"
CS_HOME="/home/mit/DEADSERPENT/HFL/SIMULATORS/cloudsim-plus/hfl-simulation"
PASS=0; FAIL=0

check() {
    if eval "$2" &>/dev/null; then
        echo "  [PASS] $1"
        ((PASS++))
    else
        echo "  [FAIL] $1"
        ((FAIL++))
    fi
}

echo "============================================================"
echo "  HFL Research Environment Verification"
echo "  Date: $(date)"
echo "============================================================"

echo ""
echo "── System Requirements ──────────────────────────────────────"
check "Ubuntu 24.04 LTS"          "grep -q '24.04' /etc/os-release"
check "GCC 13+"                   "gcc --version | grep -q '1[3-9]'"
check "G++ 13+"                   "g++ --version | grep -q '1[3-9]'"
check "CMake 3.25+"               "cmake --version | grep -qE '3\.(2[5-9]|[3-9][0-9])'"
check "Python 3.10+"              "python3 --version | grep -qE '3\.(1[0-9]|[2-9][0-9])'"
check "Java 17+"                  "java --version 2>&1 | grep -qE '(17|18|19|20|21|22)'"
check "Maven 3.6+"                "mvn --version | grep -qE '3\.[6-9]'"
check "Git"                       "git --version"
check "Disk space >50GB free"     "[ $(df /home | awk 'NR==2{print $4}') -gt 52428800 ]"

echo ""
echo "── Python Packages ──────────────────────────────────────────"
check "numpy"                     "python3 -c 'import numpy'"
check "pandas"                    "python3 -c 'import pandas'"
check "matplotlib"                "python3 -c 'import matplotlib'"
check "scipy"                     "python3 -c 'import scipy'"
check "seaborn"                   "python3 -c 'import seaborn'"

echo ""
echo "── NS-3 Installation ────────────────────────────────────────"
check "NS-3 source directory"     "[ -d '$NS3_HOME' ]"
check "NS-3 executable (./ns3)"   "[ -f '$NS3_HOME/ns3' ]"
check "NS-3 build artifacts"      "[ -d '$NS3_HOME/build' ]"
check "NS-3 Python bindings dir"  "ls '$NS3_HOME/build/lib/python*' 2>/dev/null || ls '$NS3_HOME/build/bindings' 2>/dev/null"

echo ""
echo "── CloudSim Plus Installation ───────────────────────────────"
check "CloudSim Plus source"      "[ -d '/home/mit/DEADSERPENT/HFL/SIMULATORS/cloudsim-plus/cloudsim-plus-source' ]"
check "CloudSim Plus in Maven"    "ls ~/.m2/repository/org/cloudsimplus/ 2>/dev/null"
check "HFL Maven project"         "[ -f '$CS_HOME/pom.xml' ]"
check "HFL source directory"      "[ -d '$CS_HOME/src/main/java/hfl' ]"

echo ""
echo "── Results Directories ──────────────────────────────────────"
check "NS-3 results dir"          "[ -d '/home/mit/DEADSERPENT/HFL/SIMULATORS/results/ns3' ]"
check "CloudSim results dir"      "[ -d '/home/mit/DEADSERPENT/HFL/SIMULATORS/results/cloudsim' ]"
check "Merged results dir"        "[ -d '/home/mit/DEADSERPENT/HFL/SIMULATORS/results/merged' ]"
check "Config dir"                "[ -d '/home/mit/DEADSERPENT/HFL/SIMULATORS/config' ]"

echo ""
echo "============================================================"
echo "  Results: $PASS PASSED | $FAIL FAILED"
if [ "$FAIL" -eq 0 ]; then
    echo "  STATUS: ENVIRONMENT READY FOR PHASE 4 IMPLEMENTATION"
else
    echo "  STATUS: $FAIL checks failed — run install scripts first."
    echo "  Fix: bash install_ns3.sh && bash install_cloudsim.sh"
fi
echo "============================================================"
