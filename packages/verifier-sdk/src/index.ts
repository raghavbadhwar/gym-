/**
 * @credverse/verifier-sdk
 * OpenID4VP verification flows, OPA-style policy engine, and signed verification receipts
 */

// Types
export type {
  PresentationDefinition,
  InputDescriptor,
  FieldConstraint,
  PresentationSubmission,
  DescriptorMapEntry,
  AuthorizationRequest,
  AuthorizationResponse,
  VerificationReceipt,
  VerificationDecision,
  PolicyRule,
  PolicyCondition,
  PolicyOperator,
  PolicyEvaluationResult,
} from './types.js';

// OpenID4VP flows
export {
  createAuthorizationRequest,
  validateAuthorizationResponse,
  createPresentationDefinition,
} from './oid4vp.js';

// Policy engine
export {
  evaluatePolicy,
  evaluatePolicies,
  createPolicyRule,
  resolveFieldValue,
  ageCheckPolicy,
  kycCredentialPolicy,
  employerCredentialPolicy,
} from './policy-engine.js';

// Verification receipts
export {
  createVerificationReceipt,
  serializeReceipt,
  validateReceipt,
} from './verification-receipt.js';
