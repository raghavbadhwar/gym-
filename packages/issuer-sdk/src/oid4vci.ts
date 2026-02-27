/**
 * @credverse/issuer-sdk — OpenID4VCI flow implementation
 *
 * Implements the OpenID for Verifiable Credential Issuance protocol flows
 * including issuer metadata, credential offers, token handling, and
 * credential request/response processing.
 */

import crypto from 'node:crypto';
import type { VCFormat } from '@credverse/trust-core';
import type {
  IssuerMetadata,
  CredentialConfiguration,
  CredentialOffer,
  TokenResponse,
  CredentialRequest,
  CredentialResponse,
} from './types.js';

/**
 * Create OpenID4VCI issuer metadata describing the issuer's capabilities.
 */
export function createIssuerMetadata(params: {
  issuerUrl: string;
  credentialEndpoint?: string;
  tokenEndpoint?: string;
  configurations: Record<string, CredentialConfiguration>;
}): IssuerMetadata {
  const { issuerUrl, configurations } = params;
  const credentialEndpoint = params.credentialEndpoint ?? `${issuerUrl}/credentials`;
  const tokenEndpoint = params.tokenEndpoint ?? `${issuerUrl}/token`;

  return {
    credentialIssuer: issuerUrl,
    credentialEndpoint,
    tokenEndpoint,
    credentialConfigurationsSupported: configurations,
  };
}

/**
 * Create a credential offer that initiates the pre-authorized code issuance flow.
 */
export function createCredentialOffer(params: {
  issuerUrl: string;
  configurationIds: string[];
  preAuthorizedCode: string;
  userPinRequired?: boolean;
}): CredentialOffer {
  return {
    credentialIssuer: params.issuerUrl,
    credentialConfigurationIds: params.configurationIds,
    grants: {
      preAuthorizedCode: {
        code: params.preAuthorizedCode,
        userPinRequired: params.userPinRequired ?? false,
      },
    },
  };
}

/**
 * Create a token response with a generated access token and c_nonce.
 */
export function createTokenResponse(params: {
  accessToken?: string;
  expiresIn?: number;
}): TokenResponse {
  const accessToken = params.accessToken ?? crypto.randomBytes(32).toString('hex');
  const cNonce = crypto.randomBytes(16).toString('hex');

  return {
    accessToken,
    tokenType: 'Bearer',
    expiresIn: params.expiresIn ?? 86400,
    cNonce,
    cNonceExpiresIn: 300,
  };
}

/**
 * Validate a credential request against the issuer's supported formats.
 */
export function validateCredentialRequest(
  request: CredentialRequest,
  supportedFormats: VCFormat[],
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!supportedFormats.includes(request.format)) {
    errors.push(`Unsupported format: ${request.format}`);
  }

  if (!request.types || request.types.length === 0) {
    errors.push('Credential types must not be empty');
  }

  if (request.proof && !request.proof.jwt) {
    errors.push('Proof JWT must be provided when proof is present');
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Create a credential response wrapping the issued credential.
 */
export function createCredentialResponse(params: {
  format: VCFormat;
  credential: string;
}): CredentialResponse {
  const cNonce = crypto.randomBytes(16).toString('hex');

  return {
    format: params.format,
    credential: params.credential,
    cNonce,
    cNonceExpiresIn: 300,
  };
}
