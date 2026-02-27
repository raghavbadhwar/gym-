/**
 * @credverse/verifier-sdk — Verification receipts
 * Creates, serializes, and validates signed verification receipts.
 */

import type { VerificationDecision, VerificationReceipt } from './types.js';

const VALID_DECISIONS: VerificationDecision[] = ['approved', 'denied', 'review_required'];

/** Creates a verification receipt with a timestamp and UUID. */
export function createVerificationReceipt(params: {
  verifierId: string;
  subjectDid: string;
  policiesApplied: string[];
  decision: VerificationDecision;
  evidenceHashes?: string[];
}): VerificationReceipt {
  return {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    verifierId: params.verifierId,
    subjectDid: params.subjectDid,
    policiesApplied: params.policiesApplied,
    decision: params.decision,
    evidenceHashes: params.evidenceHashes ?? [],
  };
}

/** Serializes a receipt to canonical JSON (sorted keys). */
export function serializeReceipt(receipt: VerificationReceipt): string {
  return JSON.stringify(receipt, Object.keys(receipt).sort());
}

/** Validates a verification receipt structure. */
export function validateReceipt(
  receipt: VerificationReceipt,
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!receipt.id) {
    errors.push('Missing id');
  }
  if (!receipt.timestamp) {
    errors.push('Missing timestamp');
  }
  if (receipt.timestamp && isNaN(Date.parse(receipt.timestamp))) {
    errors.push('Invalid timestamp format');
  }
  if (!receipt.verifierId) {
    errors.push('Missing verifierId');
  }
  if (!receipt.subjectDid) {
    errors.push('Missing subjectDid');
  }
  if (!Array.isArray(receipt.policiesApplied)) {
    errors.push('policiesApplied must be an array');
  }
  if (!VALID_DECISIONS.includes(receipt.decision)) {
    errors.push(`Invalid decision: must be one of ${VALID_DECISIONS.join(', ')}`);
  }
  if (!Array.isArray(receipt.evidenceHashes)) {
    errors.push('evidenceHashes must be an array');
  }

  return { valid: errors.length === 0, errors };
}
