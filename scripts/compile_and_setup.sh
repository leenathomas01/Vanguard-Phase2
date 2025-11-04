#!/usr/bin/env bash
set -e

# compile_and_setup.sh
# 
# Compiles the Vanguard circuit and performs trusted setup
# This creates the proving and verification keys needed for
# generating and verifying zk-SNARK proofs.
# 
# Requirements:
#   - circom (v2.0+)
#   - snarkjs
#   - node/npm
# 
# Usage:
#   chmod +x compile_and_setup.sh
#   ./compile_and_setup.sh

echo "=========================================="
echo "Vanguard v2 - Circuit Compilation & Setup"
echo "=========================================="
echo ""

# Configuration
CIRCUIT_NAME="intent_threshold"
CIRCUIT_FILE="circuits/${CIRCUIT_NAME}.circom"
BUILD_DIR="build"
PTAU_FILE="powersOfTau28_hez_final_12.ptau"
PTAU_URL="https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_12.ptau"

# Create build directory
mkdir -p "$BUILD_DIR"

# Check if circom is installed
if ! command -v circom &> /dev/null; then
    echo "❌ Error: circom not found"
    echo "Install: cargo install circom"
    exit 1
fi

# Check if snarkjs is installed
if ! command -v snarkjs &> /dev/null; then
    echo "❌ Error: snarkjs not found"
    echo "Install: npm install -g snarkjs"
    exit 1
fi

echo "✓ Dependencies verified"
echo ""

# Step 1: Compile circuit
echo "📦 Step 1: Compiling circuit..."
echo "  Input: $CIRCUIT_FILE"
echo "  Output: $BUILD_DIR/"

circom "$CIRCUIT_FILE" \
    --r1cs \
    --wasm \
    --sym \
    --c \
    -o "$BUILD_DIR" \
    -l node_modules

echo "  ✓ Circuit compiled"
echo "  - R1CS: $BUILD_DIR/${CIRCUIT_NAME}.r1cs"
echo "  - WASM: $BUILD_DIR/${CIRCUIT_NAME}_js/"
echo "  - Symbols: $BUILD_DIR/${CIRCUIT_NAME}.sym"
echo ""

# Step 2: Get Powers of Tau
echo "🔐 Step 2: Powers of Tau ceremony"

if [ -f "$PTAU_FILE" ]; then
    echo "  ✓ Found existing ptau file: $PTAU_FILE"
else
    echo "  Downloading from Hermez ceremony..."
    echo "  URL: $PTAU_URL"
    
    if command -v wget &> /dev/null; then
        wget -q --show-progress "$PTAU_URL" -O "$PTAU_FILE"
    elif command -v curl &> /dev/null; then
        curl -L "$PTAU_URL" -o "$PTAU_FILE" --progress-bar
    else
        echo "  ❌ Error: Need wget or curl to download ptau file"
        echo "  Download manually from: $PTAU_URL"
        exit 1
    fi
    
    echo "  ✓ Downloaded ptau file"
fi
echo ""

# Step 3: Trusted setup
echo "🔑 Step 3: Groth16 trusted setup"
echo "  Generating proving key..."

snarkjs groth16 setup \
    "$BUILD_DIR/${CIRCUIT_NAME}.r1cs" \
    "$PTAU_FILE" \
    "$BUILD_DIR/${CIRCUIT_NAME}_0000.zkey" \
    > /dev/null 2>&1

echo "  ✓ Proving key generated"
echo ""

# Step 4: Export verification key
echo "📤 Step 4: Exporting verification key"

snarkjs zkey export verificationkey \
    "$BUILD_DIR/${CIRCUIT_NAME}_0000.zkey" \
    "$BUILD_DIR/verification_key.json" \
    > /dev/null 2>&1

echo "  ✓ Verification key exported"
echo "  - Location: $BUILD_DIR/verification_key.json"
echo ""

# Step 5: Print circuit info
echo "📊 Circuit Information"
snarkjs r1cs info "$BUILD_DIR/${CIRCUIT_NAME}.r1cs"
echo ""

# Step 6: Create proofs directory
mkdir -p proofs
echo "✓ Created proofs directory"
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Generate a proof:"
echo "     python scripts/enhanced_generate_proof.py"
echo ""
echo "  2. Request confirmation:"
echo "     python scripts/request_confirmation.py --proof vca-xxxxxxxx"
echo ""
echo "  3. Verify independently:"
echo "     python scripts/verify_proof.py proofs/proof-xxx.json proofs/public-xxx.json"
echo ""
echo "Files created:"
echo "  - $BUILD_DIR/${CIRCUIT_NAME}.r1cs"
echo "  - $BUILD_DIR/${CIRCUIT_NAME}_js/"
echo "  - $BUILD_DIR/${CIRCUIT_NAME}_0000.zkey"
echo "  - $BUILD_DIR/verification_key.json"
echo "  - proofs/"
echo ""
echo "⚠️  Security Note: This uses a public Powers of Tau ceremony"
echo "   For production use, consider running your own MPC ceremony"
echo ""
