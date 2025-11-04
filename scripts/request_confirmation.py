#!/usr/bin/env python3
"""
request_confirmation.py

Presents VCA to user for haptic consent confirmation.
This is the sovereignty layer - every action requires explicit human approval.

Usage:
    python request_confirmation.py --vca vca-xxxxxxxx

Example:
    python request_confirmation.py --vca vca-7e4d9a2f
"""

import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional

PROOFS_DIR = Path("proofs")


def load_vca(vca_id: str) -> Optional[Dict[str, Any]]:
    """Load VCA from proofs directory."""
    vca_file = PROOFS_DIR / f"{vca_id}.json"
    
    if not vca_file.exists():
        print(f"❌ Error: VCA not found: {vca_id}")
        print(f"   Expected: {vca_file}")
        return None
    
    return json.loads(vca_file.read_text())


def display_vca(vca: Dict[str, Any]):
    """Display VCA information to user."""
    print("\n" + "="*60)
    print("  🔔 VANGUARD CONFIRMATION REQUEST")
    print("="*60)
    print()
    
    # Intent
    print(f"  Intent: {vca['intent']}")
    if vca.get('task_data'):
        print(f"  Details: {vca['task_data']}")
    print()
    
    # Cognitive state
    cog_state = vca.get('cognitive_state', {})
    confidence = cog_state.get('confidence', 'N/A')
    threshold = cog_state.get('threshold', 'N/A')
    
    print(f"  Confidence: {confidence}%")
    print(f"  Threshold: {threshold}%")
    
    # Additional cognitive metrics if available
    if 'fatigue' in cog_state:
        print(f"  Fatigue: {cog_state['fatigue']}/100")
    if 'focus' in cog_state:
        print(f"  Focus: {cog_state['focus']}/100")
    if 'urgency' in cog_state:
        print(f"  Urgency: {cog_state['urgency']}/100")
    
    print()
    
    # Proof status
    zkp = vca.get('zkp', {})
    proof_verified = zkp.get('verified', False)
    
    if proof_verified:
        print(f"  Proof Status: ✓ VERIFIED (zk-SNARK)")
    else:
        print(f"  Proof Status: ⚠️  UNVERIFIED")
    
    print(f"  Proof Type: {zkp.get('type', 'unknown')}")
    print()
    
    # Metadata
    print(f"  VCA ID: {vca['vca_id']}")
    print(f"  Timestamp: {vca['timestamp']}")
    print()


def simulate_haptic_pulse():
    """Simulate haptic feedback (visual in CLI)."""
    print("  [HAPTIC_PULSE]")
    print("  ...buzz...")
    print()
    time.sleep(0.5)  # Brief pause for effect


def get_consent() -> str:
    """Get y/n consent from user."""
    print("="*60)
    print()
    
    while True:
        response = input("  Approve this action? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            return 'y'
        elif response in ['n', 'no']:
            return 'n'
        else:
            print("  ⚠️  Please enter 'y' or 'n'")


def update_vca_with_consent(vca: Dict[str, Any], response: str) -> Dict[str, Any]:
    """Add consent record to VCA."""
    vca['consent'] = {
        'haptic_delivered': True,
        'user_response': response,
        'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    # Save updated VCA
    vca_file = PROOFS_DIR / f"{vca['vca_id']}.json"
    vca_file.write_text(json.dumps(vca, indent=2))
    
    return vca


def display_result(response: str, vca: Dict[str, Any]):
    """Display outcome to user."""
    print()
    print("="*60)
    
    if response == 'y':
        print("  ✅ ACTION APPROVED")
        print("="*60)
        print()
        print(f"  The action has been approved and will be executed.")
        print(f"  VCA ID: {vca['vca_id']}")
        print()
        print(f"  Next step:")
        print(f"    python scripts/post_ledger.py --vca {vca['vca_id']}")
    else:
        print("  🛑 ACTION VETOED")
        print("="*60)
        print()
        print(f"  The action has been vetoed by user.")
        print(f"  No execution will occur.")
        print(f"  VCA ID: {vca['vca_id']}")
        print()
        print(f"  The veto has been recorded in the VCA.")
        print(f"  You can still post to ledger for audit trail:")
        print(f"    python scripts/post_ledger.py --vca {vca['vca_id']}")
    
    print()


def request_confirmation(vca_id: str) -> int:
    """
    Main consent flow.
    
    Returns:
        0 on success, 1 on error
    """
    # Load VCA
    vca = load_vca(vca_id)
    if not vca:
        return 1
    
    # Check if already has consent
    if 'consent' in vca:
        print(f"\n⚠️  Warning: This VCA already has a consent record:")
        print(f"   Response: {vca['consent']['user_response']}")
        print(f"   Timestamp: {vca['consent']['timestamp']}")
        print()
        
        response = input("  Request consent again? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("  Cancelled.")
            return 0
        print()
    
    # Display VCA
    display_vca(vca)
    
    # Haptic pulse
    simulate_haptic_pulse()
    
    # Get consent
    response = get_consent()
    
    # Update VCA
    vca = update_vca_with_consent(vca, response)
    
    # Display result
    display_result(response, vca)
    
    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Request human consent for VCA execution"
    )
    parser.add_argument(
        "--vca",
        type=str,
        required=True,
        help="VCA ID to request confirmation for"
    )
    
    args = parser.parse_args()
    
    try:
        return request_confirmation(args.vca)
    except KeyboardInterrupt:
        print("\n\n⚠️  Consent request cancelled by user.")
        print("   No action will be taken.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
