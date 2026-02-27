import { describe, it, expect } from 'vitest';
import {
  computeLeafHash,
  computeNodeHash,
  buildMerkleTree,
  computeMerkleRoot,
  generateInclusionProof,
  verifyInclusionProof,
  createTransparencyLog,
} from '../src/index.js';

// ── Helper ──────────────────────────────────────────────────────────────────

function makeEntry(overrides: Record<string, unknown> = {}) {
  return {
    timestamp: new Date().toISOString(),
    entryType: 'issuance' as const,
    actorId: 'actor-1',
    action: 'issue_credential',
    resourceId: 'cred-1',
    resourceType: 'credential',
    payload: { foo: 'bar' },
    ...overrides,
  };
}

// ── Merkle Tree ─────────────────────────────────────────────────────────────

describe('Merkle tree primitives', () => {
  it('computeLeafHash returns a 64-char hex string', () => {
    const h = computeLeafHash('hello');
    expect(h).toMatch(/^[0-9a-f]{64}$/);
  });

  it('computeLeafHash is deterministic', () => {
    expect(computeLeafHash('data')).toBe(computeLeafHash('data'));
  });

  it('computeNodeHash returns a 64-char hex string', () => {
    const a = computeLeafHash('a');
    const b = computeLeafHash('b');
    expect(computeNodeHash(a, b)).toMatch(/^[0-9a-f]{64}$/);
  });

  it('computeNodeHash is order-dependent', () => {
    const a = computeLeafHash('a');
    const b = computeLeafHash('b');
    expect(computeNodeHash(a, b)).not.toBe(computeNodeHash(b, a));
  });
});

describe('buildMerkleTree', () => {
  it('returns null for empty leaves', () => {
    expect(buildMerkleTree([])).toBeNull();
  });

  it('builds a tree with one leaf', () => {
    const leaf = computeLeafHash('only');
    const tree = buildMerkleTree([leaf]);
    expect(tree).not.toBeNull();
    expect(tree!.hash).toBe(leaf);
  });

  it('builds a balanced tree with multiple leaves', () => {
    const leaves = ['a', 'b', 'c', 'd'].map(computeLeafHash);
    const tree = buildMerkleTree(leaves);
    expect(tree).not.toBeNull();
    expect(tree!.left).toBeDefined();
    expect(tree!.right).toBeDefined();
  });
});

describe('computeMerkleRoot', () => {
  it('returns all-zeros for empty leaves', () => {
    expect(computeMerkleRoot([])).toBe('0'.repeat(64));
  });

  it('returns leaf hash for single leaf', () => {
    const leaf = computeLeafHash('single');
    expect(computeMerkleRoot([leaf])).toBe(leaf);
  });

  it('is deterministic', () => {
    const leaves = ['x', 'y'].map(computeLeafHash);
    expect(computeMerkleRoot(leaves)).toBe(computeMerkleRoot(leaves));
  });
});

describe('inclusion proofs', () => {
  it('returns empty proof for out-of-bounds index', () => {
    const leaves = ['a'].map(computeLeafHash);
    expect(generateInclusionProof(leaves, 5)).toEqual([]);
    expect(generateInclusionProof(leaves, -1)).toEqual([]);
  });

  it('generates and verifies proof for each leaf in a 4-leaf tree', () => {
    const leaves = ['a', 'b', 'c', 'd'].map(computeLeafHash);
    const root = computeMerkleRoot(leaves);

    for (let i = 0; i < leaves.length; i++) {
      const proof = generateInclusionProof(leaves, i);
      expect(proof.length).toBeGreaterThan(0);
      expect(verifyInclusionProof(leaves[i], proof, root)).toBe(true);
    }
  });

  it('rejects proof with wrong leaf hash', () => {
    const leaves = ['a', 'b'].map(computeLeafHash);
    const root = computeMerkleRoot(leaves);
    const proof = generateInclusionProof(leaves, 0);
    const fakeLeaf = computeLeafHash('fake');
    expect(verifyInclusionProof(fakeLeaf, proof, root)).toBe(false);
  });

  it('rejects proof with wrong root hash', () => {
    const leaves = ['a', 'b'].map(computeLeafHash);
    const proof = generateInclusionProof(leaves, 0);
    expect(verifyInclusionProof(leaves[0], proof, '0'.repeat(64))).toBe(false);
  });
});

