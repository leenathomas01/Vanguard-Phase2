#!/usr/bin/env python3
"""
post_ledger.py

Posts VCA to the ledger, creating an immutable audit trail.
Records both approved and vetoed actions for complete transparency.

Usage:
    python post_ledger.py --vca vca-xxxxxxxx

Example:
    python post_ledger.py --vca vca-7e4d9a2f
"""

import json
import argparse
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

PROOFS_DIR = Path("proofs")
LEDGER_FILE = Path("ledger.json")


def load_vca(vca_id: str) -> Optional[Dict[str, Any]]:
    """Load VCA from proofs directory."""
    vca_file = PROOFS_DIR / f"{vca_id}.json"
    
    if not vca_file.exists():
        print(f"❌ Error: VCA not found: {vca_id}")
        return None
    
    return json.loads(vca_file.read_text())


def load_ledger() -> List[Dict[str, Any]]:
    """Load existing ledger or create new one."""
    if LEDGER_FILE.exists():
        return json.loads(LEDGER_FILE.read_text())
    return []


def save_ledger(ledger: List[Dict[str, Any]]):
    """Save ledger to disk."""
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2))


def compute_proof_hash(vca: Dict[str, Any]) -> str:
    """Compute hash of proof for ledger entry."""
    zkp = vca.get('zkp', {})
    proof_data = zkp.get('proof', {})
    
    # Serialize and hash proof
    proof_str = json.dumps(proof_data, sort_keys=True)
    return hashlib.sha256(proof_str.encode()).hexdigest()


def generate_tx_id(ledger: List[Dict[str, Any]]) -> str:
    """Generate transaction ID based on ledger length."""
    tx_number = len(ledger) + 1
    return f"tx-{tx_number:06d}"


def create_ledger_entry(vca: Dict[str, Any], tx_id: str) -> Dict[str, Any]:
    """Create ledger entry from VCA."""
    consent = vca.get('consent', {})
    user_response = consent.get('user_response', 'unknown')
    
    # Determine action and status
    if user_response == 'y':
        action = 'execute'
        status = 'executed'
    elif user_response == 'n':
        action = 'veto'
        status = 'vetoed'
    else:
        action = 'unknown'
        status = 'pending'
    
    entry = {
        'tx_id': tx_id,
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'action': action,
        'vca_id': vca['vca_id'],
        'intent': vca['intent'],
        'proof_hash': compute_proof_hash(vca),
        'human_consent': user_response,
        'status': status,
        'cognitive_state': vca.get('cognitive_state', {}),
        'metadata': {
            'proof_type': vca.get('zkp', {}).get('type', 'unknown'),
            'verified': vca.get('zkp', {}).get('verified', False),
            'consent_timestamp': consent.get('timestamp', 'unknown')
        }
    }
    
    return entry


def check_duplicate(ledger: List[Dict[str, Any]], vca_id: str) -> bool:
    """Check if VCA already posted to ledger."""
    return any(entry['vca_id'] == vca_id for entry in ledger)


def display_entry(entry: Dict[str, Any]):
    """Display ledger entry to user."""
    print("\n" + "="*60)
    print("  📋 LEDGER ENTRY")
    print("="*60)
    print()
    
    print(f"  Transaction ID: {entry['tx_id']}")
    print(f"  VCA ID: {entry['vca_id']}")
    print(f"  Timestamp: {entry['timestamp']}")
    print()
    
    print(f"  Intent: {entry['intent']}")
    print(f"  Action: {entry['action']}")
    print(f"  Status: {entry['status']}")
    print()
    
    print(f"  Human Consent: {entry['human_consent']}")
    print(f"  Proof Hash: {entry['proof_hash'][:16]}...")
    print()
    
    cog = entry.get('cognitive_state', {})
    if cog:
        print(f"  Confidence: {cog.get('confidence', 'N/A')}%")
        if 'fatigue' in cog:
            print(f"  Fatigue: {cog['fatigue']}/100")
        if 'focus' in cog:
            print(f"  Focus: {cog['focus']}/100")
        if 'urgency' in cog:
            print(f"  Urgency: {cog['urgency']}/100")
        print()
    
    print("="*60)
    print()


def calculate_vgt_reward(entry: Dict[str, Any]) -> int:
    """Calculate VGT reward for this action."""
    # Simple reward calculation
    if entry['status'] == 'executed':
        cog = entry.get('cognitive_state', {})
        confidence = cog.get('confidence', 0)
        
        # Higher confidence = higher reward
        if confidence >= 95:
            return 10
        elif confidence >= 90:
            return 5
        else:
            return 3
    else:
        # No reward for vetoed actions
        return 0


def post_to_ledger(vca_id: str) -> int:
    """
    Main ledger posting flow.
    
    Returns:
        0 on success, 1 on error
    """
    # Load VCA
    vca = load_vca(vca_id)
    if not vca:
        return 1
    
    # Check for consent
    if 'consent' not in vca:
        print("\n❌ Error: VCA does not have consent record.")
        print("   Run: python scripts/request_confirmation.py --vca", vca_id)
        return 1
    
    # Load ledger
    ledger = load_ledger()
    
    # Check for duplicates
    if check_duplicate(ledger, vca_id):
        print(f"\n⚠️  Warning: VCA {vca_id} already in ledger")
        
        response = input("  Post anyway? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("  Cancelled.")
            return 0
        print()
    
    # Generate transaction ID
    tx_id = generate_tx_id(ledger)
    
    # Create entry
    entry = create_ledger_entry(vca, tx_id)
    
    # Calculate VGT
    vgt_reward = calculate_vgt_reward(entry)
    entry['vgt_reward'] = vgt_reward
    
    # Append to ledger
    ledger.append(entry)
    
    # Save ledger
    save_ledger(ledger)
    
    # Display
    display_entry(entry)
    
    # Summary
    if entry['status'] == 'executed':
        print(f"  ✅ Action executed successfully")
        print(f"  💰 VGT Earned: +{vgt_reward}")
    else:
        print(f"  🛑 Action vetoed by user")
        print(f"  💰 VGT Earned: 0")
    
    print()
    print(f"  Ledger updated: {LEDGER_FILE}")
    print(f"  Total entries: {len(ledger)}")
    print()
    
    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Post VCA to immutable ledger"
    )
    parser.add_argument(
        "--vca",
        type=str,
        required=True,
        help="VCA ID to post to ledger"
    )
    
    args = parser.parse_args()
    
    try:
        return post_to_ledger(args.vca)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
