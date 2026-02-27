/** Supported audit log entry types within the CredVerse ecosystem. */
export type LogEntryType =
    | 'issuance'
    | 'verification'
    | 'revocation'
    | 'presentation'
    | 'policy_evaluation'
    | 'key_rotation'
    | 'system';

/** A single record in the append-only transparency log. */
export interface LogEntry {
    index: number;
    timestamp: string;
    entryType: LogEntryType;
    actorId: string;
    action: string;
    resourceId: string;
    resourceType: string;
    payload: Record<string, unknown>;
    entryHash: string;
    previousHash: string;
}

/** A node in a Merkle tree. */
export interface MerkleNode {
    hash: string;
    left?: MerkleNode;
    right?: MerkleNode;
}

/** A single step in a Merkle inclusion proof path. */
export interface ProofStep {
    hash: string;
    position: 'left' | 'right';
}

/** A Merkle inclusion proof for a specific log entry. */
export interface MerkleProof {
    entryIndex: number;
    entryHash: string;
    proof: ProofStep[];
    rootHash: string;
}

/** Result of verifying an inclusion proof. */
export interface InclusionProofResult {
    verified: boolean;
    entryIndex: number;
    rootHash: string;
    error?: string;
}

/** An error detected during integrity verification. */
export interface IntegrityError {
    index: number;
    expectedHash: string;
    actualHash: string;
    type: 'chain_break' | 'hash_mismatch' | 'timestamp_reorder';
}

/** Result of a log integrity verification scan. */
export interface LogIntegrityResult {
    valid: boolean;
    entriesChecked: number;
    errors: IntegrityError[];
}

/** Interface for an append-only transparency log with Merkle proofs. */
export interface TransparencyLog {
    append(entry: Omit<LogEntry, 'index' | 'entryHash' | 'previousHash'>): LogEntry;
    getEntry(index: number): LogEntry | null;
    getEntries(from?: number, to?: number): LogEntry[];
    getLatest(): LogEntry | null;
    size(): number;
    getRootHash(): string;
    getInclusionProof(index: number): MerkleProof | null;
    verifyInclusionProof(proof: MerkleProof): InclusionProofResult;
    verifyIntegrity(from?: number, to?: number): LogIntegrityResult;
}
