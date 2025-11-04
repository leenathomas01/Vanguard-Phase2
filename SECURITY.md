# Vanguard v2 Security Model

## Overview

Vanguard v2 uses cryptographic proofs (zk-SNARKs) to create verifiable records of cognitive actions. The security model has two phases:

- **Path A (Current):** Controlled setup - suitable for development and permissioned deployment
- **Path B (Future):** Trustless setup - suitable for public deployment and token-backed systems

This document explains both models, their trust assumptions, and the migration path between them.

**Terminology note:** *Path A ≡ v0.1 (Immediate Protection), Path B ≡ v2 (Cryptographic Sovereignty).*  
This document uses "Path A/B" for clarity; other docs may use `v0.1/ v2`.

---

## Table of Contents

1. [Trust Assumptions](#trust-assumptions)
2. [Threat Model](#threat-model)
3. [Path A: Controlled Setup](#path-a-controlled-setup)
4. [Path B: Trustless Setup](#path-b-trustless-setup)
5. [Attack Vectors & Mitigations](#attack-vectors--mitigations)
6. [Privacy Considerations](#privacy-considerations)
7. [Audit & Verification](#audit--verification)
8. [Migration Path](#migration-path)

---

## Trust Assumptions

### What Vanguard DOES Guarantee

✅ **Proof Integrity:** If a proof verifies, the confidence score genuinely met the threshold  
✅ **Consent Finality:** No action executes without explicit human approval  
* Timeouts: Absence of a human response MUST resolve to `timeout_no_consent` and be logged; execution is forbidden.  
✅ **Audit Trail:** Complete record from intent → proof → consent → outcome  
✅ **Tamper Evidence:** Any modification to proofs/ledger is detectable  
✅ **Privacy:** Zero-knowledge proofs don't expose raw cognitive data  

### What Vanguard DOES NOT Guarantee

❌ **Intent Authenticity:** System assumes input comes from legitimate user  
❌ **AI Correctness:** Edge AI classifier could be wrong about confidence  
❌ **Hardware Security:** Relies on secure execution environment  
❌ **Network Security:** Communication channels must be separately secured  

**Key insight:** Vanguard guarantees *verifiable sovereignty*, not perfect AI judgment.

**Security invariant:** *No proof ⇒ no consent ⇒ no execution.*  
If any one is missing, the system MUST deterministically perform **no action** and log the reason.

---

## Threat Model

### In-Scope Threats

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Fake Proofs** | Attacker generates proof with false confidence | zk-SNARK verification fails |
| **Proof Tampering** | Modify proof after generation | Verification fails (cryptographic binding) |
| **Ledger Manipulation** | Alter historical records | Append-only + hash chain (future) |
| **Consent Bypass** | Execute action without approval | Architecture prevents (no code path exists) |
| **Replay Attacks** | Reuse old proof for new action | Timestamp + nonce in VCA |

### Out-of-Scope Threats

| Threat | Why Out of Scope | Future Work |
|--------|------------------|-------------|
| **Compromised Hardware** | Assumes trusted execution environment | TEE integration |
| **Social Engineering** | User approves malicious intent | User responsibility |
| **AI Model Poisoning** | Edge AI trained on bad data | Model provenance |
| **Side-Channel Attacks** | Timing/power analysis | Hardware countermeasures |

*Scale:* Likelihood = Low / Med / High, Impact = Low / Med / High.

---

## Path A: Controlled Setup

**Current implementation** - suitable for development, testing, and permissioned deployment.

### Setup Process

```bash
# 1. Generate Powers of Tau (locally)
snarkjs powersoftau new bn128 12 pot12_final.ptau

# 2. Contribute randomness (single party)
snarkjs powersoftau contribute pot12_final.ptau pot12_final.ptau

# 3. Create circuit-specific setup
snarkjs groth16 setup circuit.r1cs pot12_final.ptau circuit.zkey

# 4. Export verification key
snarkjs zkey export verificationkey circuit.zkey verification_key.json
```

### Trust Assumptions

**You must trust:**
- Repository maintainer (me/Zee) generated setup honestly
- Setup randomness was not saved/leaked
- Verification key in repo matches the circuit

**You do NOT need to trust:**
- Anyone generating individual proofs (verified cryptographically)
- The ledger maintainer (proofs are independently verifiable)
- Network infrastructure (proofs verified locally)

### Suitable For

✅ Personal use (you trust yourself)  
✅ Small teams (you trust the admin)  
✅ Development/testing (security not critical)  
✅ Permissioned systems (known participants)  

❌ Public deployment (trust is centralized)  
❌ Token-backed systems (value at risk)  
❌ Adversarial environments (single point of failure)  

---

## Path B: Trustless Setup

**Future implementation** - suitable for public deployment and high-stakes use.

### Setup Process

#### Option 1: Multi-Party Ceremony (MPC)

```bash
# Phase 1: Powers of Tau (shared ceremony)
# Each participant adds entropy
participant_1: contribute_randomness() → ptau_1
participant_2: contribute_randomness() → ptau_2
participant_N: contribute_randomness() → ptau_N

# Phase 2: Circuit-specific setup
coordinator: groth16_setup(circuit, ptau_N) → zkey

# Phase 3: Verification
all_participants: verify_ceremony_transcript()
```

**Trust requirement:** At least ONE participant must be honest (1-of-N security)

#### Option 2: Use Public Ceremony

```bash
# Use existing trusted ceremony (e.g., Hermez)
wget https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_21.ptau

# Create circuit-specific setup
snarkjs groth16 setup circuit.r1cs powersOfTau28_hez_final_21.ptau circuit.zkey

# Verify against ceremony attestation
snarkjs zkey verify circuit.r1cs powersOfTau28_hez_final_21.ptau circuit.zkey
```

**Trust requirement:** Believe Hermez ceremony was conducted honestly (widely reviewed)

#### Option 3: STARKs (No Trusted Setup)

```bash
# Future: Replace Groth16 with STARK-based proof
# No setup ceremony needed
# Larger proof size but no trust assumptions
```

### Trust Assumptions

**You must trust:**
- At least one MPC participant was honest, OR
- Public ceremony (Hermez, etc.) was not fully compromised, OR
- STARK implementation is correct (if using Option 3)

**You do NOT need to trust:**
- Any single party (distributed trust)
- The circuit author (circuit code is public)
- Future proof generators (cryptographically verified)

### Suitable For

✅ Public deployment (no centralized trust)  
✅ Token-backed systems (VGT has real value)  
✅ DAO governance (community-controlled)  
✅ Adversarial environments (cryptographic security)  

---

## Attack Vectors & Mitigations

### 1. Malicious Proof Generation

**Attack:** Attacker tries to generate proof with false confidence score

**Example:**
```json
// Attacker claims confidence=95 but actual confidence=80
{"confidence": 9500, "threshold": 9200}
```

**Mitigation:**
- zk-SNARK circuit enforces constraint: `confidence >= threshold`
- If attacker lies about inputs, proof generation fails OR verification fails
- **Result:** Attack prevented by cryptography

**Severity:** 🟢 Low (cryptographically infeasible)

---

### 2. Replay Attacks

**Attack:** Reuse old VCA/proof for different action

**Example:**
**Mitigation:**  
Proofs are bound to a specific action via  
`intentHash = Poseidon(intentPreimage, nonce)` as a **public input**.  
Each VCA includes a unique ID and timestamp; the ledger rejects duplicate VCA IDs.  

**Status:** ✅ Covered  
**Spec:** See [./v2/docs/INTENT_CANON.md](./v2/docs/INTENT_CANON.md)

```json
// Example of bound proof metadata
{
  "vca_id": "vca-7e4d9a2f",
  "intentHash": "0x9af...d02",
  "nonce": "0x01a4",
  "timestamp": "2025-10-26T18:42:13Z"
}
```

**Result:** Replay attacks cryptographically prevented.

---

### 3. Consent Bypass

**Attack:** Execute action without waiting for human approval

**Example:**
```python
# Attacker tries to skip request_confirmation.py
post_ledger(vca)  # Direct execution
```

**Mitigation:**
- `post_ledger.py` checks for consent signature
- VCA without consent field is rejected
- No code path allows execution without approval

**Experimental: Consent Signature**  
Gate behavior: When `CONSENT_SIG_REQUIRED=true`, any ledger post without a valid Ed25519 consent artifact MUST be rejected with a non-zero exit code (`POST_LEDGER_ERR_NO_CONSENT_SIG`).

**Timeouts:** Lack of response MUST resolve to `timeout_no_consent`; ledger MUST reject execution attempts for timed-out VCAs.


**Severity:** 🟢 Low (architecture prevents it)

---

### 4. Ledger Tampering

**Attack:** Modify historical ledger entries

**Example:**
```json
// Change "vetoed" to "executed" after the fact
{"action": "executed"}  // was "vetoed"
```

**Mitigation (Current):**
- Git history (if using version control)
- File system timestamps
- Periodic ledger hash snapshots

**Mitigation (Future):**
- Hash chain: each entry contains hash of previous
- Blockchain backend: immutable by design
- Merkle tree: efficient verification of history

**Status:** 🟡 Weak (JSON file is mutable)

**TODO:** Implement hash chain in ledger entries

---

### 5. Trusted Setup Backdoor

**Attack:** Setup ceremony participant saves secret randomness

**Impact:** Could generate fake proofs that verify correctly

**Path A Risk:** 🔴 High (single party setup)

**Path B Mitigation:**
- Multi-party ceremony: ALL participants must be corrupt
- 1-of-N security: very hard to compromise
- Public ceremony: widely reviewed by community

**Status:** Acknowledged risk in Path A, resolved in Path B

---

### 6. Side-Channel Attacks

**Attack:** Extract secrets via timing/power/EM analysis

**Example:**
- Measure proof generation time to infer confidence score
- Power analysis during key operations

**Mitigation:**
- Constant-time operations (Circom best practices)
- Hardware countermeasures (TEE, secure enclaves)
- Blinding factors in proofs

**Status:** 🟡 Depends on deployment environment

**TODO:** Add blinding factors to circuit

---

### 7. Service Abuse / DoS (operational)

**Risk:** Unbounded proof requests can exhaust CPU.

**Mitigation (v0.1):** Per-process rate limits and concurrency caps in CLI/daemon configs.

**Mitigation (v2.1):** Token-bucket + back-pressure; optional stake-gated API for hosted deployments.

---

## Privacy Considerations

### What's Private

✅ **Raw Cognitive Data:** Never exposed in proofs  
✅ **Exact Confidence Score:** Proof only shows ≥ threshold  
✅ **Internal AI State:** Edge AI details not revealed  

### What's Public

📢 **Intent Summary:** "Schedule meeting with DAO" (by design)  
📢 **Proof Existence:** That a valid proof was generated  
📢 **Consent Decision:** y/n response (audit requirement)  
📢 **Timestamp:** When action occurred  

### Privacy Enhancement Options

**Option 1: Encrypted Intents**
```json
{
  "intent_hash": "0x7f8e9d...",  // Public
  "intent_encrypted": "...",      // Only user can decrypt
  "proof": {...}
}
```

**Option 2: Private Ledger**
- Store ledger entries on private chain
- Only participant nodes can read
- zk-Rollups for public settlements

**Option 3: Selective Disclosure**
- Prove properties about VCAs without revealing details
- "I have 10 approved VCAs" without showing which ones

---

## Supply Chain & Reproducible Builds (v0.1 → v2.1)

* **Pin toolchains:** Record exact versions (Node, snarkjs, circom) in `BUILD.md`.
* **Checksums:** Publish SHA-256 for `circuit.r1cs`, `*.zkey`, and `verification_key.json` in releases.
* **Deterministic builds (planned):** Document reproducible steps and compare artifact hashes (v2.1).
* **Provenance (planned):** Consider SLSA-style provenance attestations for release artifacts (v2.1).

---

## Audit & Verification

### Independent Verification

Anyone can verify a VCA:

```bash
# 1. Get verification key (from repo or chain)
wget https://vanguard.io/verification_key.json

# 2. Verify the proof
snarkjs groth16 verify \
  verification_key.json \
  vca-7e4d9a2f/public.json \
  vca-7e4d9a2f/proof.json

# Output: OK! or INVALID
```

### Audit Checklist

**Circuit Audit:**
- [ ] Review `intent_threshold.circom` for logic bugs
- [ ] Verify constraints enforce intended properties
- [ ] Check for under-constrained signals
- [ ] Test edge cases (confidence = threshold exactly)

**Setup Audit:**
- [ ] Verify Powers of Tau ceremony transcript
- [ ] Check participant contributions (Path B)
- [ ] Validate verification key derivation
- [ ] Reproduce setup from source

**Implementation Audit:**
- [ ] Review proof generation code
- [ ] Check consent loop for bypass vulnerabilities
- [ ] Verify ledger integrity checks
- [ ] Test replay attack mitigations

---

## Migration Path

### Path A → Path B Timeline

**Phase 1: Development (Current)**
- Local trusted setup
- JSON ledger
- CLI consent interface
- **Duration:** Q4 2025

**Phase 2: Hardening**
- Implement hash chain in ledger
- Add commitment binding to proofs
- Deploy browser UI
- **Duration:** Q1 2026

**Phase 3: MPC Ceremony**
- Organize multi-party setup
- Minimum 10 participants
- Public transcript + verification
- **Duration:** Q2 2026

**Phase 4: Testnet Deployment**
- Deploy to Arbitrum Sepolia
- On-chain verification contracts
- Test VGT token mechanics
- **Duration:** Q3 2026

**Phase 5: Mainnet (Path B Complete)**
- Final security audit
- Deploy to Arbitrum One
- Enable public VGT minting
- **Duration:** Q4 2026

### Migration Checklist

- [ ] Complete circuit audit (external firm)
- [ ] Run MPC ceremony with >10 participants
- [ ] Deploy verification contracts to testnet
- [ ] Conduct public bug bounty program
- [ ] Publish ceremony transcript + verification
- [ ] Migrate existing VCAs to new setup (optional)

---

## Security Best Practices

### For Developers

1. **Never log private keys or randomness**
2. **Use constant-time operations in circuits**
3. **Validate all inputs before proof generation**
4. **Implement rate limiting on proof requests**
5. **Store verification keys securely (not in env vars)**

### For Users

1. **Verify proofs before approving actions**
2. **Check ledger for unexpected entries**
3. **Use hardware wallet for future VGT transactions**
4. **Report suspicious VCAs immediately**
5. **Participate in setup ceremonies if possible**

### For Auditors

1. **Review circuit constraints exhaustively**
2. **Test with malicious inputs**
3. **Verify ceremony transcripts**
4. **Check for side-channel vulnerabilities**
5. **Assess economic incentive alignment**

---

## Incident Response

### If Fake Proof Detected

1. **Verify:** Re-run verification on suspicious proof
2. **Isolate:** Flag VCA in ledger as disputed
3. **Investigate:** Trace back to proof generation
4. **Communicate:** Notify community immediately
5. **Patch:** Update circuit/code if bug found

### If Setup Compromised

1. **Assess Impact:** Which proofs are affected?
2. **New Ceremony:** Run fresh MPC setup
3. **Migration:** Re-generate proofs with new keys
4. **Disclosure:** Full transparency on what happened
5. **Compensation:** If tokens affected, handle via DAO

---

## Open Questions

1. **Should we support proof delegation?**
   - Alice generates proof, Bob approves?
   - Enables multi-sig-like workflows
   - Adds complexity to consent model

2. **How to handle hardware failures?**
   - What if user loses consent device?
   - Recovery mechanism needed?
   - Balance between security and usability

3. **Cross-chain verification?**
   - Deploy verification to multiple chains?
   - Bridge VGT across ecosystems?
   - Increases attack surface

4. **Quantum resistance?**
   - Current setup not quantum-safe
   - Migration path to post-quantum crypto?
   - Timeline: 5-10 years (monitor NIST standards)

---

## Conclusion

**Vanguard's security model is layered:**

1. **Cryptographic Layer:** zk-SNARKs prevent fake proofs
2. **Consent Layer:** Human veto cannot be bypassed
3. **Audit Layer:** Complete trail from intent to outcome
4. **Trust Layer:** Path A (you trust setup) → Path B (distributed trust)

**Current status:**
- Path A is secure for intended use cases (dev, permissioned)
- Path B is designed and ready for implementation
- Migration is incremental and well-defined

**The goal:**
- Make cognitive sovereignty both *verifiable* and *trustless*
- No single point of failure
- Full transparency + cryptographic guarantees

---

**Security is not a feature. It's the foundation.**

For questions or security concerns, open an issue or contact: [security@vanguard.io]

---

**Related Documentation:**
- [← Back to Vanguard README](./README.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Development Roadmap](./ROADMAP.md)
- [Intent Canonicalization](./v2/docs/INTENT_CANON.md)
