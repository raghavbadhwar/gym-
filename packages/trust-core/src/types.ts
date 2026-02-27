/**
 * @credverse/trust-core — Core type definitions
 * W3C VC Data Model v2, DID Core, SD-JWT VC, key management types
 */

// ── DID Core ────────────────────────────────────────────────────────────────

/** W3C DID Core verification method */
export interface VerificationMethod {
  id: string;
  type: string;
  controller: string;
  publicKeyJwk?: Record<string, unknown>;
  publicKeyMultibase?: string;
}

/** DID service endpoint */
export interface ServiceEndpoint {
  id: string;
  type: string;
  serviceEndpoint: string;
}

/** W3C DID Core document */
export interface DIDDocument {
  id: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  assertionMethod: string[];
  service: ServiceEndpoint[];
}

// ── W3C VC Data Model v2 ────────────────────────────────────────────────────

/** Linked-data proof */
export interface Proof {
  type: string;
  created: string;
  verificationMethod: string;
  proofPurpose: string;
  proofValue: string;
}

/** Credential status (e.g. StatusList2021Entry) */
export interface CredentialStatus {
  id: string;
  type: string;
  statusPurpose: string;
  statusListIndex: string;
  statusListCredential: string;
}

/** W3C Verifiable Credential Data Model v2 */
export interface VerifiableCredential {
  '@context': string[];
  id: string;
  type: string[];
  issuer: string;
  validFrom: string;
  validUntil?: string;
  credentialSubject: Record<string, unknown>;
  credentialStatus?: CredentialStatus;
  proof?: Proof;
}

/** W3C Verifiable Presentation */
export interface VerifiablePresentation {
  '@context': string[];
  id: string;
  type: string[];
  holder: string;
  verifiableCredential: VerifiableCredential[];
  proof?: Proof;
}

// ── VC Formats ──────────────────────────────────────────────────────────────

/** Supported VC serialization formats */
export type VCFormat = 'jwt-vc' | 'ldp-vc' | 'sd-jwt-vc';

// ── SD-JWT VC ───────────────────────────────────────────────────────────────

/** A single SD-JWT disclosure triple */
export interface SdJwtDisclosure {
  salt: string;
  claimName: string;
  claimValue: unknown;
}

/** SD-JWT VC envelope */
export interface SdJwtVc {
  jwt: string;
  disclosures: SdJwtDisclosure[];
  keyBindingJwt?: string;
}

// ── Key Management ──────────────────────────────────────────────────────────

/** Supported signing algorithms */
export type SigningAlgorithm = 'ES256' | 'ES384' | 'EdDSA' | 'RS256';

/** Asymmetric key pair */
export interface KeyPair {
  id: string;
  type: string;
  publicKey: string;
  privateKey: string;
  algorithm: SigningAlgorithm;
}
