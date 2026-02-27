/**
 * @credverse/verifier-sdk — OpenID4VP flow implementation
 * Creates authorization requests, validates responses, and builds presentation definitions.
 */

import type {
  AuthorizationRequest,
  AuthorizationResponse,
  FieldConstraint,
  InputDescriptor,
  PresentationDefinition,
} from './types.js';

/** Creates an OpenID4VP authorization request with a generated nonce. */
export function createAuthorizationRequest(params: {
  clientId: string;
  redirectUri: string;
  presentationDefinition: PresentationDefinition;
  state?: string;
}): AuthorizationRequest {
  return {
    responseType: 'vp_token',
    clientId: params.clientId,
    redirectUri: params.redirectUri,
    nonce: crypto.randomUUID(),
    state: params.state ?? crypto.randomUUID(),
    presentationDefinition: params.presentationDefinition,
  };
}

/** Validates an OpenID4VP authorization response structure. */
export function validateAuthorizationResponse(
  response: AuthorizationResponse,
  expectedState: string,
  expectedNonce: string,
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!response.vpToken) {
    errors.push('Missing vpToken');
  }
  if (!response.presentationSubmission) {
    errors.push('Missing presentationSubmission');
  }
  if (!response.state) {
    errors.push('Missing state');
  }
  if (response.state !== expectedState) {
    errors.push(`State mismatch: expected "${expectedState}", got "${response.state}"`);
  }
  if (!expectedNonce) {
    errors.push('Expected nonce must be provided');
  }
  if (response.presentationSubmission) {
    if (!response.presentationSubmission.id) {
      errors.push('Missing presentationSubmission.id');
    }
    if (!response.presentationSubmission.definitionId) {
      errors.push('Missing presentationSubmission.definitionId');
    }
    if (
      !response.presentationSubmission.descriptorMap ||
      response.presentationSubmission.descriptorMap.length === 0
    ) {
      errors.push('presentationSubmission.descriptorMap must have at least one entry');
    }
  }

  return { valid: errors.length === 0, errors };
}

/** Helper to build an OpenID4VP presentation definition. */
export function createPresentationDefinition(params: {
  id?: string;
  descriptors: Array<{
    id: string;
    name?: string;
    purpose?: string;
    fields: Array<{ path: string[]; filter?: FieldConstraint['filter'] }>;
  }>;
}): PresentationDefinition {
  const inputDescriptors: InputDescriptor[] = params.descriptors.map((d) => ({
    id: d.id,
    ...(d.name !== undefined && { name: d.name }),
    ...(d.purpose !== undefined && { purpose: d.purpose }),
    constraints: {
      fields: d.fields.map((f) => ({
        path: f.path,
        ...(f.filter !== undefined && { filter: f.filter }),
      })),
    },
  }));

  return {
    id: params.id ?? crypto.randomUUID(),
    inputDescriptors,
  };
}