// ── Transparency Log ────────────────────────────────────────────────────────

describe('TransparencyLog', () => {
  it('starts empty', () => {
    const log = createTransparencyLog();
    expect(log.size()).toBe(0);
    expect(log.getLatest()).toBeNull();
    expect(log.getEntry(0)).toBeNull();
  });

  it('appends entries with auto-computed index and hashes', () => {
    const log = createTransparencyLog();
    const e1 = log.append(makeEntry());
    const e2 = log.append(makeEntry({ action: 'verify_credential' }));

    expect(e1.index).toBe(0);
    expect(e2.index).toBe(1);
    expect(e1.entryHash).toMatch(/^[0-9a-f]{64}$/);
    expect(e2.previousHash).toBe(e1.entryHash);
    expect(log.size()).toBe(2);
  });

  it('first entry links to genesis hash', () => {
    const log = createTransparencyLog();
    const e = log.append(makeEntry());
    expect(e.previousHash).toBe('0'.repeat(64));
  });

  it('getEntry / getEntries / getLatest return correct data', () => {
    const log = createTransparencyLog();
    log.append(makeEntry());
    log.append(makeEntry({ action: 'revoke' }));
    log.append(makeEntry({ action: 'present' }));

    expect(log.getEntry(1)!.action).toBe('revoke');
    expect(log.getEntries(1, 3)).toHaveLength(2);
    expect(log.getLatest()!.index).toBe(2);
  });

  describe('integrity verification', () => {
    it('passes on untampered log', () => {
      const log = createTransparencyLog();
      log.append(makeEntry());
      log.append(makeEntry());
      log.append(makeEntry());

      const result = log.verifyIntegrity();
      expect(result.valid).toBe(true);
      expect(result.entriesChecked).toBe(3);
      expect(result.errors).toHaveLength(0);
    });

    it('passes with range parameters', () => {
      const log = createTransparencyLog();
      for (let i = 0; i < 5; i++) log.append(makeEntry());

      const result = log.verifyIntegrity(1, 4);
      expect(result.valid).toBe(true);
      expect(result.entriesChecked).toBe(3);
    });
  });

  describe('inclusion proofs', () => {
    it('returns null for out-of-range index', () => {
      const log = createTransparencyLog();
      expect(log.getInclusionProof(0)).toBeNull();
    });

    it('generates and verifies inclusion proof', () => {
      const log = createTransparencyLog();
      log.append(makeEntry());
      log.append(makeEntry());
      log.append(makeEntry());

      const proof = log.getInclusionProof(1);
      expect(proof).not.toBeNull();
      expect(proof!.entryIndex).toBe(1);
      expect(proof!.rootHash).toBe(log.getRootHash());

      const verification = log.verifyInclusionProof(proof!);
      expect(verification.verified).toBe(true);
    });

    it('rejects tampered proof', () => {
      const log = createTransparencyLog();
      log.append(makeEntry());
      log.append(makeEntry());

      const proof = log.getInclusionProof(0)!;
      proof.entryHash = 'f'.repeat(64); // tamper

      const verification = log.verifyInclusionProof(proof);
      expect(verification.verified).toBe(false);
      expect(verification.error).toBeDefined();
    });
  });

  describe('tamper detection via root hash', () => {
    it('root hash changes when new entries are appended', () => {
      const log = createTransparencyLog();
      log.append(makeEntry());
      const root1 = log.getRootHash();

      log.append(makeEntry());
      const root2 = log.getRootHash();

      expect(root1).not.toBe(root2);
    });

    it('root hash is all-zeros for empty log', () => {
      const log = createTransparencyLog();
      expect(log.getRootHash()).toBe('0'.repeat(64));
    });
  });
});
