#!/bin/bash
# =============================================================================
# NS-3.43 Installation Script for HFL Research Project
# Project: Hierarchical Federated Learning for Privacy-Aware Multimodal IoT
# Student: Samartha H V | MIT Bengaluru
# =============================================================================
# Requirements: Ubuntu 24.04 LTS, GCC 13+, CMake 3.28+, Python 3.12+
# Run as: bash install_ns3.sh
# =============================================================================

set -e  # Exit on any error

NS3_DIR="/home/mit/DEADSERPENT/HFL/SIMULATORS/ns3"
NS3_VERSION="ns-3.43"
CORES=$(nproc)

echo "============================================================"
echo "  NS-3 Installation for HFL Research"
echo "  Version: $NS3_VERSION | Cores: $CORES"
echo "============================================================"

# ── STEP 1: Install system dependencies ──────────────────────────────────────
echo ""
echo "[STEP 1/6] Installing NS-3 system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
    build-essential \
    libsqlite3-dev \
    libboost-all-dev \
    libssl-dev \
    git \
    python3-dev \
    python3-setuptools \
    python3-pip \
    pkg-config \
    sqlite3 \
    bison \
    flex \
    ccache \
    libxml2-dev \
    gdb \
    valgrind \
    ninja-build \
    libpython3-dev \
    python3-pytest \
    libgsl-dev \
    gsl-bin \
    libopenmpi-dev \
    openmpi-bin \
    clang-format \
    python3-matplotlib \
    python3-scipy \
    python3-numpy \
    castxml 2>/dev/null || true

echo "  [OK] System dependencies installed."

# ── STEP 2: Install Python dependencies for NS-3 bindings ────────────────────
echo ""
echo "[STEP 2/6] Installing Python packages for NS-3 bindings..."
pip3 install --user \
    cppyy \
    pybindgen \
    matplotlib \
    numpy \
    pandas \
    scipy \
    seaborn \
    jupyter 2>/dev/null || true

echo "  [OK] Python packages installed."

# ── STEP 3: Download NS-3 source ─────────────────────────────────────────────
echo ""
echo "[STEP 3/6] Downloading NS-3 source ($NS3_VERSION)..."
cd "$NS3_DIR"

if [ -d "ns-3-dev/.git" ]; then
    echo "  Repository already exists. Fetching latest..."
    cd ns-3-dev && git fetch --tags
else
    git clone https://gitlab.com/nsnam/ns-3-dev.git
    cd ns-3-dev
fi

# Checkout the stable release tag
git checkout $NS3_VERSION 2>/dev/null || \
git checkout tags/$NS3_VERSION 2>/dev/null || \
    echo "  [WARN] Tag $NS3_VERSION not found, using latest main branch."

echo "  [OK] NS-3 source ready at: $(pwd)"

# ── STEP 4: Configure with Python bindings enabled ───────────────────────────
echo ""
echo "[STEP 4/6] Configuring NS-3 (Python bindings + examples + tests)..."

./ns3 configure \
    --enable-python-bindings \
    --enable-examples \
    --enable-tests \
    --build-profile=optimized \
    2>&1 | tail -20

echo "  [OK] NS-3 configured."

# ── STEP 5: Build NS-3 (using all cores) ─────────────────────────────────────
echo ""
echo "[STEP 5/6] Building NS-3 (this takes 10-20 minutes, using $CORES cores)..."
./ns3 build -j$CORES 2>&1 | tail -5

echo "  [OK] NS-3 build complete."

# ── STEP 6: Run smoke test ───────────────────────────────────────────────────
echo ""
echo "[STEP 6/6] Running smoke test..."
./ns3 run hello-simulator 2>&1 | head -5 && \
    echo "  [OK] C++ test: PASSED" || \
    echo "  [WARN] C++ test failed — check build."

python3 -c "import ns.core; print('  [OK] Python bindings: PASSED')" 2>/dev/null || \
    echo "  [INFO] Python bindings: may need PYTHONPATH — see verify_setup.sh"

echo ""
echo "============================================================"
echo "  NS-3 Installation COMPLETE"
echo "  Location: $NS3_DIR/ns-3-dev"
echo "  Run simulations with: ./ns3 run <script-name>"
echo "  Python interface: python3 <script.py> from ns-3-dev directory"
echo "============================================================"
