#!/usr/bin/env python3
"""
enhanced_generate_proof.py

Generates real zk-SNARK proofs for Verifiable Cognitive Actions (VCAs).
This script bridges Python and snarkjs to create cryptographic proofs
that confidence scores meet the required threshold.

Usage:
    python enhanced_generate_proof.py [--confidence 95.0] [--threshold 92.0]

Example:
    python enhanced_generate_proof.py --confidence 94.3 --threshold 92.0
"""

import json
import subprocess
import uuid
import time
import argparse
from pathlib import Path
from typing import Dict, Any

# Configuration
PROOFS_DIR = Path("proofs")
BUILD_DIR = Path("build")
CIRCUIT_NAME = "intent_threshold"
ZKEY = BUILD_DIR / f"{CIRCUIT_NAME}_0000.zkey"
VERIFICATION_KEY = BUILD_DIR / "verification_key.json"
WASM_DIR = BUILD_DIR / f"{CIRCUIT_NAME}_js"
WITNESS_FILE = BUILD_DIR / "witness.wtns"

# Ensure directories exist
PROOFS_DIR.mkdir(exist_ok=True)


def run_command(cmd: list, description: str = "") -> str:
    """Execute shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Command failed: {description}")


def generate_witness(confidence_fixed: int, threshold_fixed: int) -> Path:
    """Generate witness using snarkjs."""
    # Write input file
    input_data = {
        "confidence": confidence_fixed,
        "threshold": threshold_fixed
    }
    input_file = BUILD_DIR / "input.json"
    input_file.write_text(json.dumps(input_data))
    
    print(f"  📝 Input: confidence={confidence_fixed}, threshold={threshold_fixed}")
    
    # Generate witness using node
    witness_gen_js = WASM_DIR / "generate_witness.js"
    wasm_file = WASM_DIR / f"{CIRCUIT_NAME}.wasm"
    
    if not witness_gen_js.exists():
        raise FileNotFoundError(
            f"Witness generator not found: {witness_gen_js}\n"
            f"Run: ./scripts/compile_and_setup.sh"
        )
    
    run_command(
        ["node", str(witness_gen_js), str(wasm_file), str(input_file), str(WITNESS_FILE)],
        "witness generation"
    )
    
    print(f"  ✓ Witness generated")
    return WITNESS_FILE


def generate_proof(witness_file: Path) -> tuple[Path, Path]:
    """Generate zk-SNARK proof using snarkjs."""
    # Generate unique filenames
    proof_id = uuid.uuid4().hex[:8]
    proof_file = PROOFS_DIR / f"proof-{proof_id}.json"
    public_file = PROOFS_DIR / f"public-{proof_id}.json"
    
    if not ZKEY.exists():
        raise FileNotFoundError(
            f"Proving key not found: {ZKEY}\n"
            f"Run: ./scripts/compile_and_setup.sh"
        )
    
    run_command(
        ["snarkjs", "groth16", "prove", str(ZKEY), str(witness_file),
         str(proof_file), str(public_file)],
        "proof generation"
    )
    
    print(f"  ✓ Proof generated: {proof_file.name}")
    return proof_file, public_file


def verify_proof(proof_file: Path, public_file: Path) -> bool:
    """Verify the generated proof."""
    if not VERIFICATION_KEY.exists():
        raise FileNotFoundError(
            f"Verification key not found: {VERIFICATION_KEY}\n"
            f"Run: ./scripts/compile_and_setup.sh"
        )
    
    try:
        output = run_command(
            ["snarkjs", "groth16", "verify", str(VERIFICATION_KEY),
             str(public_file), str(proof_file)],
            "proof verification"
        )
        return "OK" in output
    except:
        return False


def create_vca(
    confidence: float,
    threshold: float,
    proof_file: Path,
    public_file: Path,
    intent: str = "Example intent",
    task_data: str = ""
) -> Dict[str, Any]:
    """Create Verifiable Cognitive Action object."""
    vca_id = f"vca-{uuid.uuid4().hex[:8]}"
    
    # Read proof and public signals
    proof_data = json.loads(proof_file.read_text())
    public_data = json.loads(public_file.read_text())
    
    # Create VCA
    vca = {
        "vca_id": vca_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "intent": intent,
        "task_data": task_data,
        "cognitive_state": {
            "confidence": confidence,
            "threshold": threshold
        },
        "zkp": {
            "type": "groth16",
            "circuit": CIRCUIT_NAME,
            "proof_file": str(proof_file.relative_to(Path.cwd())),
            "public_file": str(public_file.relative_to(Path.cwd())),
            "proof": proof_data,
            "public_signals": public_data,
            "verified": True,
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }
    
    # Save VCA
    vca_file = PROOFS_DIR / f"{vca_id}.json"
    vca_file.write_text(json.dumps(vca, indent=2))
    
    print(f"  ✓ VCA created: {vca_file.name}")
    return vca


def generate_real_proof(
    confidence_percent: float,
    threshold_percent: float = 92.0,
    intent: str = "Example cognitive action",
    task_data: str = ""
) -> Dict[str, Any]:
    """
    Main function to generate a complete VCA with real zk-SNARK proof.
    
    Args:
        confidence_percent: Confidence score (0-100), e.g., 94.3
        threshold_percent: Minimum threshold (0-100), e.g., 92.0
        intent: Human-readable intent description
        task_data: Additional task details
    
    Returns:
        VCA object with embedded proof
    """
    print("\n" + "="*50)
    print("Vanguard v2 - Real Proof Generation")
    print("="*50)
    
    # Convert to fixed-point integers (multiply by 100)
    confidence_fixed = int(round(confidence_percent * 100))
    threshold_fixed = int(round(threshold_percent * 100))
    
    print(f"\n📊 Parameters:")
    print(f"  Confidence: {confidence_percent}% ({confidence_fixed})")
    print(f"  Threshold: {threshold_percent}% ({threshold_fixed})")
    print(f"  Intent: {intent}")
    
    # Generate witness
    print(f"\n🔨 Generating witness...")
    witness_file = generate_witness(confidence_fixed, threshold_fixed)
    
    # Generate proof
    print(f"\n🔐 Generating zk-SNARK proof...")
    proof_file, public_file = generate_proof(witness_file)
    
    # Verify proof
    print(f"\n✓ Verifying proof...")
    is_valid = verify_proof(proof_file, public_file)
    
    if is_valid:
        print(f"  ✅ Proof verified successfully!")
    else:
        print(f"  ❌ Proof verification failed!")
        raise RuntimeError("Proof verification failed")
    
    # Create VCA
    print(f"\n📦 Creating VCA...")
    vca = create_vca(
        confidence_percent,
        threshold_percent,
        proof_file,
        public_file,
        intent,
        task_data
    )
    
    print(f"\n" + "="*50)
    print(f"✅ VCA Generated Successfully")
    print(f"="*50)
    print(f"\nVCA ID: {vca['vca_id']}")
    print(f"Proof: {proof_file.name}")
    print(f"Public: {public_file.name}")
    print(f"\nNext steps:")
    print(f"  1. Request confirmation:")
    print(f"     python scripts/request_confirmation.py --vca {vca['vca_id']}")
    print(f"  2. Verify independently:")
    print(f"     python scripts/verify_proof.py {proof_file} {public_file}")
    print()
    
    return vca


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate real zk-SNARK proof for cognitive action"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=94.3,
        help="Confidence score (0-100)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=92.0,
        help="Minimum threshold (0-100)"
    )
    parser.add_argument(
        "--intent",
        type=str,
        default="Example cognitive action",
        help="Intent description"
    )
    parser.add_argument(
        "--task-data",
        type=str,
        default="",
        help="Additional task details"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not (0 <= args.confidence <= 100):
        print("❌ Error: Confidence must be between 0 and 100")
        return 1
    
    if not (0 <= args.threshold <= 100):
        print("❌ Error: Threshold must be between 0 and 100")
        return 1
    
    # Generate proof
    try:
        vca = generate_real_proof(
            args.confidence,
            args.threshold,
            args.intent,
            args.task_data
        )
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
