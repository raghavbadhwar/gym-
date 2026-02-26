import crypto from 'crypto';
import type {
    LogEntry,
    TransparencyLog,
    MerkleProof,
    InclusionProofResult,
    LogIntegrityResult,
    IntegrityError,
} from './types.js';
import {
    computeLeafHash,
    computeMerkleRoot,
    generateInclusionProof,
    verifyInclusionProof as verifyMerkleProof,
} from './merkle.js';

const GENESIS_HASH = '0'.repeat(64);

/**
 * RFC 8785–style JSON canonicalization (simplified):
 * recursively sort object keys, pass arrays/primitives through unchanged.
 */
function canonicalize(value: unknown): string {
    if (value === null || value === undefined) return JSON.stringify(value);
    if (typeof value === 'boolean' || typeof value === 'number' || typeof value === 'string') {
        return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
        return '[' + value.map((v) => canonicalize(v)).join(',') + ']';
    }
    if (typeof value === 'object') {
        const keys = Object.keys(value as Record<string, unknown>).sort();
        const parts = keys.map(
            (k) => JSON.stringify(k) + ':' + canonicalize((value as Record<string, unknown>)[k]),
        );
        return '{' + parts.join(',') + '}';
    }
    return JSON.stringify(value);
}

/** Compute the SHA-256 hash of a log entry (excluding entryHash). */
function computeEntryHash(entry: Omit<LogEntry, 'entryHash'>): string {
    const data = canonicalize({
        index: entry.index,
        timestamp: entry.timestamp,
        entryType: entry.entryType,
        actorId: entry.actorId,
        action: entry.action,
        resourceId: entry.resourceId,
        resourceType: entry.resourceType,
        payload: entry.payload,
        previousHash: entry.previousHash,
    });
    return crypto.createHash('sha256').update(data).digest('hex');
}

/** Create an in-memory transparency log implementing the TransparencyLog interface. */
export function createTransparencyLog(): TransparencyLog {
    const entries: LogEntry[] = [];

    function append(
        partial: Omit<LogEntry, 'index' | 'entryHash' | 'previousHash'>,
    ): LogEntry {
        const index = entries.length;
        const previousHash = index === 0 ? GENESIS_HASH : entries[index - 1].entryHash;

        const withoutHash: Omit<LogEntry, 'entryHash'> = {
            ...partial,
            index,
            previousHash,
        };

        const entryHash = computeEntryHash(withoutHash);
        const entry: LogEntry = { ...withoutHash, entryHash };
        entries.push(entry);
        return entry;
    }

    function getEntry(index: number): LogEntry | null {
        return entries[index] ?? null;
    }

    function getEntries(from = 0, to?: number): LogEntry[] {
        return entries.slice(from, to);
    }

    function getLatest(): LogEntry | null {
        return entries.length === 0 ? null : entries[entries.length - 1];
    }

    function size(): number {
        return entries.length;
    }

    function leafHashes(): string[] {
        return entries.map((e) => computeLeafHash(e.entryHash));
    }

    function getRootHash(): string {
        return computeMerkleRoot(leafHashes());
    }

    function getInclusionProof(index: number): MerkleProof | null {
        if (index < 0 || index >= entries.length) return null;
        const leaves = leafHashes();
        const proof = generateInclusionProof(leaves, index);
        return {
            entryIndex: index,
            entryHash: entries[index].entryHash,
            proof,
            rootHash: computeMerkleRoot(leaves),
        };
    }

    function verifyInclusionProof(proof: MerkleProof): InclusionProofResult {
        const leafHash = computeLeafHash(proof.entryHash);
        const verified = verifyMerkleProof(leafHash, proof.proof, proof.rootHash);
        return {
            verified,
            entryIndex: proof.entryIndex,
            rootHash: proof.rootHash,
            ...(!verified ? { error: 'Inclusion proof verification failed' } : {}),
        };
    }

    function verifyIntegrity(from = 0, to?: number): LogIntegrityResult {
        const end = to ?? entries.length;
        const errors: IntegrityError[] = [];
        let entriesChecked = 0;

        for (let i = from; i < end; i++) {
            const entry = entries[i];
            entriesChecked++;

            // Check hash chain continuity
            const expectedPrev = i === 0 ? GENESIS_HASH : entries[i - 1].entryHash;
            if (entry.previousHash !== expectedPrev) {
                errors.push({
                    index: i,
                    expectedHash: expectedPrev,
                    actualHash: entry.previousHash,
                    type: 'chain_break',
                });
            }

            // Check hash correctness
            const recomputed = computeEntryHash({
                index: entry.index,
                timestamp: entry.timestamp,
                entryType: entry.entryType,
                actorId: entry.actorId,
                action: entry.action,
                resourceId: entry.resourceId,
                resourceType: entry.resourceType,
                payload: entry.payload,
                previousHash: entry.previousHash,
            });
            if (entry.entryHash !== recomputed) {
                errors.push({
                    index: i,
                    expectedHash: recomputed,
                    actualHash: entry.entryHash,
                    type: 'hash_mismatch',
                });
            }

            // Check timestamp ordering
            if (i > from) {
                const prev = entries[i - 1];
                if (entry.timestamp < prev.timestamp) {
                    errors.push({
                        index: i,
                        expectedHash: prev.timestamp,
                        actualHash: entry.timestamp,
                        type: 'timestamp_reorder',
                    });
                }
            }
        }

        return { valid: errors.length === 0, entriesChecked, errors };
    }

    return {
        append,
        getEntry,
        getEntries,
        getLatest,
        size,
        getRootHash,
        getInclusionProof,
        verifyInclusionProof,
        verifyIntegrity,
    };
}
