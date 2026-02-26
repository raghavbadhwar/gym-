/**
 * @credverse/wallet-sdk — Comprehensive test suite
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  createInMemoryStore,
  createSelectivePresentation,
  prepareSdJwtPresentation,
  matchCredentialsToRequest,
  createKeyManager,
  type WalletCredentialRecord,
  type WalletStore,
  type PresentationRequest,
  type KeyManager,
} from '../src/index.js';
import {
  createVerifiableCredential,
  createSdJwtVc,
  createDisclosure,
} from '@credverse/trust-core';

// ── Helpers ─────────────────────────────────────────────────────────────────

function makeRecord(overrides: Partial<WalletCredentialRecord> = {}): WalletCredentialRecord {
  const vc = createVerifiableCredential({
    issuer: overrides.issuerDid ?? 'did:example:issuer1',
    subject: { name: 'Alice', degree: 'BSc', gpa: '3.9' },
    types: ['UniversityDegreeCredential'],
  });

  return {
    id: overrides.id ?? vc.id,
    credential: vc,
    format: 'ldp-vc',
    issuedAt: overrides.issuedAt ?? '2024-06-01T00:00:00Z',
    issuerDid: overrides.issuerDid ?? 'did:example:issuer1',
    tags: overrides.tags ?? ['education'],
    metadata: overrides.metadata ?? {},
  };
}

// ── Store tests ─────────────────────────────────────────────────────────────

describe('createInMemoryStore', () => {
  let store: WalletStore;

  beforeEach(() => {
    store = createInMemoryStore();
  });

  // save & getById
  it('should save and retrieve a record by id', () => {
    const record = makeRecord({ id: 'cred-1' });
    store.save(record);
    expect(store.getById('cred-1')).toEqual(record);
  });

  it('should return null for a non-existent id', () => {
    expect(store.getById('does-not-exist')).toBeNull();
  });

  // getAll
  it('should return all saved records', () => {
    const r1 = makeRecord({ id: 'a' });
    const r2 = makeRecord({ id: 'b' });
    store.save(r1);
    store.save(r2);
    expect(store.getAll()).toHaveLength(2);
  });

  it('should return an empty array when store is empty', () => {
    expect(store.getAll()).toEqual([]);
  });

  // remove
  it('should remove an existing record and return true', () => {
    const record = makeRecord({ id: 'del-1' });
    store.save(record);
    expect(store.remove('del-1')).toBe(true);
    expect(store.getById('del-1')).toBeNull();
  });

  it('should return false when removing a non-existent record', () => {
    expect(store.remove('no-such-id')).toBe(false);
  });

  // duplicate save (overwrite)
  it('should overwrite a record when saving with the same id', () => {
    const r1 = makeRecord({ id: 'dup', tags: ['v1'] });
    const r2 = makeRecord({ id: 'dup', tags: ['v2'] });
    store.save(r1);
    store.save(r2);
    expect(store.getAll()).toHaveLength(1);
    expect(store.getById('dup')!.tags).toEqual(['v2']);
  });

  // ── query filters ──

  describe('query', () => {
    beforeEach(() => {
      store.save(makeRecord({ id: 'q1', issuerDid: 'did:example:uni', tags: ['education'], issuedAt: '2024-01-15T00:00:00Z' }));
      store.save(makeRecord({ id: 'q2', issuerDid: 'did:example:corp', tags: ['employment'], issuedAt: '2024-06-01T00:00:00Z' }));
      store.save(makeRecord({ id: 'q3', issuerDid: 'did:example:uni', tags: ['education', 'verified'], issuedAt: '2024-09-01T00:00:00Z' }));
    });

    it('should filter by issuer', () => {
      const results = store.query({ issuer: 'did:example:uni' });
      expect(results).toHaveLength(2);
      expect(results.every((r) => r.issuerDid === 'did:example:uni')).toBe(true);
    });

    it('should filter by credential type', () => {
      const results = store.query({ type: 'UniversityDegreeCredential' });
      expect(results).toHaveLength(3);
    });

    it('should filter by tag', () => {
      const results = store.query({ tag: 'employment' });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('q2');
    });

    it('should filter by issuedAfter (inclusive)', () => {
      const results = store.query({ issuedAfter: '2024-06-01T00:00:00Z' });
      expect(results).toHaveLength(2);
    });

    it('should filter by issuedBefore (exclusive)', () => {
      const results = store.query({ issuedBefore: '2024-06-01T00:00:00Z' });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('q1');
    });

    it('should filter by date range', () => {
      const results = store.query({
        issuedAfter: '2024-02-01T00:00:00Z',
        issuedBefore: '2024-08-01T00:00:00Z',
      });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('q2');
    });

    it('should combine issuer + tag filters (AND logic)', () => {
      const results = store.query({ issuer: 'did:example:uni', tag: 'verified' });
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe('q3');
    });

    it('should return all records when filter is empty', () => {
      expect(store.query({})).toHaveLength(3);
    });

    it('should return empty array when no records match', () => {
      expect(store.query({ issuer: 'did:example:nonexistent' })).toEqual([]);
    });
  });
});

// ── Presentation tests ──────────────────────────────────────────────────────

describe('createSelectivePresentation', () => {
  it('should create a presentation with only the disclosed claims', () => {
    const vc = createVerifiableCredential({
      issuer: 'did:example:issuer',
      subject: { name: 'Alice', degree: 'BSc', gpa: '3.9' },
      types: ['UniversityDegreeCredential'],
    });

    const result = createSelectivePresentation({
      holder: 'did:example:holder',
      credential: vc,
      disclosedClaims: ['name', 'degree'],
    });

    expect(result.format).toBe('ldp-vc');
    expect(result.presentation).not.toBeNull();
    expect(result.selectedCredentials).toEqual([vc.id]);

    const presented = result.presentation!.verifiableCredential[0];
    expect(presented.credentialSubject).toHaveProperty('name', 'Alice');
    expect(presented.credentialSubject).toHaveProperty('degree', 'BSc');
    expect(presented.credentialSubject).not.toHaveProperty('gpa');
  });

  it('should handle disclosing claims that do not exist on the credential', () => {
    const vc = createVerifiableCredential({
      issuer: 'did:example:issuer',
      subject: { name: 'Bob' },
    });

    const result = createSelectivePresentation({
      holder: 'did:example:holder',
      credential: vc,
      disclosedClaims: ['name', 'nonExistentClaim'],
    });

    const presented = result.presentation!.verifiableCredential[0];
    expect(presented.credentialSubject).toEqual({ name: 'Bob' });
  });

  it('should return an empty credentialSubject when no claims are disclosed', () => {
    const vc = createVerifiableCredential({
      issuer: 'did:example:issuer',
      subject: { name: 'Charlie' },
    });

    const result = createSelectivePresentation({
      holder: 'did:example:holder',
      credential: vc,
      disclosedClaims: [],
    });

    expect(result.presentation!.verifiableCredential[0].credentialSubject).toEqual({});
  });

  it('should set the holder on the presentation', () => {
    const vc = createVerifiableCredential({
      issuer: 'did:example:issuer',
      subject: { name: 'Alice' },
    });

    const result = createSelectivePresentation({
      holder: 'did:example:myholder',
      credential: vc,
      disclosedClaims: ['name'],
    });

    expect(result.presentation!.holder).toBe('did:example:myholder');
  });
});

describe('prepareSdJwtPresentation', () => {
  it('should select only the requested disclosures', () => {
    const sdJwt = createSdJwtVc('header.payload.signature', [
      createDisclosure('salt1', 'name', 'Alice'),
      createDisclosure('salt2', 'degree', 'BSc'),
      createDisclosure('salt3', 'gpa', '3.9'),
    ]);

    const result = prepareSdJwtPresentation({
      holder: 'did:example:holder',
      sdJwtVc: sdJwt,
      selectedClaims: ['name', 'gpa'],
    });

    expect(result.format).toBe('sd-jwt-vc');
    expect(result.presentation).toBeNull();
    expect(result.sdJwtVc).toBeDefined();
    expect(result.sdJwtVc!.disclosures).toHaveLength(2);

    const claimNames = result.sdJwtVc!.disclosures.map((d) => d.claimName);
    expect(claimNames).toContain('name');
    expect(claimNames).toContain('gpa');
    expect(claimNames).not.toContain('degree');
  });

  it('should preserve the original jwt and keyBindingJwt', () => {
    const sdJwt = createSdJwtVc(
      'my.jwt.token',
      [createDisclosure('s', 'claim', 'val')],
      'kb-jwt',
    );

    const result = prepareSdJwtPresentation({
      holder: 'did:example:h',
      sdJwtVc: sdJwt,
      selectedClaims: ['claim'],
    });

    expect(result.sdJwtVc!.jwt).toBe('my.jwt.token');
    expect(result.sdJwtVc!.keyBindingJwt).toBe('kb-jwt');
  });

  it('should return empty disclosures when no claims are selected', () => {
    const sdJwt = createSdJwtVc('jwt', [
      createDisclosure('s1', 'a', 1),
      createDisclosure('s2', 'b', 2),
    ]);

    const result = prepareSdJwtPresentation({
      holder: 'did:example:h',
      sdJwtVc: sdJwt,
      selectedClaims: [],
    });

    expect(result.sdJwtVc!.disclosures).toEqual([]);
  });

  it('should track the jwt as selectedCredentials', () => {
    const sdJwt = createSdJwtVc('the.jwt', [createDisclosure('s', 'c', 'v')]);

    const result = prepareSdJwtPresentation({
      holder: 'did:example:h',
      sdJwtVc: sdJwt,
      selectedClaims: ['c'],
    });

    expect(result.selectedCredentials).toEqual(['the.jwt']);
  });
});

describe('matchCredentialsToRequest', () => {
  let store: WalletStore;

  beforeEach(() => {
    store = createInMemoryStore();

    const vc1 = createVerifiableCredential({
      issuer: 'did:example:uni',
      subject: { name: 'Alice', degree: 'BSc' },
      types: ['UniversityDegreeCredential'],
    });
    store.save({ id: 'c1', credential: vc1, format: 'ldp-vc', issuedAt: '2024-01-01T00:00:00Z', issuerDid: 'did:example:uni', tags: [], metadata: {} });

    const vc2 = createVerifiableCredential({
      issuer: 'did:example:corp',
      subject: { employeeId: '123', role: 'engineer' },
      types: ['EmploymentCredential'],
    });
    store.save({ id: 'c2', credential: vc2, format: 'ldp-vc', issuedAt: '2024-01-01T00:00:00Z', issuerDid: 'did:example:corp', tags: [], metadata: {} });
  });

  it('should return all credentials when no input_descriptors are present', () => {
    const request: PresentationRequest = {
      id: 'req-1',
      verifierDid: 'did:example:verifier',
      presentationDefinition: {},
      nonce: 'nonce-1',
    };

    expect(matchCredentialsToRequest(store, request)).toHaveLength(2);
  });

  it('should return all credentials when definition is null', () => {
    const request: PresentationRequest = {
      id: 'req-2',
      verifierDid: 'did:example:verifier',
      presentationDefinition: null,
      nonce: 'nonce-2',
    };

    expect(matchCredentialsToRequest(store, request)).toHaveLength(2);
  });

  it('should match credentials that have the requested fields', () => {
    const request: PresentationRequest = {
      id: 'req-3',
      verifierDid: 'did:example:verifier',
      presentationDefinition: {
        input_descriptors: [
          {
            constraints: {
              fields: [{ path: ['$.degree'] }],
            },
          },
        ],
      },
      nonce: 'nonce-3',
    };

    const matched = matchCredentialsToRequest(store, request);
    expect(matched).toHaveLength(1);
    expect(matched[0].id).toBe('c1');
  });

  it('should match credentials when field path references a top-level VC property', () => {
    const request: PresentationRequest = {
      id: 'req-4',
      verifierDid: 'did:example:verifier',
      presentationDefinition: {
        input_descriptors: [
          {
            constraints: {
              fields: [{ path: ['$.issuer'] }],
            },
          },
        ],
      },
      nonce: 'nonce-4',
    };

    // Both credentials have an issuer field
    expect(matchCredentialsToRequest(store, request)).toHaveLength(2);
  });

  it('should return empty array when no credentials match', () => {
    const request: PresentationRequest = {
      id: 'req-5',
      verifierDid: 'did:example:verifier',
      presentationDefinition: {
        input_descriptors: [
          {
            constraints: {
              fields: [{ path: ['$.nonExistentField'] }],
            },
          },
        ],
      },
      nonce: 'nonce-5',
    };

    expect(matchCredentialsToRequest(store, request)).toEqual([]);
  });

  it('should match when descriptor has no constraints', () => {
    const request: PresentationRequest = {
      id: 'req-6',
      verifierDid: 'did:example:verifier',
      presentationDefinition: {
        input_descriptors: [{}],
      },
      nonce: 'nonce-6',
    };

    expect(matchCredentialsToRequest(store, request)).toHaveLength(2);
  });
});

// ── Key Manager tests ───────────────────────────────────────────────────────

describe('createKeyManager', () => {
  let km: KeyManager;

  beforeEach(() => {
    km = createKeyManager();
  });

  it('should generate a key and return a KeyRecord', async () => {
    const key = await km.generateKey('EdDSA');

    expect(key.id).toBeDefined();
    expect(key.did).toMatch(/^did:key:/);
    expect(key.algorithm).toBe('EdDSA');
    expect(key.createdAt).toBeDefined();
    expect(key.tags).toEqual([]);
  });

  it('should generate keys with different algorithms', async () => {
    const edKey = await km.generateKey('EdDSA');
    const esKey = await km.generateKey('ES256');

    expect(edKey.algorithm).toBe('EdDSA');
    expect(esKey.algorithm).toBe('ES256');
    expect(edKey.id).not.toBe(esKey.id);
  });

  it('should retrieve a generated key by id', async () => {
    const key = await km.generateKey('ES256');
    const retrieved = km.getKey(key.id);

    expect(retrieved).not.toBeNull();
    expect(retrieved!.id).toBe(key.id);
    expect(retrieved!.did).toBe(key.did);
  });

  it('should return null for a non-existent key id', () => {
    expect(km.getKey('no-such-key')).toBeNull();
  });

  it('should list all generated keys', async () => {
    await km.generateKey('EdDSA');
    await km.generateKey('ES256');
    await km.generateKey('ES384');

    const keys = km.listKeys();
    expect(keys).toHaveLength(3);
  });

  it('should return empty array when no keys exist', () => {
    expect(km.listKeys()).toEqual([]);
  });

  it('should rotate a key and return both old and new key', async () => {
    const original = await km.generateKey('EdDSA');
    const { newKey, oldKey } = await km.rotateKey(original.id, 'ES256');

    expect(oldKey.id).toBe(original.id);
    expect(newKey.id).not.toBe(original.id);
    expect(newKey.algorithm).toBe('ES256');
  });

  it('should throw when rotating a non-existent key', async () => {
    await expect(km.rotateKey('missing-key', 'EdDSA')).rejects.toThrow('Key not found: missing-key');
  });

  it('should remove an existing key and return true', async () => {
    const key = await km.generateKey('EdDSA');
    expect(km.removeKey(key.id)).toBe(true);
    expect(km.getKey(key.id)).toBeNull();
  });

  it('should return false when removing a non-existent key', () => {
    expect(km.removeKey('no-key')).toBe(false);
  });

  it('should keep the old key accessible after rotation', async () => {
    const original = await km.generateKey('EdDSA');
    await km.rotateKey(original.id, 'ES256');

    // The old key should still be in the store (rotation does not remove it)
    expect(km.getKey(original.id)).not.toBeNull();
  });
});
