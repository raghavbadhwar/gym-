import { describe, it, expect } from 'vitest';
import {
  // OID4VCI
  createIssuerMetadata,
  createCredentialOffer,
  createTokenResponse,
  validateCredentialRequest,
  createCredentialResponse,
  // Templates
  createTemplate,
  validateSubjectAgainstTemplate,
  universityDegreeTemplate,
  employmentCredentialTemplate,
  ageVerificationTemplate,
  // Status list
  createStatusList,
  addStatusEntry,
  revokeCredential,
  suspendCredential,
  getCredentialStatus,
  encodeStatusList,
} from '../src/index.js';
import type { CredentialConfiguration, StatusList } from '../src/index.js';

// ── OID4VCI Tests ───────────────────────────────────────────────────────────

describe('OID4VCI', () => {
  const issuerUrl = 'https://issuer.example.com';
  const configurations: Record<string, CredentialConfiguration> = {
    UniversityDegree: {
      format: 'jwt-vc',
      types: ['VerifiableCredential', 'UniversityDegreeCredential'],
      cryptographicBindingMethodsSupported: ['did:key'],
      credentialSigningAlgValuesSupported: ['ES256'],
    },
  };

  describe('createIssuerMetadata', () => {
    it('should create metadata with default endpoints', () => {
      const metadata = createIssuerMetadata({ issuerUrl, configurations });

      expect(metadata.credentialIssuer).toBe(issuerUrl);
      expect(metadata.credentialEndpoint).toBe(`${issuerUrl}/credentials`);
      expect(metadata.tokenEndpoint).toBe(`${issuerUrl}/token`);
      expect(metadata.credentialConfigurationsSupported).toBe(configurations);
    });

    it('should allow overriding endpoints', () => {
      const metadata = createIssuerMetadata({
        issuerUrl,
        credentialEndpoint: 'https://custom.example.com/creds',
        tokenEndpoint: 'https://custom.example.com/tok',
        configurations,
      });

      expect(metadata.credentialEndpoint).toBe('https://custom.example.com/creds');
      expect(metadata.tokenEndpoint).toBe('https://custom.example.com/tok');
    });
  });

  describe('createCredentialOffer', () => {
    it('should create a credential offer with pre-authorized code', () => {
      const offer = createCredentialOffer({
        issuerUrl,
        configurationIds: ['UniversityDegree'],
        preAuthorizedCode: 'code-123',
      });

      expect(offer.credentialIssuer).toBe(issuerUrl);
      expect(offer.credentialConfigurationIds).toEqual(['UniversityDegree']);
      expect(offer.grants.preAuthorizedCode.code).toBe('code-123');
      expect(offer.grants.preAuthorizedCode.userPinRequired).toBe(false);
    });

    it('should set userPinRequired when specified', () => {
      const offer = createCredentialOffer({
        issuerUrl,
        configurationIds: ['UniversityDegree'],
        preAuthorizedCode: 'code-456',
        userPinRequired: true,
      });

      expect(offer.grants.preAuthorizedCode.userPinRequired).toBe(true);
    });
  });

  describe('createTokenResponse', () => {
    it('should generate access token and c_nonce when none provided', () => {
      const response = createTokenResponse({});

      expect(response.accessToken).toBeDefined();
      expect(response.accessToken.length).toBeGreaterThan(0);
      expect(response.tokenType).toBe('Bearer');
      expect(response.expiresIn).toBe(86400);
      expect(response.cNonce).toBeDefined();
      expect(response.cNonce.length).toBeGreaterThan(0);
      expect(response.cNonceExpiresIn).toBe(300);
    });

    it('should use provided access token and expiresIn', () => {
      const response = createTokenResponse({
        accessToken: 'my-token',
        expiresIn: 3600,
      });

      expect(response.accessToken).toBe('my-token');
      expect(response.expiresIn).toBe(3600);
    });
  });

  describe('validateCredentialRequest', () => {
    it('should validate a correct request', () => {
      const result = validateCredentialRequest(
        { format: 'jwt-vc', types: ['VerifiableCredential'] },
        ['jwt-vc', 'ldp-vc'],
      );

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject unsupported format', () => {
      const result = validateCredentialRequest(
        { format: 'sd-jwt-vc', types: ['VerifiableCredential'] },
        ['jwt-vc'],
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Unsupported format: sd-jwt-vc');
    });

    it('should reject empty types', () => {
      const result = validateCredentialRequest(
        { format: 'jwt-vc', types: [] },
        ['jwt-vc'],
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Credential types must not be empty');
    });

    it('should reject proof with missing jwt', () => {
      const result = validateCredentialRequest(
        { format: 'jwt-vc', types: ['VC'], proof: { proofType: 'jwt', jwt: '' } },
        ['jwt-vc'],
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Proof JWT must be provided when proof is present');
    });

    it('should accept proof with valid jwt', () => {
      const result = validateCredentialRequest(
        { format: 'jwt-vc', types: ['VC'], proof: { proofType: 'jwt', jwt: 'eyJ...' } },
        ['jwt-vc'],
      );

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should collect multiple errors', () => {
      const result = validateCredentialRequest(
        { format: 'ldp-vc', types: [], proof: { proofType: 'jwt', jwt: '' } },
        ['jwt-vc'],
      );

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('createCredentialResponse', () => {
    it('should wrap credential with format and c_nonce', () => {
      const response = createCredentialResponse({
        format: 'jwt-vc',
        credential: 'eyJhbGciOiJFUzI1NiJ9...',
      });

      expect(response.format).toBe('jwt-vc');
      expect(response.credential).toBe('eyJhbGciOiJFUzI1NiJ9...');
      expect(response.cNonce).toBeDefined();
      expect(response.cNonceExpiresIn).toBe(300);
    });
  });
});

// ── Template Tests ──────────────────────────────────────────────────────────

describe('Templates', () => {
  describe('createTemplate', () => {
    it('should create a template with defaults', () => {
      const template = createTemplate({
        name: 'TestCredential',
        fields: [{ name: 'field1', type: 'string', required: true }],
      });

      expect(template.id).toMatch(/^urn:uuid:/);
      expect(template.name).toBe('TestCredential');
      expect(template.description).toBe('');
      expect(template.types).toEqual(['VerifiableCredential']);
      expect(template.format).toBe('jwt-vc');
      expect(template.subjectFields).toHaveLength(1);
    });

    it('should use provided values', () => {
      const template = createTemplate({
        name: 'Custom',
        description: 'Custom template',
        types: ['VerifiableCredential', 'CustomCredential'],
        fields: [
          { name: 'a', type: 'number', required: true },
          { name: 'b', type: 'boolean', required: false },
        ],
        format: 'ldp-vc',
      });

      expect(template.description).toBe('Custom template');
      expect(template.types).toContain('CustomCredential');
      expect(template.format).toBe('ldp-vc');
      expect(template.subjectFields).toHaveLength(2);
    });
  });

  describe('validateSubjectAgainstTemplate', () => {
    const template = createTemplate({
      name: 'TestTemplate',
      fields: [
        { name: 'name', type: 'string', required: true },
        { name: 'age', type: 'number', required: true },
        { name: 'active', type: 'boolean', required: false },
        { name: 'createdAt', type: 'date', required: false },
      ],
    });

    it('should validate a correct subject', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 'Alice',
        age: 30,
        active: true,
        createdAt: '2024-01-01',
      });

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should pass when optional fields are omitted', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 'Bob',
        age: 25,
      });

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should fail when required fields are missing', () => {
      const result = validateSubjectAgainstTemplate(template, { name: 'Charlie' });

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing required field: age');
    });

    it('should fail when field type is wrong (string expected)', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 123,
        age: 30,
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toEqual(
        expect.arrayContaining([expect.stringContaining('must be a string')]),
      );
    });

    it('should fail when field type is wrong (number expected)', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 'Dave',
        age: 'thirty',
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toEqual(
        expect.arrayContaining([expect.stringContaining('must be a number')]),
      );
    });

    it('should fail when boolean field receives wrong type', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 'Eve',
        age: 22,
        active: 'yes',
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toEqual(
        expect.arrayContaining([expect.stringContaining('must be a boolean')]),
      );
    });

    it('should fail for invalid date string', () => {
      const result = validateSubjectAgainstTemplate(template, {
        name: 'Frank',
        age: 40,
        createdAt: 'not-a-date',
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toEqual(
        expect.arrayContaining([expect.stringContaining('must be a valid date string')]),
      );
    });
  });

  describe('built-in templates', () => {
    it('universityDegreeTemplate has correct structure', () => {
      const t = universityDegreeTemplate();

      expect(t.name).toBe('UniversityDegree');
      expect(t.types).toContain('UniversityDegreeCredential');
      expect(t.subjectFields.map((f) => f.name)).toEqual(
        expect.arrayContaining(['degree', 'university', 'graduationDate', 'gpa']),
      );
      const degreeField = t.subjectFields.find((f) => f.name === 'degree');
      expect(degreeField?.required).toBe(true);
      const gpaField = t.subjectFields.find((f) => f.name === 'gpa');
      expect(gpaField?.required).toBe(false);
    });

    it('employmentCredentialTemplate has correct structure', () => {
      const t = employmentCredentialTemplate();

      expect(t.name).toBe('EmploymentCredential');
      expect(t.types).toContain('EmploymentCredential');
      expect(t.subjectFields.map((f) => f.name)).toEqual(
        expect.arrayContaining(['employer', 'jobTitle', 'startDate']),
      );
      const currentField = t.subjectFields.find((f) => f.name === 'current');
      expect(currentField?.type).toBe('boolean');
      expect(currentField?.required).toBe(false);
    });

    it('ageVerificationTemplate has correct structure', () => {
      const t = ageVerificationTemplate();

      expect(t.name).toBe('AgeVerification');
      expect(t.types).toContain('AgeVerificationCredential');
      expect(t.subjectFields.map((f) => f.name)).toEqual(
        expect.arrayContaining(['birthDate', 'ageOver', 'verified']),
      );
      const verifiedField = t.subjectFields.find((f) => f.name === 'verified');
      expect(verifiedField?.type).toBe('boolean');
      expect(verifiedField?.required).toBe(true);
    });

    it('validates correct subject for universityDegreeTemplate', () => {
      const t = universityDegreeTemplate();
      const result = validateSubjectAgainstTemplate(t, {
        degree: 'B.Sc. Computer Science',
        university: 'MIT',
        graduationDate: '2024-06-15',
        gpa: 3.9,
      });
      expect(result.valid).toBe(true);
    });

    it('rejects invalid subject for employmentCredentialTemplate', () => {
      const t = employmentCredentialTemplate();
      const result = validateSubjectAgainstTemplate(t, {
        employer: 'Acme',
        // missing required jobTitle and startDate
      });
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(2);
    });
  });
});

// ── Status List Tests ───────────────────────────────────────────────────────

describe('Status List', () => {
  describe('createStatusList', () => {
    it('should create a revocation list by default', () => {
      const list = createStatusList({ issuer: 'did:example:issuer' });

      expect(list.id).toMatch(/^urn:uuid:/);
      expect(list.issuer).toBe('did:example:issuer');
      expect(list.purpose).toBe('revocation');
      expect(list.entries).toHaveLength(0);
      expect(list.encodedList).toBeDefined();
    });

    it('should create a suspension list when specified', () => {
      const list = createStatusList({
        issuer: 'did:example:issuer',
        purpose: 'suspension',
      });

      expect(list.purpose).toBe('suspension');
    });

    it('should use provided id', () => {
      const list = createStatusList({
        id: 'custom-id',
        issuer: 'did:example:issuer',
      });

      expect(list.id).toBe('custom-id');
    });
  });

  describe('addStatusEntry', () => {
    it('should add an active entry', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');

      expect(list.entries).toHaveLength(1);
      expect(list.entries[0].credentialId).toBe('cred-1');
      expect(list.entries[0].status).toBe('active');
      expect(list.entries[0].index).toBe(0);
    });

    it('should assign sequential indices', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');
      list = addStatusEntry(list, 'cred-2');
      list = addStatusEntry(list, 'cred-3');

      expect(list.entries).toHaveLength(3);
      expect(list.entries[0].index).toBe(0);
      expect(list.entries[1].index).toBe(1);
      expect(list.entries[2].index).toBe(2);
    });
  });

  describe('revokeCredential', () => {
    it('should mark a credential as revoked', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');
      list = revokeCredential(list, 'cred-1');

      expect(list.entries[0].status).toBe('revoked');
    });
  });

  describe('suspendCredential', () => {
    it('should mark a credential as suspended', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');
      list = suspendCredential(list, 'cred-1');

      expect(list.entries[0].status).toBe('suspended');
    });
  });

  describe('getCredentialStatus', () => {
    it('should return the entry for an existing credential', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');
      list = revokeCredential(list, 'cred-1');

      const entry = getCredentialStatus(list, 'cred-1');
      expect(entry).not.toBeNull();
      expect(entry!.status).toBe('revoked');
      expect(entry!.credentialId).toBe('cred-1');
    });

    it('should return null for a non-existent credential', () => {
      const list = createStatusList({ issuer: 'did:example:issuer' });
      const entry = getCredentialStatus(list, 'cred-unknown');

      expect(entry).toBeNull();
    });
  });

  describe('encodeStatusList', () => {
    it('should encode empty list', () => {
      const list: StatusList = {
        id: 'test',
        issuer: 'did:example:issuer',
        purpose: 'revocation',
        entries: [],
        encodedList: '',
      };

      const encoded = encodeStatusList(list);
      expect(encoded).toBeDefined();
      expect(typeof encoded).toBe('string');
      // Empty list encodes a single zero byte
      const decoded = Buffer.from(encoded, 'base64url');
      expect(decoded).toEqual(Buffer.from([0]));
    });

    it('should encode active entries as zero bits', () => {
      const list: StatusList = {
        id: 'test',
        issuer: 'did:example:issuer',
        purpose: 'revocation',
        entries: [
          { credentialId: 'c1', index: 0, status: 'active', updatedAt: new Date().toISOString() },
          { credentialId: 'c2', index: 1, status: 'active', updatedAt: new Date().toISOString() },
        ],
        encodedList: '',
      };

      const encoded = encodeStatusList(list);
      const decoded = Buffer.from(encoded, 'base64url');
      expect(decoded[0]).toBe(0b00000000);
    });

    it('should encode revoked entries as set bits', () => {
      const list: StatusList = {
        id: 'test',
        issuer: 'did:example:issuer',
        purpose: 'revocation',
        entries: [
          { credentialId: 'c1', index: 0, status: 'revoked', updatedAt: new Date().toISOString() },
          { credentialId: 'c2', index: 1, status: 'active', updatedAt: new Date().toISOString() },
        ],
        encodedList: '',
      };

      const encoded = encodeStatusList(list);
      const decoded = Buffer.from(encoded, 'base64url');
      // Index 0 → bit 7 of byte 0 → 0b10000000 = 128
      expect(decoded[0]).toBe(0b10000000);
    });

    it('should update encodedList after revocation', () => {
      let list = createStatusList({ issuer: 'did:example:issuer' });
      list = addStatusEntry(list, 'cred-1');
      list = addStatusEntry(list, 'cred-2');

      const beforeRevoke = list.encodedList;
      list = revokeCredential(list, 'cred-2');
      expect(list.encodedList).not.toBe(beforeRevoke);
    });
  });
});
