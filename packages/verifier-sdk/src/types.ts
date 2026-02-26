/**
 * @credverse/verifier-sdk — Type definitions
 * OpenID4VP presentation flows, policy engine, and verification receipts
 */

import type { VCFormat } from '@credverse/trust-core';

// ── OpenID4VP Presentation Exchange ─────────────────────────────────────────

/** Field constraint for input descriptors */
export interface FieldConstraint {
  path: string[];
  filter?: { type: string; pattern?: string; const?: unknown };
}

/** Input descriptor within a presentation definition */
export interface InputDescriptor {
  id: string;
  name?: string;
  purpose?: string;
  constraints: { fields: FieldConstraint[] };
}

/** OpenID4VP presentation definition */
export interface PresentationDefinition {
  id: string;
  inputDescriptors: InputDescriptor[];
}

/** Descriptor map entry in a presentation submission */
export interface DescriptorMapEntry {
  id: string;
  format: VCFormat;
  path: string;
}

/** OpenID4VP presentation submission */
export interface PresentationSubmission {
  id: string;
  definitionId: string;
  descriptorMap: DescriptorMapEntry[];
}

/** OpenID4VP authorization request */
export interface AuthorizationRequest {
  responseType: string;
  clientId: string;
  redirectUri: string;
  nonce: string;
  state: string;
  presentationDefinition: PresentationDefinition;
}

/** OpenID4VP authorization response */
export interface AuthorizationResponse {
  vpToken: string;
  presentationSubmission: PresentationSubmission;
  state: string;
}

// ── Verification Receipts ───────────────────────────────────────────────────

/** Verification decision outcome */
export type VerificationDecision = 'approved' | 'denied' | 'review_required';

/** Signed verification receipt */
export interface VerificationReceipt {
  id: string;
  timestamp: string;
  verifierId: string;
  subjectDid: string;
  policiesApplied: string[];
  decision: VerificationDecision;
  evidenceHashes: string[];
  signature?: string;
}

// ── Policy Engine ───────────────────────────────────────────────────────────

/** Supported policy comparison operators */
export type PolicyOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'contains'
  | 'exists'
  | 'in';

/** Condition evaluated by the policy engine */
export interface PolicyCondition {
  field: string;
  operator: PolicyOperator;
  value: unknown;
}

/** A single policy rule */
export interface PolicyRule {
  id: string;
  name: string;
  description: string;
  condition: PolicyCondition;
}

/** Result of evaluating a single policy rule */
export interface PolicyEvaluationResult {
  policyId: string;
  passed: boolean;
  reason?: string;
}
