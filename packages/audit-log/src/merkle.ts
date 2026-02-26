import crypto from 'crypto';
import type { MerkleNode, ProofStep } from './types.js';

const LEAF_PREFIX = Buffer.from([0x00]);
const NODE_PREFIX = Buffer.from([0x01]);

/** Compute the hash of a leaf node (0x00 ‖ data). */
export function computeLeafHash(data: string): string {
    return crypto
        .createHash('sha256')
        .update(Buffer.concat([LEAF_PREFIX, Buffer.from(data, 'utf8')]))
        .digest('hex');
}

/** Compute the hash of an internal node (0x01 ‖ left ‖ right). */
export function computeNodeHash(left: string, right: string): string {
    return crypto
        .createHash('sha256')
        .update(Buffer.concat([NODE_PREFIX, Buffer.from(left, 'hex'), Buffer.from(right, 'hex')]))
        .digest('hex');
}

/** Pad leaves to the next power of two by duplicating the last leaf. */
function padLeaves(leaves: string[]): string[] {
    if (leaves.length === 0) return [];
    let padded = [...leaves];
    let size = 1;
    while (size < padded.length) size *= 2;
    while (padded.length < size) {
        padded.push(padded[padded.length - 1]);
    }
    return padded;
}

/** Build a balanced Merkle tree from an array of leaf hashes. */
export function buildMerkleTree(leaves: string[]): MerkleNode | null {
    if (leaves.length === 0) return null;

    const padded = padLeaves(leaves);
    let nodes: MerkleNode[] = padded.map((hash) => ({ hash }));

    while (nodes.length > 1) {
        const next: MerkleNode[] = [];
        for (let i = 0; i < nodes.length; i += 2) {
            const left = nodes[i];
            const right = nodes[i + 1];
            next.push({
                hash: computeNodeHash(left.hash, right.hash),
                left,
                right,
            });
        }
        nodes = next;
    }

    return nodes[0];
}

/** Compute the Merkle root hash for a set of leaf hashes. */
export function computeMerkleRoot(leaves: string[]): string {
    if (leaves.length === 0) return '0'.repeat(64);
    const tree = buildMerkleTree(leaves);
    return tree!.hash;
}

/** Generate an inclusion proof (audit path) for the leaf at `index`. */
export function generateInclusionProof(leaves: string[], index: number): ProofStep[] {
    if (index < 0 || index >= leaves.length || leaves.length === 0) return [];

    const padded = padLeaves(leaves);
    let layerNodes = [...padded];
    const proof: ProofStep[] = [];
    let pos = index;

    while (layerNodes.length > 1) {
        const nextLayer: string[] = [];
        for (let i = 0; i < layerNodes.length; i += 2) {
            const left = layerNodes[i];
            const right = layerNodes[i + 1];
            nextLayer.push(computeNodeHash(left, right));
        }

        const siblingIndex = pos % 2 === 0 ? pos + 1 : pos - 1;
        proof.push({
            hash: layerNodes[siblingIndex],
            position: pos % 2 === 0 ? 'right' : 'left',
        });

        pos = Math.floor(pos / 2);
        layerNodes = nextLayer;
    }

    return proof;
}

/** Verify that a leaf hash is included under `rootHash` given a proof path. */
export function verifyInclusionProof(leafHash: string, proof: ProofStep[], rootHash: string): boolean {
    let current = leafHash;
    for (const step of proof) {
        current =
            step.position === 'right'
                ? computeNodeHash(current, step.hash)
                : computeNodeHash(step.hash, current);
    }
    return current === rootHash;
}
