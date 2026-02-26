/**
 * @credverse/issuer-sdk — Credential status management
 *
 * Implements StatusList2021-style credential status tracking for
 * revocation and suspension using a compact bitstring representation.
 */

import crypto from 'node:crypto';
import type { StatusList, StatusListEntry } from './types.js';

/**
 * Create a new status list for tracking credential revocation or suspension.
 */
export function createStatusList(params: {
  id?: string;
  issuer: string;
  purpose?: 'revocation' | 'suspension';
}): StatusList {
  const list: StatusList = {
    id: params.id ?? `urn:uuid:${crypto.randomUUID()}`,
    issuer: params.issuer,
    purpose: params.purpose ?? 'revocation',
    entries: [],
    encodedList: '',
  };
  return { ...list, encodedList: encodeStatusList(list) };
}

/**
 * Add a new credential to the status list as active.
 */
export function addStatusEntry(list: StatusList, credentialId: string): StatusList {
  const entry: StatusListEntry = {
    credentialId,
    index: list.entries.length,
    status: 'active',
    updatedAt: new Date().toISOString(),
  };

  const updated: StatusList = {
    ...list,
    entries: [...list.entries, entry],
  };
  return { ...updated, encodedList: encodeStatusList(updated) };
}

/**
 * Mark a credential as revoked in the status list.
 */
export function revokeCredential(list: StatusList, credentialId: string): StatusList {
  return updateEntryStatus(list, credentialId, 'revoked');
}

/**
 * Mark a credential as suspended in the status list.
 */
export function suspendCredential(list: StatusList, credentialId: string): StatusList {
  return updateEntryStatus(list, credentialId, 'suspended');
}

/**
 * Look up the status of a credential in the list.
 */
export function getCredentialStatus(
  list: StatusList,
  credentialId: string,
): StatusListEntry | null {
  return list.entries.find((e) => e.credentialId === credentialId) ?? null;
}

/**
 * Encode the status list as a base64url bitstring.
 * Each bit represents a credential: 0 = active, 1 = revoked/suspended.
 */
export function encodeStatusList(list: StatusList): string {
  if (list.entries.length === 0) {
    return Buffer.from([0]).toString('base64url');
  }

  const byteLength = Math.ceil(list.entries.length / 8);
  const bits = new Uint8Array(byteLength);

  for (const entry of list.entries) {
    if (entry.status === 'revoked' || entry.status === 'suspended') {
      const byteIndex = Math.floor(entry.index / 8);
      const bitIndex = 7 - (entry.index % 8);
      bits[byteIndex] |= 1 << bitIndex;
    }
  }

  return Buffer.from(bits).toString('base64url');
}

// ── Internal helpers ────────────────────────────────────────────────────────

function updateEntryStatus(
  list: StatusList,
  credentialId: string,
  status: 'revoked' | 'suspended',
): StatusList {
  const entries = list.entries.map((entry) =>
    entry.credentialId === credentialId
      ? { ...entry, status, updatedAt: new Date().toISOString() }
      : entry,
  );

  const updated: StatusList = { ...list, entries };
  return { ...updated, encodedList: encodeStatusList(updated) };
}
