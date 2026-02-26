# @credverse/audit-log

Tamper-evident append-only transparency log with Merkle tree inclusion proofs for the CredVerse ecosystem.

## Overview

This package provides an append-only log that chains entries with SHA-256 hashes and builds a Merkle tree over all entries. It supports:

- **Hash-chained entries** — each entry references the hash of its predecessor, making tampering detectable.
- **Merkle inclusion proofs** — prove that a specific entry exists in the log without revealing other entries.
- **Integrity verification** — scan the log for chain breaks, hash mismatches, and timestamp reordering.

The design follows the transparency log pattern (similar to Sigstore Rekor / Certificate Transparency) and extends the basic audit chain in `@credverse/shared-auth`.

## Installation

```bash
npm install @credverse/audit-log
```

## Usage

### Creating a log and appending entries

```typescript
import { createTransparencyLog } from '@credverse/audit-log';

const log = createTransparencyLog();

const entry = log.append({
  timestamp: new Date().toISOString(),
  entryType: 'issuance',
  actorId: 'issuer-001',
  action: 'credential.issue',
  resourceId: 'cred-abc-123',
  resourceType: 'VerifiableCredential',
  payload: { credentialType: 'UniversityDegree', holder: 'did:example:holder' },
});

console.log(entry.index);        // 0
console.log(entry.entryHash);    // SHA-256 hex digest
console.log(entry.previousHash); // '0000…0000' (genesis)
```

### Verifying log integrity

```typescript
const result = log.verifyIntegrity();

if (result.valid) {
  console.log(`All ${result.entriesChecked} entries are valid.`);
} else {
  for (const err of result.errors) {
    console.error(`Entry ${err.index}: ${err.type}`);
  }
}
```

### Generating and verifying inclusion proofs

```typescript
// Generate a proof that entry 0 is in the log
const proof = log.getInclusionProof(0);

if (proof) {
  const verification = log.verifyInclusionProof(proof);
  console.log(verification.verified); // true
  console.log(verification.rootHash); // current Merkle root
}
```

### Tamper detection

```typescript
// Any modification to a stored entry will be caught by verifyIntegrity()
// because the recomputed hash will not match the stored entryHash,
// and downstream entries will have broken previousHash chains.
```

## API

### `createTransparencyLog(): TransparencyLog`

Creates an in-memory transparency log.

### `TransparencyLog` interface

| Method | Description |
|---|---|
| `append(entry)` | Append a new entry; returns the complete `LogEntry` with computed hashes |
| `getEntry(index)` | Retrieve a single entry by index |
| `getEntries(from?, to?)` | Retrieve a slice of entries |
| `getLatest()` | Get the most recent entry |
| `size()` | Number of entries in the log |
| `getRootHash()` | Current Merkle root hash |
| `getInclusionProof(index)` | Generate a Merkle inclusion proof for an entry |
| `verifyInclusionProof(proof)` | Verify a previously generated inclusion proof |
| `verifyIntegrity(from?, to?)` | Verify hash chain and timestamp ordering |

### Merkle utilities

| Function | Description |
|---|---|
| `computeLeafHash(data)` | SHA-256 with `0x00` leaf prefix |
| `computeNodeHash(left, right)` | SHA-256 with `0x01` node prefix |
| `buildMerkleTree(leaves)` | Build a balanced Merkle tree |
| `computeMerkleRoot(leaves)` | Compute the root hash |
| `generateInclusionProof(leaves, index)` | Generate a proof path |
| `verifyInclusionProof(leafHash, proof, rootHash)` | Verify a proof path |

## Design decisions

- **RFC 8785 canonicalization** — Entry data is canonicalized (sorted keys, deterministic JSON) before hashing for reproducibility.
- **Domain-separated hashing** — Leaf and internal Merkle nodes use different prefixes (`0x00` / `0x01`) to prevent second-preimage attacks.
- **Power-of-2 padding** — The Merkle tree duplicates the last leaf to reach a power-of-two size for a balanced tree.
- **Genesis hash** — The first entry uses 64 zero characters as its `previousHash`.
- **In-memory by default** — The `TransparencyLog` interface is designed for easy extension to persistent backends (database, file system) by implementing the same interface.
