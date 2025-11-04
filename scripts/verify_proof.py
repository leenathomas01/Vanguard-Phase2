#!/usr/bin/env python3
"""
verify_proof.py

Independently verify a zk-SNARK proof without trusting the generator.
Anyone with the verification key can run this to validate proofs.

Usage:
    python verify_proof.py <proof.json> <public.json>

Example:
    python verify_proof.py proofs/proof-3f8a2b1c.json proofs/public-3f8a2b1c.json
"""

import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional

BUILD_DIR = Path("build")
VERIFICATION_KEY = BUILD_DIR / "verification_key.json"


def verify_proof(proof_path: Path, public_path: Path, vkey_path: Path) -> tuple[bool, str]:
    """
    Verify zk-SNARK proof using snarkjs.
    
    Returns:
        (is_valid, output_message)
    """
    if not proof_path.exists():
        return False, f"Proof file not found: {proof_path}"
    
    if not public_path.exists():
        return False, f"Public signals file not found: {public_path}"
    
    if not vkey_path.exists():
        return False, f"Verification key not found: {vkey_path}\nRun: ./scripts/compile_and_setup.sh"
    
    try:
        result = subprocess.run(
            ["snarkjs", "groth16", "verify", str(vkey_path), str(public_path), str(proof_path)],
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout + result.stderr
        is_valid = "OK" in result.stdout or result.returncode == 0
        
        return is_valid, output
    
    except FileNotFoundError:
        return False, "snarkjs not found. Install: npm install -g snarkjs"
    except Exception as e:
        return False, f"Verification error: {e}"


def display_proof_info(proof_path: Path, public_path: Path):
    """Display proof metadata."""
    print("\n" + "="*60)
    print("  🔍 PROOF VERIFICATION")
    print("="*60)
    print()
    
    print(f"  Proof file: {proof_path}")
    print(f"  Public signals: {public_path}")
    print(f"  Verification key: {VERIFICATION_KEY}")
    print()
    
    # Try to read public signals
    try:
        public_data = json.loads(public_path.read_text())
        print(f"  Public Inputs:")
        for i, signal in enumerate(public_data):
            print(f"    [{i}] {signal}")
        print()
    except:
        pass


def display_result(is_valid: bool, output: str):
    """Display verification result."""
    print("="*60)
    
    if is_valid:
        print("  ✅ PROOF VERIFIED")
        print("="*60)
        print()
        print("  The proof is cryptographically valid.")
        print("  The prover demonstrated that confidence >= threshold")
        print("  without revealing the exact confidence value.")
    else:
        print("  ❌ PROOF INVALID")
        print("="*60)
        print()
        print("  The proof failed verification.")
        print("  This could mean:")
        print("    - The proof was tampered with")
        print("    - The proof was generated with wrong inputs")
        print("    - The verification key doesn't match")
    
    print()
    
    if output and not is_valid:
        print("  Verification output:")
        print("  " + "-"*56)
        for line in output.split('\n'):
            if line.strip():
                print(f"  {line}")
        print("  " + "-"*56)
        print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Independently verify a zk-SNARK proof",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a specific proof
  python verify_proof.py proofs/proof-abc123.json proofs/public-abc123.json
  
  # Use custom verification key
  python verify_proof.py proof.json public.json --vkey my_vkey.json
"""
    )
    parser.add_argument(
        "proof",
        type=Path,
        help="Path to proof.json file"
    )
    parser.add_argument(
        "public",
        type=Path,
        help="Path to public.json file"
    )
    parser.add_argument(
        "--vkey",
        type=Path,
        default=VERIFICATION_KEY,
        help="Path to verification key (default: build/verification_key.json)"
    )
    
    args = parser.parse_args()
    
    try:
        # Display info
        display_proof_info(args.proof, args.public)
        
        # Verify
        print("  Verifying...")
        is_valid, output = verify_proof(args.proof, args.public, args.vkey)
        
        # Display result
        display_result(is_valid, output)
        
        return 0 if is_valid else 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
