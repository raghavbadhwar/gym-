/**
 * @credverse/trust-core
 * Core module: W3C VC Data Model v2, DID Core, SD-JWT VC, key management, crypto utilities
 */

// Types
export type {
  DIDDocument,
  VerificationMethod,
  ServiceEndpoint,
  VerifiableCredential,
  VerifiablePresentation,
  Proof,
  CredentialStatus,
  VCFormat,
  SdJwtVc,
  SdJwtDisclosure,
  KeyPair,
  SigningAlgorithm,
} from './types.js';

// DID utilities
export {
  createDidKey,
  createDidWeb,
  resolveDidDocument,
  extractVerificationMethod,
} from './did.js';

// Verifiable Credential utilities
export {
  createVerifiableCredential,
  validateCredentialStructure,
  createVerifiablePresentation,
} from './vc.js';

// SD-JWT VC utilities
export {
  createDisclosure,
  encodeDisclosure,
  decodeDisclosure,
  selectDisclosures,
  createSdJwtVc,
  parseSdJwtVc,
  serializeSdJwtVc,
} from './sd-jwt.js';

// Cryptographic utilities
export {
  generateSalt,
  sha256,
  canonicalize,
  generateKeyPair,
  base64urlEncode,
  base64urlDecode,
} from './crypto.js';
