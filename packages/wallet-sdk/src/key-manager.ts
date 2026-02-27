/**
 * @credverse/wallet-sdk — Wallet key management
 */

import type { SigningAlgorithm } from '@credverse/trust-core';
import { generateKeyPair, createDidKey } from '@credverse/trust-core';
import type { KeyRecord } from './types.js';

export interface KeyManager {
  generateKey(algorithm: SigningAlgorithm): Promise<KeyRecord>;
  getKey(id: string): KeyRecord | null;
  listKeys(): KeyRecord[];
  rotateKey(oldKeyId: string, algorithm: SigningAlgorithm): Promise<{ newKey: KeyRecord; oldKey: KeyRecord }>;
  removeKey(id: string): boolean;
}

/**
 * Create an in-memory key manager backed by @credverse/trust-core key generation.
 */
export function createKeyManager(): KeyManager {
  const keys = new Map<string, KeyRecord>();

  async function generateKey(algorithm: SigningAlgorithm): Promise<KeyRecord> {
    const keyPair = await generateKeyPair(algorithm);
    const publicKeyBytes = new TextEncoder().encode(keyPair.publicKey);
    const did = createDidKey(publicKeyBytes);

    const record: KeyRecord = {
      id: keyPair.id,
      did,
      algorithm,
      createdAt: new Date().toISOString(),
      tags: [],
    };

    keys.set(record.id, record);
    return record;
  }

  return {
    generateKey,

    getKey(id: string): KeyRecord | null {
      return keys.get(id) ?? null;
    },

    listKeys(): KeyRecord[] {
      return [...keys.values()];
    },

    async rotateKey(oldKeyId: string, algorithm: SigningAlgorithm) {
      const oldKey = keys.get(oldKeyId);
      if (!oldKey) {
        throw new Error(`Key not found: ${oldKeyId}`);
      }
      const newKey = await generateKey(algorithm);
      return { newKey, oldKey };
    },

    removeKey(id: string): boolean {
      return keys.delete(id);
    },
  };
}
