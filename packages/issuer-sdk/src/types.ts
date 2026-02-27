/**
 * @credverse/issuer-sdk — Type definitions
 * OpenID4VCI issuance flows, credential templates, and status management
 */

import type { VCFormat } from '@credverse/trust-core';

// ── OpenID4VCI Issuance ─────────────────────────────────────────────────────

/** Credential configuration describing a supported credential type */
export interface CredentialConfiguration {
  format: VCFormat;
  types: string[];
  cryptographicBindingMethodsSupported: string[];
  credentialSigningAlgValuesSupported: string[];
}

/** OpenID4VCI issuer metadata */
export interface IssuerMetadata {
  credentialIssuer: string;
  credentialEndpoint: string;
  tokenEndpoint: string;
  credentialConfigurationsSupported: Record<string, CredentialConfiguration>;
}

/** Token request using pre-authorized code grant */
export interface TokenRequest {
  grantType: 'urn:ietf:params:oauth:grant-type:pre-authorized_code';
  preAuthorizedCode: string;
  userPin?: string;
}

/** Token response from the issuer */
export interface TokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  cNonce: string;
  cNonceExpiresIn: number;
}

/** Credential issuance request */
export interface CredentialRequest {
  format: VCFormat;
  types: string[];
  proof?: { proofType: string; jwt: string };
}

/** Credential issuance response */
export interface CredentialResponse {
  format: VCFormat;
  credential: string;
  cNonce?: string;
  cNonceExpiresIn?: number;
}

/** Credential offer initiating the issuance flow */
export interface CredentialOffer {
  credentialIssuer: string;
  credentialConfigurationIds: string[];
  grants: {
    preAuthorizedCode: {
      code: string;
      userPinRequired: boolean;
    };
  };
}

// ── Credential Templates ────────────────────────────────────────────────────

/** Field definition within a credential template */
export interface TemplateField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date';
  required: boolean;
  description?: string;
}

/** Credential template defining the structure of a credential type */
export interface CredentialTemplate {
  id: string;
  name: string;
  description: string;
  types: string[];
  subjectFields: TemplateField[];
  format: VCFormat;
}

// ── Status List ─────────────────────────────────────────────────────────────

/** Entry tracking the status of an individual credential */
export interface StatusListEntry {
  credentialId: string;
  index: number;
  status: 'active' | 'revoked' | 'suspended';
  updatedAt: string;
}

/** Status list for tracking revocation or suspension of credentials */
export interface StatusList {
  id: string;
  issuer: string;
  purpose: 'revocation' | 'suspension';
  entries: StatusListEntry[];
  encodedList: string;
}
