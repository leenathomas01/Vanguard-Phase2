#!/usr/bin/env python3
"""
batch_mint.py

Demonstrates batch VCA generation for scalability testing (Sim 004).
Generates multiple proofs and shows gas savings via rollup-style batching.

Usage:
    python batch_mint.py [--count 10] [--base-confidence 94.0]

Example:
    python batch_mint.py --count 10 --base-confidence 94.0
"""

import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Import from enhanced_generate_proof
import sys
sys.path.insert(0, str(Path(__file__).parent))
from enhanced_generate_proof import generate_real_proof

PROOFS_DIR = Path("proofs")
LEDGER_FILE = Path("ledger.json")


def generate_batch_intents(count: int) -> List[tuple[str, str]]:
    """Generate sample intents for batch processing."""
    intents = [
        ("Approve email to team", "Send project update email"),
        ("Schedule standup meeting", "Book 15min daily sync"),
        ("Review pull request", "Code review for feature X"),
        ("Update documentation", "Add API examples to README"),
        ("Respond to Slack message", "Answer technical question"),
        ("Create calendar event", "Block focus time tomorrow"),
        ("Archive completed tasks", "Clean up task board"),
        ("Send meeting notes", "Distribute notes from planning session"),
        ("Update project timeline", "Adjust milestones in tracker"),
        ("Approve expense report", "Sign off on team lunch expense"),
    ]
    
    # Cycle through intents if count > len(intents)
    return [intents[i % len(intents)] for i in range(count)]


def batch_mint(count: int, base_confidence: float, threshold: float = 92.0) -> List[Dict[str, Any]]:
    """
    Generate batch of VCAs with incremental confidence scores.
    
    Args:
        count: Number of VCAs to generate
        base_confidence: Starting confidence (will increment)
        threshold: Minimum threshold for all proofs
    
    Returns:
        List of VCA objects
    """
    print("\n" + "="*60)
    print(f"  🔨 BATCH MINT - Simulation 004")
    print("="*60)
    print()
    print(f"  Generating {count} VCAs...")
    print(f"  Base confidence: {base_confidence}%")
    print(f"  Threshold: {threshold}%")
    print()
    
    intents = generate_batch_intents(count)
    vcas = []
    
    start_time = time.time()
    
    for i in range(count):
        # Increment confidence slightly for variety
        confidence = base_confidence + (i * 0.1)
        intent, task_data = intents[i]
        
        print(f"  [{i+1}/{count}] Generating VCA...")
        print(f"    Intent: {intent}")
        print(f"    Confidence: {confidence}%")
        
        try:
            vca = generate_real_proof(
                confidence_percent=confidence,
                threshold_percent=threshold,
                intent=intent,
                task_data=task_data
            )
            vcas.append(vca)
            print(f"    ✓ VCA created: {vca['vca_id']}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
        
        print()
    
    elapsed = time.time() - start_time
    
    print("="*60)
    print(f"  ✅ BATCH COMPLETE")
    print("="*60)
    print()
    print(f"  VCAs generated: {len(vcas)}")
    print(f"  Time elapsed: {elapsed:.2f}s")
    print(f"  Average per VCA: {elapsed/len(vcas):.2f}s")
    print()
    
    return vcas


def create_rollup_entry(vcas: List[Dict[str, Any]], batch_id: str) -> Dict[str, Any]:
    """Create single rollup ledger entry for batch."""
    total_confidence = sum(vca['cognitive_state']['confidence'] for vca in vcas)
    avg_confidence = total_confidence / len(vcas)
    
    entry = {
        "batch_id": batch_id,
        "tx_id": f"rollup-{batch_id}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "action": "batch_rollup",
        "vca_count": len(vcas),
        "vca_ids": [vca['vca_id'] for vca in vcas],
        "total_confidence_avg": round(avg_confidence, 2),
        "status": "pending_confirmation",
        "metadata": {
            "individual_proofs": True,
            "gas_savings_vs_individual": "87%",
            "vgt_amortized": True
        }
    }
    
    return entry


def simulate_gas_savings(vca_count: int) -> Dict[str, Any]:
    """Simulate gas savings from batching."""
    # Simulated gas costs
    individual_gas = 150000  # per tx
    batch_overhead = 50000   # batch setup
    per_item_gas = 20000     # per VCA in batch
    
    individual_total = individual_gas * vca_count
    batch_total = batch_overhead + (per_item_gas * vca_count)
    
    savings = individual_total - batch_total
    savings_percent = (savings / individual_total) * 100
    
    return {
        "individual_cost": individual_total,
        "batch_cost": batch_total,
        "savings": savings,
        "savings_percent": round(savings_percent, 1)
    }


def display_batch_summary(vcas: List[Dict[str, Any]], rollup_entry: Dict[str, Any]):
    """Display batch processing summary."""
    gas = simulate_gas_savings(len(vcas))
    
    print("="*60)
    print("  📊 BATCH SUMMARY")
    print("="*60)
    print()
    
    print(f"  Batch ID: {rollup_entry['batch_id']}")
    print(f"  VCAs in batch: {len(vcas)}")
    print(f"  Average confidence: {rollup_entry['total_confidence_avg']}%")
    print()
    
    print(f"  Gas Analysis:")
    print(f"    Individual txs: {gas['individual_cost']:,} gas")
    print(f"    Batch rollup: {gas['batch_cost']:,} gas")
    print(f"    Savings: {gas['savings']:,} gas ({gas['savings_percent']}%)")
    print()
    
    print(f"  VGT Distribution:")
    print(f"    Individual model: +{len(vcas) * 5} VGT total")
    print(f"    Amortized model: +3 VGT (batching incentive)")
    print()
    
    print(f"  Next steps:")
    print(f"    1. Batch approval:")
    print(f"       python scripts/request_batch_confirmation.py --batch {rollup_entry['batch_id']}")
    print(f"    2. Individual approvals:")
    for i, vca in enumerate(vcas[:3]):  # Show first 3
        print(f"       python scripts/request_confirmation.py --vca {vca['vca_id']}")
    if len(vcas) > 3:
        print(f"       ... and {len(vcas) - 3} more")
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch VCA generation for scalability testing (Sim 004)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of VCAs to generate (default: 10)"
    )
    parser.add_argument(
        "--base-confidence",
        type=float,
        default=94.0,
        help="Base confidence score (default: 94.0)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=92.0,
        help="Threshold for all proofs (default: 92.0)"
    )
    
    args = parser.parse_args()
    
    try:
        # Generate batch
        vcas = batch_mint(args.count, args.base_confidence, args.threshold)
        
        if not vcas:
            print("❌ No VCAs generated")
            return 1
        
        # Create rollup entry
        batch_id = f"batch-{int(time.time())}"
        rollup_entry = create_rollup_entry(vcas, batch_id)
        
        # Save rollup entry
        rollup_file = PROOFS_DIR / f"{batch_id}.json"
        rollup_file.write_text(json.dumps(rollup_entry, indent=2))
        
        # Display summary
        display_batch_summary(vcas, rollup_entry)
        
        print("="*60)
        print(f"  ✅ Sim 004 Complete: {len(vcas)} VCAs minted")
        print("="*60)
        print()
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
