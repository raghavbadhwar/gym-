/**
 * @credverse/trust-core — Verifiable Credential creation and validation
 */

import crypto from 'node:crypto';
import type {
  CredentialStatus,
  VerifiableCredential,
  VerifiablePresentation,
} from './types.js';

const VC_CONTEXT_V2 = 'https://www.w3.org/ns/credentials/v2';
const VC_TYPE = 'VerifiableCredential';
const VP_TYPE = 'VerifiablePresentation';

/**
 * Create an unsigned Verifiable Credential conforming to W3C VC Data Model v2.
 */
export function createVerifiableCredential(params: {
  issuer: string;
  subject: Record<string, unknown>;
  types?: string[];
  credentialStatus?: CredentialStatus;
  validFrom?: string;
  validUntil?: string;
}): VerifiableCredential {
  const types = [VC_TYPE, ...(params.types ?? [])];

  const vc: VerifiableCredential = {
    '@context': [VC_CONTEXT_V2],
    id: `urn:uuid:${crypto.randomUUID()}`,
    type: types,
    issuer: params.issuer,
    validFrom: params.validFrom ?? new Date().toISOString(),
    credentialSubject: params.subject,
  };

  if (params.validUntil) {
    vc.validUntil = params.validUntil;
  }

  if (params.credentialStatus) {
    vc.credentialStatus = params.credentialStatus;
  }

  return vc;
}

/**
 * Validate a Verifiable Credential's structure against W3C VC Data Model v2.
 * Returns a list of structural errors (does NOT verify proofs).
 */
export function validateCredentialStructure(
  vc: VerifiableCredential,
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!vc['@context'] || !Array.isArray(vc['@context'])) {
    errors.push('@context must be a non-empty array');
  } else if (!vc['@context'].includes(VC_CONTEXT_V2)) {
    errors.push(`@context must include ${VC_CONTEXT_V2}`);
  }

  if (!vc.id || typeof vc.id !== 'string' || vc.id.trim() === '') {
    errors.push('id must be a non-empty string');
  }

  if (!Array.isArray(vc.type) || !vc.type.includes(VC_TYPE)) {
    errors.push(`type must be an array containing "${VC_TYPE}"`);
  }

  if (!vc.issuer || typeof vc.issuer !== 'string' || vc.issuer.trim() === '') {
    errors.push('issuer must be a non-empty string');
  }

  if (!vc.validFrom || typeof vc.validFrom !== 'string' || vc.validFrom.trim() === '') {
    errors.push('validFrom must be a non-empty string');
  }

  if (
    !vc.credentialSubject ||
    typeof vc.credentialSubject !== 'object' ||
    Array.isArray(vc.credentialSubject)
  ) {
    errors.push('credentialSubject must be a non-null object');
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Create an unsigned Verifiable Presentation.
 */
export function createVerifiablePresentation(params: {
  holder: string;
  credentials: VerifiableCredential[];
}): VerifiablePresentation {
  return {
    '@context': [VC_CONTEXT_V2],
    id: `urn:uuid:${crypto.randomUUID()}`,
    type: [VP_TYPE],
    holder: params.holder,
    verifiableCredential: params.credentials,
  };
}
