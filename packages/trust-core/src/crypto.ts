/**
 * @credverse/trust-core — Cryptographic utilities
 *
 * All operations use the Node.js built-in `crypto` module.
 */

import crypto from 'node:crypto';
import type { KeyPair, SigningAlgorithm } from './types.js';

/**
 * Generate a cryptographically random salt encoded as base64url.
 */
export function generateSalt(): string {
  return base64urlEncode(crypto.randomBytes(16));
}

/**
 * Compute the SHA-256 hash of a string, returned as a hex digest.
 */
export function sha256(data: string): string {
  return crypto.createHash('sha256').update(data, 'utf8').digest('hex');
}

/**
 * RFC 8785 JSON Canonicalization Scheme.
 *
 * Produces a deterministic JSON serialization by:
 * - Sorting object keys lexicographically (recursively)
 * - Serializing arrays in order
 * - Using `JSON.stringify` for primitives (numbers follow ES2015 serialization)
 */
export function canonicalize(obj: unknown): string {
  if (obj === null || obj === undefined) return 'null';
  if (typeof obj === 'boolean' || typeof obj === 'number') return JSON.stringify(obj);
  if (typeof obj === 'string') return JSON.stringify(obj);

  if (Array.isArray(obj)) {
    const items = obj.map((item) => canonicalize(item));
    return `[${items.join(',')}]`;
  }

  if (typeof obj === 'object') {
    const keys = Object.keys(obj as Record<string, unknown>).sort();
    const entries = keys.map(
      (key) =>
        `${JSON.stringify(key)}:${canonicalize((obj as Record<string, unknown>)[key])}`,
    );
    return `{${entries.join(',')}}`;
  }

  return JSON.stringify(obj);
}

/** Map signing algorithm names to Node.js crypto curve / key parameters */
const ALGORITHM_CONFIG: Record<
  SigningAlgorithm,
  { keyType: string; namedCurve?: string; modulusLength?: number }
> = {
  ES256: { keyType: 'ec', namedCurve: 'P-256' },
  ES384: { keyType: 'ec', namedCurve: 'P-384' },
  EdDSA: { keyType: 'ed25519' },
  RS256: { keyType: 'rsa', modulusLength: 2048 },
};

/**
 * Generate an asymmetric key pair for the given signing algorithm.
 */
export async function generateKeyPair(algorithm: SigningAlgorithm): Promise<KeyPair> {
  const config = ALGORITHM_CONFIG[algorithm];

  return new Promise<KeyPair>((resolve, reject) => {
    const options: Record<string, unknown> = {
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
    };

    if (config.namedCurve) {
      (options as Record<string, unknown>).namedCurve = config.namedCurve;
    }
    if (config.modulusLength) {
      (options as Record<string, unknown>).modulusLength = config.modulusLength;
      (options as Record<string, unknown>).publicExponent = 65537;
    }

    crypto.generateKeyPair(
      config.keyType as 'ec' | 'ed25519' | 'rsa',
      options as crypto.ECKeyPairOptions<'pem', 'pem'>,
      (err, publicKey, privateKey) => {
        if (err) return reject(err);
        resolve({
          id: `urn:uuid:${crypto.randomUUID()}`,
          type: `${algorithm}VerificationKey`,
          publicKey: publicKey as string,
          privateKey: privateKey as string,
          algorithm,
        });
      },
    );
  });
}

/**
 * Base64url-encode a string or byte array (no padding).
 */
export function base64urlEncode(data: string | Uint8Array): string {
  const buf = typeof data === 'string' ? Buffer.from(data, 'utf8') : Buffer.from(data);
  return buf.toString('base64url');
}

/**
 * Decode a base64url-encoded string back to a UTF-8 string.
 */
export function base64urlDecode(encoded: string): string {
  return Buffer.from(encoded, 'base64url').toString('utf8');
}
