import { describe, it, expect } from 'vitest';
import {
  // OID4VP
  createAuthorizationRequest,
  validateAuthorizationResponse,
  createPresentationDefinition,
  // Policy engine
  evaluatePolicy,
  evaluatePolicies,
  createPolicyRule,
  resolveFieldValue,
  ageCheckPolicy,
  kycCredentialPolicy,
  employerCredentialPolicy,
  // Verification receipts
  createVerificationReceipt,
  serializeReceipt,
  validateReceipt,
  // Types
  type PresentationDefinition,
  type AuthorizationResponse,
  type PolicyRule,
  type VerificationReceipt,
} from '../src/index.js';

// ── OID4VP Tests ────────────────────────────────────────────────────────────

describe('OID4VP', () => {
  const sampleDefinition: PresentationDefinition = {
    id: 'def-1',
    inputDescriptors: [
      {
        id: 'desc-1',
        constraints: {
          fields: [{ path: ['$.credentialSubject.name'] }],
        },
      },
    ],
  };

  describe('createAuthorizationRequest', () => {
    it('generates nonce and state when not provided', () => {
      const req = createAuthorizationRequest({
        clientId: 'client-123',
        redirectUri: 'https://example.com/callback',
        presentationDefinition: sampleDefinition,
      });

      expect(req.responseType).toBe('vp_token');
      expect(req.clientId).toBe('client-123');
      expect(req.redirectUri).toBe('https://example.com/callback');
      expect(req.nonce).toBeDefined();
      expect(req.nonce.length).toBeGreaterThan(0);
      expect(req.state).toBeDefined();
      expect(req.state.length).toBeGreaterThan(0);
      expect(req.presentationDefinition).toEqual(sampleDefinition);
    });

    it('uses provided state when supplied', () => {
      const req = createAuthorizationRequest({
        clientId: 'client-123',
        redirectUri: 'https://example.com/callback',
        presentationDefinition: sampleDefinition,
        state: 'my-custom-state',
      });

      expect(req.state).toBe('my-custom-state');
      expect(req.nonce).toBeDefined();
    });

    it('generates unique nonce/state on each call', () => {
      const req1 = createAuthorizationRequest({
        clientId: 'c',
        redirectUri: 'https://x.com',
        presentationDefinition: sampleDefinition,
      });
      const req2 = createAuthorizationRequest({
        clientId: 'c',
        redirectUri: 'https://x.com',
        presentationDefinition: sampleDefinition,
      });

      expect(req1.nonce).not.toBe(req2.nonce);
      expect(req1.state).not.toBe(req2.state);
    });
  });

  describe('validateAuthorizationResponse', () => {
    const validResponse: AuthorizationResponse = {
      vpToken: 'eyJhbGciOi...',
      presentationSubmission: {
        id: 'sub-1',
        definitionId: 'def-1',
        descriptorMap: [
          { id: 'desc-1', format: 'jwt_vc', path: '$.verifiableCredential[0]' },
        ],
      },
      state: 'expected-state',
    };

    it('accepts a valid response', () => {
      const result = validateAuthorizationResponse(validResponse, 'expected-state', 'nonce-1');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('rejects when state mismatches', () => {
      const result = validateAuthorizationResponse(validResponse, 'wrong-state', 'nonce-1');
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('State mismatch'))).toBe(true);
    });

    it('rejects when vpToken is missing', () => {
      const bad = { ...validResponse, vpToken: '' };
      const result = validateAuthorizationResponse(bad, 'expected-state', 'nonce-1');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing vpToken');
    });

    it('rejects when presentationSubmission is missing', () => {
      const bad = { ...validResponse, presentationSubmission: undefined as any };
      const result = validateAuthorizationResponse(bad, 'expected-state', 'nonce-1');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing presentationSubmission');
    });

    it('rejects when state is missing', () => {
      const bad = { ...validResponse, state: '' };
      const result = validateAuthorizationResponse(bad, 'expected-state', 'nonce-1');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing state');
    });

    it('rejects when expectedNonce is empty', () => {
      const result = validateAuthorizationResponse(validResponse, 'expected-state', '');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Expected nonce must be provided');
    });

    it('rejects when descriptorMap is empty', () => {
      const bad: AuthorizationResponse = {
        ...validResponse,
        presentationSubmission: {
          id: 'sub-1',
          definitionId: 'def-1',
          descriptorMap: [],
        },
      };
      const result = validateAuthorizationResponse(bad, 'expected-state', 'nonce-1');
      expect(result.valid).toBe(false);
      expect(
        result.errors.some((e) => e.includes('descriptorMap must have at least one entry')),
      ).toBe(true);
    });
  });

  describe('createPresentationDefinition', () => {
    it('builds a definition with provided descriptors', () => {
      const def = createPresentationDefinition({
        id: 'pd-1',
        descriptors: [
          {
            id: 'id-card',
            name: 'ID Card',
            purpose: 'Identity verification',
            fields: [
              {
                path: ['$.credentialSubject.name'],
                filter: { type: 'string' },
              },
            ],
          },
        ],
      });

      expect(def.id).toBe('pd-1');
      expect(def.inputDescriptors).toHaveLength(1);
      expect(def.inputDescriptors[0].id).toBe('id-card');
      expect(def.inputDescriptors[0].name).toBe('ID Card');
      expect(def.inputDescriptors[0].purpose).toBe('Identity verification');
      expect(def.inputDescriptors[0].constraints.fields).toHaveLength(1);
      expect(def.inputDescriptors[0].constraints.fields[0].filter).toEqual({ type: 'string' });
    });

    it('generates an id when not provided', () => {
      const def = createPresentationDefinition({
        descriptors: [
          {
            id: 'd1',
            fields: [{ path: ['$.type'] }],
          },
        ],
      });

      expect(def.id).toBeDefined();
      expect(def.id.length).toBeGreaterThan(0);
    });

    it('omits optional name/purpose when not provided', () => {
      const def = createPresentationDefinition({
        descriptors: [
          {
            id: 'd1',
            fields: [{ path: ['$.type'] }],
          },
        ],
      });

      expect(def.inputDescriptors[0]).not.toHaveProperty('name');
      expect(def.inputDescriptors[0]).not.toHaveProperty('purpose');
    });

    it('omits filter when not provided', () => {
      const def = createPresentationDefinition({
        descriptors: [{ id: 'd1', fields: [{ path: ['$.type'] }] }],
      });

      expect(def.inputDescriptors[0].constraints.fields[0]).not.toHaveProperty('filter');
    });
  });
});

