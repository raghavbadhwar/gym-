/**
 * @credverse/wallet-sdk — Selective disclosure presentation
 */

import crypto from 'node:crypto';
import type {
  VerifiableCredential,
  SdJwtVc,
} from '@credverse/trust-core';
import {
  createVerifiablePresentation,
  selectDisclosures,
} from '@credverse/trust-core';
import type {
  PresentationResult,
  PresentationRequest,
  WalletStore,
  WalletCredentialRecord,
} from './types.js';

/**
 * Create a Verifiable Presentation with only the disclosed claims
 * from the credential subject.
 */
export function createSelectivePresentation(params: {
  holder: string;
  credential: VerifiableCredential;
  disclosedClaims: string[];
  nonce?: string;
}): PresentationResult {
  const { holder, credential, disclosedClaims } = params;

  const filteredSubject: Record<string, unknown> = {};
  for (const claim of disclosedClaims) {
    if (claim in credential.credentialSubject) {
      filteredSubject[claim] = credential.credentialSubject[claim];
    }
  }

  const selectiveCredential: VerifiableCredential = {
    ...credential,
    id: `urn:uuid:${crypto.randomUUID()}`,
    credentialSubject: filteredSubject,
  };

  const presentation = createVerifiablePresentation({
    holder,
    credentials: [selectiveCredential],
  });

  return {
    presentation,
    format: 'ldp-vc',
    selectedCredentials: [credential.id],
  };
}

/**
 * Prepare an SD-JWT Verifiable Presentation with only selected disclosures.
 */
export function prepareSdJwtPresentation(params: {
  holder: string;
  sdJwtVc: SdJwtVc;
  selectedClaims: string[];
  nonce?: string;
}): PresentationResult {
  const { sdJwtVc, selectedClaims } = params;

  const filteredDisclosures = selectDisclosures(sdJwtVc.disclosures, selectedClaims);

  const presentedSdJwt: SdJwtVc = {
    jwt: sdJwtVc.jwt,
    disclosures: filteredDisclosures,
    keyBindingJwt: sdJwtVc.keyBindingJwt,
  };

  return {
    presentation: null,
    sdJwtVc: presentedSdJwt,
    format: 'sd-jwt-vc',
    selectedCredentials: [sdJwtVc.jwt],
  };
}

/**
 * Find credentials in the store that match a presentation request.
 */
export function matchCredentialsToRequest(
  store: WalletStore,
  request: PresentationRequest,
): WalletCredentialRecord[] {
  const definition = request.presentationDefinition;
  const all = store.getAll();

  if (!definition || !Array.isArray(definition.input_descriptors)) {
    return all;
  }

  return all.filter((record) =>
    definition.input_descriptors.some((descriptor: { constraints?: { fields?: { path?: string[] }[] } }) => {
      if (!descriptor.constraints?.fields) return true;
      return descriptor.constraints.fields.every((field: { path?: string[] }) => {
        if (!Array.isArray(field.path)) return true;
        return field.path.some((p: string) => {
          const key = p.replace(/^\$\./, '');
          return key in record.credential.credentialSubject || key in record.credential;
        });
      });
    }),
  );
}
