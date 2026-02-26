/**
 * @credverse/wallet-sdk — In-memory credential store implementation
 */

import type { WalletStore, WalletCredentialRecord, CredentialFilter } from './types.js';

/**
 * Create an in-memory credential store.
 */
export function createInMemoryStore(): WalletStore {
  const records = new Map<string, WalletCredentialRecord>();

  return {
    save(record: WalletCredentialRecord): void {
      records.set(record.id, record);
    },

    getById(id: string): WalletCredentialRecord | null {
      return records.get(id) ?? null;
    },

    getAll(): WalletCredentialRecord[] {
      return [...records.values()];
    },

    query(filter: CredentialFilter): WalletCredentialRecord[] {
      return [...records.values()].filter((record) => {
        if (filter.issuer && record.issuerDid !== filter.issuer) return false;
        if (filter.type && !record.credential.type.includes(filter.type)) return false;
        if (filter.tag && !record.tags.includes(filter.tag)) return false;
        if (filter.issuedAfter && record.issuedAt < filter.issuedAfter) return false;
        if (filter.issuedBefore && record.issuedAt >= filter.issuedBefore) return false;
        return true;
      });
    },

    remove(id: string): boolean {
      return records.delete(id);
    },
  };
}
