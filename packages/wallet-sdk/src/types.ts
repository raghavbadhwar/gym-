/**
 * @credverse/wallet-sdk — Wallet type definitions
 */

import type {
  VerifiableCredential,
  VerifiablePresentation,
  VCFormat,
  SdJwtVc,
  SigningAlgorithm,
} from '@credverse/trust-core';

/** A credential stored in the wallet */
export interface WalletCredentialRecord {
  id: string;
  credential: VerifiableCredential;
  format: VCFormat;
  issuedAt: string;
  issuerDid: string;
  tags: string[];
  metadata: Record<string, unknown>;
}

/** Filter criteria for querying credentials (AND logic) */
export interface CredentialFilter {
  issuer?: string;
  type?: string;
  tag?: string;
  issuedAfter?: string;
  issuedBefore?: string;
}

/** Credential store interface */
export interface WalletStore {
  save(record: WalletCredentialRecord): void;
  getById(id: string): WalletCredentialRecord | null;
  getAll(): WalletCredentialRecord[];
  query(filter: CredentialFilter): WalletCredentialRecord[];
  remove(id: string): boolean;
}

/** Incoming presentation request from a verifier */
export interface PresentationRequest {
  id: string;
  verifierDid: string;
  presentationDefinition: any;
  nonce: string;
  callbackUrl?: string;
}

/** Result of creating a presentation */
export interface PresentationResult {
  presentation: VerifiablePresentation | null;
  sdJwtVc?: SdJwtVc;
  format: VCFormat;
  selectedCredentials: string[];
}

/** A key stored in the wallet key manager */
export interface KeyRecord {
  id: string;
  did: string;
  algorithm: SigningAlgorithm;
  createdAt: string;
  tags: string[];
}

/** Wallet configuration */
export interface WalletConfig {
  storageBackend: 'memory' | 'encrypted-file';
  encryptionKey?: string;
}
