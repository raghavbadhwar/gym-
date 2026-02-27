/**
 * @credverse/trust-core — DID resolution and creation utilities
 */

import crypto from 'node:crypto';
import type { DIDDocument, VerificationMethod } from './types.js';

// Simplified base58btc alphabet (Bitcoin alphabet)
const BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

/** Multicodec prefix for Ed25519 public key (0xed 0x01) */
const ED25519_MULTICODEC_PREFIX = new Uint8Array([0xed, 0x01]);

/** Encode bytes to base58btc */
function base58btcEncode(bytes: Uint8Array): string {
  let num = BigInt(0);
  for (const byte of bytes) {
    num = num * 256n + BigInt(byte);
  }

  let encoded = '';
  while (num > 0n) {
    const remainder = Number(num % 58n);
    num = num / 58n;
    encoded = BASE58_ALPHABET[remainder] + encoded;
  }

  // Preserve leading zeros
  for (const byte of bytes) {
    if (byte === 0) {
      encoded = '1' + encoded;
    } else {
      break;
    }
  }

  return encoded;
}

/**
 * Create a did:key identifier from raw public key bytes.
 * Encodes the key as multibase base58btc with the 'z' prefix.
 */
export function createDidKey(publicKeyBytes: Uint8Array): string {
  const multicodec = new Uint8Array([...ED25519_MULTICODEC_PREFIX, ...publicKeyBytes]);
  const multibase = 'z' + base58btcEncode(multicodec);
  return `did:key:${multibase}`;
}

/**
 * Create a did:web identifier from a domain and optional path.
 * @example createDidWeb('example.com')           → 'did:web:example.com'
 * @example createDidWeb('example.com', 'issuer') → 'did:web:example.com:issuer'
 */
export function createDidWeb(domain: string, path?: string): string {
  const encoded = domain.replace(/:/g, '%3A');
  return path ? `did:web:${encoded}:${path}` : `did:web:${encoded}`;
}

/**
 * Basic DID resolution — builds a minimal DID Document for did:key and did:web methods.
 * For production use, replace with a full DID resolver.
 */
export function resolveDidDocument(did: string): DIDDocument {
  if (!did.startsWith('did:')) {
    throw new Error(`Invalid DID: ${did}`);
  }

  const vmId = `${did}#key-1`;

  if (did.startsWith('did:key:')) {
    const multibase = did.slice('did:key:'.length);
    return {
      id: did,
      verificationMethod: [
        {
          id: vmId,
          type: 'Ed25519VerificationKey2020',
          controller: did,
          publicKeyMultibase: multibase,
        },
      ],
      authentication: [vmId],
      assertionMethod: [vmId],
      service: [],
    };
  }

  if (did.startsWith('did:web:')) {
    return {
      id: did,
      verificationMethod: [
        {
          id: vmId,
          type: 'JsonWebKey2020',
          controller: did,
        },
      ],
      authentication: [vmId],
      assertionMethod: [vmId],
      service: [],
    };
  }

  // Fallback: return a minimal document for unknown methods
  return {
    id: did,
    verificationMethod: [],
    authentication: [],
    assertionMethod: [],
    service: [],
  };
}

/**
 * Extract the first verification method referenced by the given purpose
 * (e.g. 'authentication', 'assertionMethod').
 */
export function extractVerificationMethod(
  doc: DIDDocument,
  purpose: string,
): VerificationMethod | null {
  const refs = (doc as Record<string, unknown>)[purpose];
  if (!Array.isArray(refs) || refs.length === 0) return null;

  const ref = refs[0] as string;
  return doc.verificationMethod.find((vm) => vm.id === ref) ?? null;
}
