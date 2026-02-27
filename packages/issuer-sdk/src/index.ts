/**
 * @credverse/issuer-sdk
 * OpenID4VCI issuance flows, credential templates, and status management
 */

// Types
export type {
  IssuerMetadata,
  CredentialConfiguration,
  TokenRequest,
  TokenResponse,
  CredentialRequest,
  CredentialResponse,
  CredentialOffer,
  CredentialTemplate,
  TemplateField,
  StatusListEntry,
  StatusList,
} from './types.js';

// OpenID4VCI flows
export {
  createIssuerMetadata,
  createCredentialOffer,
  createTokenResponse,
  validateCredentialRequest,
  createCredentialResponse,
} from './oid4vci.js';

// Credential templates
export {
  createTemplate,
  validateSubjectAgainstTemplate,
  universityDegreeTemplate,
  employmentCredentialTemplate,
  ageVerificationTemplate,
} from './templates.js';

// Status list management
export {
  createStatusList,
  addStatusEntry,
  revokeCredential,
  suspendCredential,
  getCredentialStatus,
  encodeStatusList,
} from './status-list.js';
