// Types
export type {
    LogEntryType,
    LogEntry,
    MerkleNode,
    ProofStep,
    MerkleProof,
    InclusionProofResult,
    IntegrityError,
    LogIntegrityResult,
    TransparencyLog,
} from './types.js';

// Merkle tree utilities
export {
    computeLeafHash,
    computeNodeHash,
    buildMerkleTree,
    computeMerkleRoot,
    generateInclusionProof,
    verifyInclusionProof,
} from './merkle.js';

// Transparency log factory
export { createTransparencyLog } from './log.js';