// ── Policy Engine Tests ─────────────────────────────────────────────────────

describe('Policy Engine', () => {
  describe('resolveFieldValue', () => {
    it('resolves top-level fields', () => {
      expect(resolveFieldValue({ name: 'Alice' }, 'name')).toBe('Alice');
    });

    it('resolves nested fields', () => {
      const data = { credentialSubject: { age: 25, address: { city: 'NYC' } } };
      expect(resolveFieldValue(data, 'credentialSubject.age')).toBe(25);
      expect(resolveFieldValue(data, 'credentialSubject.address.city')).toBe('NYC');
    });

    it('returns undefined for missing paths', () => {
      expect(resolveFieldValue({ a: 1 }, 'b')).toBeUndefined();
      expect(resolveFieldValue({ a: { b: 1 } }, 'a.c')).toBeUndefined();
    });

    it('returns undefined when traversing through a non-object', () => {
      expect(resolveFieldValue({ a: 'string' }, 'a.b')).toBeUndefined();
    });

    it('returns undefined when traversing through null', () => {
      expect(resolveFieldValue({ a: null } as any, 'a.b')).toBeUndefined();
    });
  });

  describe('evaluatePolicy — all operators', () => {
    function makeRule(field: string, operator: string, value: unknown): PolicyRule {
      return createPolicyRule({ name: 'test', field, operator: operator as any, value });
    }

    it('equals — passes when values match', () => {
      const result = evaluatePolicy(makeRule('status', 'equals', 'active'), { status: 'active' });
      expect(result.passed).toBe(true);
    });

    it('equals — fails when values differ', () => {
      const result = evaluatePolicy(makeRule('status', 'equals', 'active'), {
        status: 'inactive',
      });
      expect(result.passed).toBe(false);
      expect(result.reason).toContain('Expected active');
    });

    it('not_equals — passes when values differ', () => {
      const result = evaluatePolicy(makeRule('status', 'not_equals', 'banned'), {
        status: 'active',
      });
      expect(result.passed).toBe(true);
    });

    it('not_equals — fails when values match', () => {
      const result = evaluatePolicy(makeRule('status', 'not_equals', 'banned'), {
        status: 'banned',
      });
      expect(result.passed).toBe(false);
    });

    it('greater_than — passes when field > value', () => {
      const result = evaluatePolicy(makeRule('age', 'greater_than', 17), { age: 18 });
      expect(result.passed).toBe(true);
    });

    it('greater_than — fails when field <= value', () => {
      const result = evaluatePolicy(makeRule('age', 'greater_than', 18), { age: 18 });
      expect(result.passed).toBe(false);
    });

    it('greater_than — fails for non-numeric field', () => {
      const result = evaluatePolicy(makeRule('age', 'greater_than', 17), { age: 'old' });
      expect(result.passed).toBe(false);
    });

    it('less_than — passes when field < value', () => {
      const result = evaluatePolicy(makeRule('score', 'less_than', 100), { score: 50 });
      expect(result.passed).toBe(true);
    });

    it('less_than — fails when field >= value', () => {
      const result = evaluatePolicy(makeRule('score', 'less_than', 50), { score: 50 });
      expect(result.passed).toBe(false);
    });

    it('contains — passes for substring match', () => {
      const result = evaluatePolicy(makeRule('email', 'contains', '@example'), {
        email: 'user@example.com',
      });
      expect(result.passed).toBe(true);
    });

    it('contains — fails for missing substring', () => {
      const result = evaluatePolicy(makeRule('email', 'contains', '@corp'), {
        email: 'user@example.com',
      });
      expect(result.passed).toBe(false);
    });

    it('contains — passes for array containing value', () => {
      const result = evaluatePolicy(makeRule('roles', 'contains', 'admin'), {
        roles: ['user', 'admin'],
      });
      expect(result.passed).toBe(true);
    });

    it('contains — fails for array not containing value', () => {
      const result = evaluatePolicy(makeRule('roles', 'contains', 'superadmin'), {
        roles: ['user', 'admin'],
      });
      expect(result.passed).toBe(false);
    });

    it('contains — fails for non-string/non-array field', () => {
      const result = evaluatePolicy(makeRule('count', 'contains', 5), { count: 5 });
      expect(result.passed).toBe(false);
      expect(result.reason).toContain('not a string or array');
    });

    it('exists — passes when field is present', () => {
      const result = evaluatePolicy(makeRule('name', 'exists', true), { name: 'Alice' });
      expect(result.passed).toBe(true);
    });

    it('exists — fails when field is undefined', () => {
      const result = evaluatePolicy(makeRule('missing', 'exists', true), { name: 'Alice' });
      expect(result.passed).toBe(false);
    });

    it('exists — fails when field is null', () => {
      const result = evaluatePolicy(makeRule('val', 'exists', true), { val: null });
      expect(result.passed).toBe(false);
    });

    it('in — passes when field value is in allowed set', () => {
      const result = evaluatePolicy(makeRule('country', 'in', ['US', 'CA', 'UK']), {
        country: 'US',
      });
      expect(result.passed).toBe(true);
    });

    it('in — fails when field value is not in allowed set', () => {
      const result = evaluatePolicy(makeRule('country', 'in', ['US', 'CA', 'UK']), {
        country: 'FR',
      });
      expect(result.passed).toBe(false);
      expect(result.reason).toContain('not in allowed set');
    });
  });

  describe('evaluatePolicies', () => {
    const passingRule = createPolicyRule({
      id: 'p1',
      name: 'pass',
      field: 'active',
      operator: 'equals',
      value: true,
    });
    const failingRule = createPolicyRule({
      id: 'p2',
      name: 'fail',
      field: 'active',
      operator: 'equals',
      value: false,
    });

    it('returns approved when all policies pass', () => {
      const { results, allPassed, decision } = evaluatePolicies(
        [passingRule],
        { active: true },
      );
      expect(allPassed).toBe(true);
      expect(decision).toBe('approved');
      expect(results).toHaveLength(1);
      expect(results[0].passed).toBe(true);
    });

    it('returns review_required when minority of policies fail', () => {
      const pass2 = createPolicyRule({
        id: 'p3',
        name: 'pass2',
        field: 'active',
        operator: 'equals',
        value: true,
      });
      // 1 fail out of 3 → failedCount (1) <= total/2 (1.5) → review_required
      const { allPassed, decision } = evaluatePolicies(
        [passingRule, failingRule, pass2],
        { active: true },
      );
      expect(allPassed).toBe(false);
      expect(decision).toBe('review_required');
    });

    it('returns denied when majority of policies fail', () => {
      const fail2 = createPolicyRule({
        id: 'p4',
        name: 'fail2',
        field: 'score',
        operator: 'greater_than',
        value: 100,
      });
      // 2 fail out of 3 → failedCount (2) > total/2 (1.5) → denied
      const { allPassed, decision } = evaluatePolicies(
        [passingRule, failingRule, fail2],
        { active: true, score: 50 },
      );
      expect(allPassed).toBe(false);
      expect(decision).toBe('denied');
    });
  });

  describe('sample policy factories', () => {
    it('ageCheckPolicy passes for age >= minimum', () => {
      const rule = ageCheckPolicy(18);
      // Uses greater_than with minimumAge - 1 = 17, so age 18 passes
      const result = evaluatePolicy(rule, { credentialSubject: { age: 18 } });
      expect(result.passed).toBe(true);
    });

    it('ageCheckPolicy fails for age < minimum', () => {
      const rule = ageCheckPolicy(18);
      const result = evaluatePolicy(rule, { credentialSubject: { age: 17 } });
      expect(result.passed).toBe(false);
    });

    it('kycCredentialPolicy passes when kycVerified is true', () => {
      const rule = kycCredentialPolicy();
      const result = evaluatePolicy(rule, { credentialSubject: { kycVerified: true } });
      expect(result.passed).toBe(true);
    });

    it('kycCredentialPolicy fails when kycVerified is false', () => {
      const rule = kycCredentialPolicy();
      const result = evaluatePolicy(rule, { credentialSubject: { kycVerified: false } });
      expect(result.passed).toBe(false);
    });

    it('employerCredentialPolicy passes for matching employer', () => {
      const rule = employerCredentialPolicy('Acme Corp');
      const result = evaluatePolicy(rule, { credentialSubject: { employer: 'Acme Corp' } });
      expect(result.passed).toBe(true);
    });

    it('employerCredentialPolicy fails for non-matching employer', () => {
      const rule = employerCredentialPolicy('Acme Corp');
      const result = evaluatePolicy(rule, { credentialSubject: { employer: 'Other Inc' } });
      expect(result.passed).toBe(false);
    });
  });
});

// ── Verification Receipt Tests ──────────────────────────────────────────────

describe('Verification Receipts', () => {
  describe('createVerificationReceipt', () => {
    it('creates a receipt with generated id and timestamp', () => {
      const receipt = createVerificationReceipt({
        verifierId: 'verifier-1',
        subjectDid: 'did:example:subject',
        policiesApplied: ['age-check', 'kyc-check'],
        decision: 'approved',
        evidenceHashes: ['hash1', 'hash2'],
      });

      expect(receipt.id).toBeDefined();
      expect(receipt.id.length).toBeGreaterThan(0);
      expect(receipt.timestamp).toBeDefined();
      expect(Date.parse(receipt.timestamp)).not.toBeNaN();
      expect(receipt.verifierId).toBe('verifier-1');
      expect(receipt.subjectDid).toBe('did:example:subject');
      expect(receipt.policiesApplied).toEqual(['age-check', 'kyc-check']);
      expect(receipt.decision).toBe('approved');
      expect(receipt.evidenceHashes).toEqual(['hash1', 'hash2']);
    });

    it('defaults evidenceHashes to empty array', () => {
      const receipt = createVerificationReceipt({
        verifierId: 'v1',
        subjectDid: 'did:example:s1',
        policiesApplied: [],
        decision: 'denied',
      });

      expect(receipt.evidenceHashes).toEqual([]);
    });
  });

  describe('serializeReceipt', () => {
    it('serializes to canonical JSON with sorted keys', () => {
      const receipt: VerificationReceipt = {
        id: 'r-1',
        timestamp: '2024-01-01T00:00:00.000Z',
        verifierId: 'v-1',
        subjectDid: 'did:example:s',
        policiesApplied: ['p1'],
        decision: 'approved',
        evidenceHashes: ['h1'],
      };

      const serialized = serializeReceipt(receipt);
      const parsed = JSON.parse(serialized);

      // Sorted keys should produce consistent output
      const keys = Object.keys(parsed);
      const sortedKeys = [...keys].sort();
      expect(keys).toEqual(sortedKeys);

      // Values preserved
      expect(parsed.id).toBe('r-1');
      expect(parsed.decision).toBe('approved');
    });
  });

  describe('validateReceipt', () => {
    const validReceipt: VerificationReceipt = {
      id: 'r-1',
      timestamp: '2024-01-01T00:00:00.000Z',
      verifierId: 'v-1',
      subjectDid: 'did:example:s',
      policiesApplied: ['p1'],
      decision: 'approved',
      evidenceHashes: ['h1'],
    };

    it('validates a correct receipt', () => {
      const result = validateReceipt(validReceipt);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('rejects missing id', () => {
      const result = validateReceipt({ ...validReceipt, id: '' });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing id');
    });

    it('rejects missing timestamp', () => {
      const result = validateReceipt({ ...validReceipt, timestamp: '' });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing timestamp');
    });

    it('rejects invalid timestamp format', () => {
      const result = validateReceipt({ ...validReceipt, timestamp: 'not-a-date' });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Invalid timestamp format');
    });

    it('rejects missing verifierId', () => {
      const result = validateReceipt({ ...validReceipt, verifierId: '' });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing verifierId');
    });

    it('rejects missing subjectDid', () => {
      const result = validateReceipt({ ...validReceipt, subjectDid: '' });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing subjectDid');
    });

    it('rejects non-array policiesApplied', () => {
      const result = validateReceipt({ ...validReceipt, policiesApplied: 'not-array' as any });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('policiesApplied must be an array');
    });

    it('rejects invalid decision', () => {
      const result = validateReceipt({ ...validReceipt, decision: 'maybe' as any });
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('Invalid decision'))).toBe(true);
    });

    it('rejects non-array evidenceHashes', () => {
      const result = validateReceipt({ ...validReceipt, evidenceHashes: 'not-array' as any });
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('evidenceHashes must be an array');
    });
  });
});
