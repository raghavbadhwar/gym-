import { describe, it, expect } from 'vitest';
import {
  // DID
  createDidKey,
  createDidWeb,
  resolveDidDocument,
  extractVerificationMethod,
  // VC
  createVerifiableCredential,
  validateCredentialStructure,
  createVerifiablePresentation,
  // SD-JWT
  createDisclosure,
  encodeDisclosure,
  decodeDisclosure,
  selectDisclosures,
  createSdJwtVc,
  parseSdJwtVc,
  serializeSdJwtVc,
  // Crypto
  generateSalt,
  sha256,
  canonicalize,
  base64urlEncode,
  base64urlDecode,
  generateKeyPair,
  // Types
  type VerifiableCredential,
  type DIDDocument,
} from '../src/index.js';

// ── DID Tests ────────────────────────────────────────────────────────────────

describe('DID utilities', () => {
  describe('createDidKey', () => {
    it('should create a did:key from raw public key bytes', () => {
      const publicKey = new Uint8Array(32).fill(1);
      const did = createDidKey(publicKey);
      expect(did).toMatch(/^did:key:z/);
    });

    it('should produce deterministic output for the same key', () => {
      const key = new Uint8Array(32).fill(42);
      expect(createDidKey(key)).toBe(createDidKey(key));
    });

    it('should produce different DIDs for different keys', () => {
      const key1 = new Uint8Array(32).fill(1);
      const key2 = new Uint8Array(32).fill(2);
      expect(createDidKey(key1)).not.toBe(createDidKey(key2));
    });

    it('should handle zero-byte keys', () => {
      const key = new Uint8Array(32).fill(0);
      const did = createDidKey(key);
      expect(did).toMatch(/^did:key:z/);
    });
  });

  describe('createDidWeb', () => {
    it('should create a did:web from a domain', () => {
      expect(createDidWeb('example.com')).toBe('did:web:example.com');
    });

    it('should create a did:web with an optional path', () => {
      expect(createDidWeb('example.com', 'issuer')).toBe('did:web:example.com:issuer');
    });

    it('should encode colons in domain as %3A', () => {
      expect(createDidWeb('localhost:8080')).toBe('did:web:localhost%3A8080');
    });

    it('should encode colons and append path', () => {
      expect(createDidWeb('localhost:3000', 'users')).toBe(
        'did:web:localhost%3A3000:users',
      );
    });
  });

  describe('resolveDidDocument', () => {
    it('should resolve a did:key document with Ed25519 verification method', () => {
      const key = new Uint8Array(32).fill(7);
      const did = createDidKey(key);
      const doc = resolveDidDocument(did);

      expect(doc.id).toBe(did);
      expect(doc.verificationMethod).toHaveLength(1);
      expect(doc.verificationMethod[0].type).toBe('Ed25519VerificationKey2020');
      expect(doc.verificationMethod[0].controller).toBe(did);
      expect(doc.verificationMethod[0].publicKeyMultibase).toBeDefined();
      expect(doc.authentication).toEqual([`${did}#key-1`]);
      expect(doc.assertionMethod).toEqual([`${did}#key-1`]);
      expect(doc.service).toEqual([]);
    });

    it('should resolve a did:web document with JsonWebKey2020', () => {
      const doc = resolveDidDocument('did:web:example.com');

      expect(doc.id).toBe('did:web:example.com');
      expect(doc.verificationMethod).toHaveLength(1);
      expect(doc.verificationMethod[0].type).toBe('JsonWebKey2020');
      expect(doc.authentication).toEqual(['did:web:example.com#key-1']);
    });

    it('should return a minimal document for unknown DID methods', () => {
      const doc = resolveDidDocument('did:example:123');

      expect(doc.id).toBe('did:example:123');
      expect(doc.verificationMethod).toEqual([]);
      expect(doc.authentication).toEqual([]);
      expect(doc.assertionMethod).toEqual([]);
    });

    it('should throw for invalid DID strings', () => {
      expect(() => resolveDidDocument('not-a-did')).toThrow('Invalid DID');
      expect(() => resolveDidDocument('')).toThrow('Invalid DID');
    });
  });

  describe('extractVerificationMethod', () => {
    it('should extract the first verification method by purpose', () => {
      const did = createDidKey(new Uint8Array(32).fill(5));
      const doc = resolveDidDocument(did);

      const vm = extractVerificationMethod(doc, 'authentication');
      expect(vm).not.toBeNull();
      expect(vm!.id).toBe(`${did}#key-1`);
      expect(vm!.type).toBe('Ed25519VerificationKey2020');
    });

    it('should return null for empty purpose arrays', () => {
      const doc: DIDDocument = {
        id: 'did:example:empty',
        verificationMethod: [],
        authentication: [],
        assertionMethod: [],
        service: [],
      };

      expect(extractVerificationMethod(doc, 'authentication')).toBeNull();
    });

    it('should return null for non-existent purpose', () => {
      const doc = resolveDidDocument('did:web:example.com');
      expect(extractVerificationMethod(doc, 'keyAgreement')).toBeNull();
    });

    it('should return null when ref does not match any verification method', () => {
      const doc: DIDDocument = {
        id: 'did:example:mismatch',
        verificationMethod: [
          { id: 'did:example:mismatch#key-1', type: 'Test', controller: 'did:example:mismatch' },
        ],
        authentication: ['did:example:mismatch#key-999'],
        assertionMethod: [],
        service: [],
      };

      expect(extractVerificationMethod(doc, 'authentication')).toBeNull();
    });

    it('should work with assertionMethod purpose', () => {
      const did = createDidKey(new Uint8Array(32).fill(9));
      const doc = resolveDidDocument(did);

      const vm = extractVerificationMethod(doc, 'assertionMethod');
      expect(vm).not.toBeNull();
      expect(vm!.id).toBe(`${did}#key-1`);
    });
  });
});

// ── VC Tests ─────────────────────────────────────────────────────────────────

describe('Verifiable Credential utilities', () => {
  describe('createVerifiableCredential', () => {
    it('should create a VC with required fields', () => {
      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: { id: 'did:key:z123', name: 'Alice' },
      });

      expect(vc['@context']).toContain('https://www.w3.org/ns/credentials/v2');
      expect(vc.id).toMatch(/^urn:uuid:/);
      expect(vc.type).toContain('VerifiableCredential');
      expect(vc.issuer).toBe('did:web:example.com');
      expect(vc.validFrom).toBeDefined();
      expect(vc.credentialSubject).toEqual({ id: 'did:key:z123', name: 'Alice' });
    });

    it('should include custom types', () => {
      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: { degree: 'BSc' },
        types: ['UniversityDegreeCredential'],
      });

      expect(vc.type).toContain('VerifiableCredential');
      expect(vc.type).toContain('UniversityDegreeCredential');
    });

    it('should accept custom validFrom and validUntil', () => {
      const from = '2024-01-01T00:00:00Z';
      const until = '2025-01-01T00:00:00Z';

      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: {},
        validFrom: from,
        validUntil: until,
      });

      expect(vc.validFrom).toBe(from);
      expect(vc.validUntil).toBe(until);
    });

    it('should not include validUntil when not provided', () => {
      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: {},
      });

      expect(vc.validUntil).toBeUndefined();
    });

    it('should include credentialStatus when provided', () => {
      const status = {
        id: 'https://example.com/status/1',
        type: 'StatusList2021Entry',
        statusPurpose: 'revocation',
        statusListIndex: '42',
        statusListCredential: 'https://example.com/status-list',
      };

      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: {},
        credentialStatus: status,
      });

      expect(vc.credentialStatus).toEqual(status);
    });

    it('should generate unique IDs for each credential', () => {
      const vc1 = createVerifiableCredential({ issuer: 'did:web:a.com', subject: {} });
      const vc2 = createVerifiableCredential({ issuer: 'did:web:a.com', subject: {} });
      expect(vc1.id).not.toBe(vc2.id);
    });
  });

  describe('validateCredentialStructure', () => {
    const makeValidVc = (): VerifiableCredential => ({
      '@context': ['https://www.w3.org/ns/credentials/v2'],
      id: 'urn:uuid:test-id',
      type: ['VerifiableCredential'],
      issuer: 'did:web:example.com',
      validFrom: '2024-01-01T00:00:00Z',
      credentialSubject: { name: 'Alice' },
    });

    it('should validate a correct credential', () => {
      const result = validateCredentialStructure(makeValidVc());
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject missing @context', () => {
      const vc = makeValidVc();
      (vc as Record<string, unknown>)['@context'] = undefined;
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('@context must be a non-empty array');
    });

    it('should reject @context without the W3C v2 context', () => {
      const vc = makeValidVc();
      vc['@context'] = ['https://wrong.context'];
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('must include'))).toBe(true);
    });

    it('should reject empty id', () => {
      const vc = makeValidVc();
      vc.id = '';
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('id must be a non-empty string');
    });

    it('should reject whitespace-only id', () => {
      const vc = makeValidVc();
      vc.id = '   ';
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
    });

    it('should reject missing VerifiableCredential type', () => {
      const vc = makeValidVc();
      vc.type = ['SomeOtherType'];
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.includes('VerifiableCredential'))).toBe(true);
    });

    it('should reject empty issuer', () => {
      const vc = makeValidVc();
      vc.issuer = '';
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
    });

    it('should reject missing validFrom', () => {
      const vc = makeValidVc();
      (vc as Record<string, unknown>).validFrom = undefined;
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
    });

    it('should reject array credentialSubject', () => {
      const vc = makeValidVc();
      (vc as Record<string, unknown>).credentialSubject = ['invalid'];
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('credentialSubject must be a non-null object');
    });

    it('should reject null credentialSubject', () => {
      const vc = makeValidVc();
      (vc as Record<string, unknown>).credentialSubject = null;
      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
    });

    it('should collect multiple errors at once', () => {
      const vc = {
        '@context': ['wrong'],
        id: '',
        type: ['wrong'],
        issuer: '',
        validFrom: '',
        credentialSubject: null,
      } as unknown as VerifiableCredential;

      const result = validateCredentialStructure(vc);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('createVerifiablePresentation', () => {
    it('should create a VP with credentials', () => {
      const vc = createVerifiableCredential({
        issuer: 'did:web:example.com',
        subject: { name: 'Alice' },
      });

      const vp = createVerifiablePresentation({
        holder: 'did:key:zHolder',
        credentials: [vc],
      });

      expect(vp['@context']).toContain('https://www.w3.org/ns/credentials/v2');
      expect(vp.id).toMatch(/^urn:uuid:/);
      expect(vp.type).toContain('VerifiablePresentation');
      expect(vp.holder).toBe('did:key:zHolder');
      expect(vp.verifiableCredential).toHaveLength(1);
      expect(vp.verifiableCredential[0]).toEqual(vc);
    });

    it('should support an empty credentials array', () => {
      const vp = createVerifiablePresentation({
        holder: 'did:web:holder.com',
        credentials: [],
      });

      expect(vp.verifiableCredential).toEqual([]);
    });

    it('should generate unique IDs for each presentation', () => {
      const vp1 = createVerifiablePresentation({ holder: 'did:web:a.com', credentials: [] });
      const vp2 = createVerifiablePresentation({ holder: 'did:web:a.com', credentials: [] });
      expect(vp1.id).not.toBe(vp2.id);
    });
  });
});

// ── SD-JWT Tests ─────────────────────────────────────────────────────────────

describe('SD-JWT utilities', () => {
  describe('createDisclosure', () => {
    it('should create a disclosure triple', () => {
      const d = createDisclosure('salt123', 'name', 'Alice');
      expect(d).toEqual({ salt: 'salt123', claimName: 'name', claimValue: 'Alice' });
    });

    it('should support complex claim values', () => {
      const d = createDisclosure('s', 'address', { city: 'Berlin', zip: '10115' });
      expect(d.claimValue).toEqual({ city: 'Berlin', zip: '10115' });
    });

    it('should support null claim values', () => {
      const d = createDisclosure('s', 'field', null);
      expect(d.claimValue).toBeNull();
    });

    it('should support numeric claim values', () => {
      const d = createDisclosure('s', 'age', 30);
      expect(d.claimValue).toBe(30);
    });
  });

  describe('encodeDisclosure / decodeDisclosure roundtrip', () => {
    it('should encode and decode a string disclosure', () => {
      const original = createDisclosure('abc', 'email', 'alice@example.com');
      const encoded = encodeDisclosure(original);
      const decoded = decodeDisclosure(encoded);
      expect(decoded).toEqual(original);
    });

    it('should encode and decode a numeric disclosure', () => {
      const original = createDisclosure('xyz', 'age', 25);
      const encoded = encodeDisclosure(original);
      const decoded = decodeDisclosure(encoded);
      expect(decoded).toEqual(original);
    });

    it('should encode and decode an object disclosure', () => {
      const original = createDisclosure('s1', 'address', { street: '123 Main St' });
      const encoded = encodeDisclosure(original);
      const decoded = decodeDisclosure(encoded);
      expect(decoded).toEqual(original);
    });

    it('should encode and decode a boolean disclosure', () => {
      const original = createDisclosure('s2', 'verified', true);
      const encoded = encodeDisclosure(original);
      const decoded = decodeDisclosure(encoded);
      expect(decoded).toEqual(original);
    });

    it('should encode and decode a null disclosure', () => {
      const original = createDisclosure('s3', 'optional', null);
      const encoded = encodeDisclosure(original);
      const decoded = decodeDisclosure(encoded);
      expect(decoded).toEqual(original);
    });

    it('should produce base64url-safe output (no +, /, or =)', () => {
      const d = createDisclosure('salt', 'name', 'value');
      const encoded = encodeDisclosure(d);
      expect(encoded).not.toMatch(/[+/=]/);
    });
  });

  describe('selectDisclosures', () => {
    const disclosures = [
      createDisclosure('s1', 'name', 'Alice'),
      createDisclosure('s2', 'email', 'alice@example.com'),
      createDisclosure('s3', 'age', 30),
      createDisclosure('s4', 'address', { city: 'Berlin' }),
    ];

    it('should select only the requested claims', () => {
      const selected = selectDisclosures(disclosures, ['name', 'age']);
      expect(selected).toHaveLength(2);
      expect(selected.map((d) => d.claimName)).toEqual(['name', 'age']);
    });

    it('should return empty when no claims match', () => {
      const selected = selectDisclosures(disclosures, ['nonexistent']);
      expect(selected).toEqual([]);
    });

    it('should return empty when selectedClaims is empty', () => {
      const selected = selectDisclosures(disclosures, []);
      expect(selected).toEqual([]);
    });

    it('should return all when all claims are selected', () => {
      const selected = selectDisclosures(disclosures, ['name', 'email', 'age', 'address']);
      expect(selected).toHaveLength(4);
    });

    it('should ignore duplicate selected claims', () => {
      const selected = selectDisclosures(disclosures, ['name', 'name']);
      expect(selected).toHaveLength(1);
    });
  });

  describe('createSdJwtVc', () => {
    it('should create an SD-JWT VC envelope', () => {
      const d = [createDisclosure('s', 'name', 'Alice')];
      const sdJwt = createSdJwtVc('header.payload.sig', d);
      expect(sdJwt.jwt).toBe('header.payload.sig');
      expect(sdJwt.disclosures).toEqual(d);
      expect(sdJwt.keyBindingJwt).toBeUndefined();
    });

    it('should include key-binding JWT when provided', () => {
      const sdJwt = createSdJwtVc('jwt', [], 'kb-jwt');
      expect(sdJwt.keyBindingJwt).toBe('kb-jwt');
    });

    it('should support empty disclosures', () => {
      const sdJwt = createSdJwtVc('jwt', []);
      expect(sdJwt.disclosures).toEqual([]);
    });
  });

  describe('parseSdJwtVc / serializeSdJwtVc roundtrip', () => {
    it('should roundtrip an SD-JWT VC without key binding', () => {
      const disclosures = [
        createDisclosure('s1', 'name', 'Alice'),
        createDisclosure('s2', 'age', 25),
      ];
      const original = createSdJwtVc('header.payload.sig', disclosures);
      const serialized = serializeSdJwtVc(original);
      const parsed = parseSdJwtVc(serialized);

      expect(parsed.jwt).toBe('header.payload.sig');
      expect(parsed.disclosures).toEqual(disclosures);
      expect(parsed.keyBindingJwt).toBeUndefined();
    });

    it('should roundtrip an SD-JWT VC with key binding', () => {
      const disclosures = [createDisclosure('s1', 'email', 'a@b.com')];
      const original = createSdJwtVc('jwt-token', disclosures, 'kb-jwt-token');
      const serialized = serializeSdJwtVc(original);
      const parsed = parseSdJwtVc(serialized);

      expect(parsed.jwt).toBe('jwt-token');
      expect(parsed.disclosures).toEqual(disclosures);
      expect(parsed.keyBindingJwt).toBe('kb-jwt-token');
    });

    it('should roundtrip with empty disclosures', () => {
      const original = createSdJwtVc('jwt-only', []);
      const serialized = serializeSdJwtVc(original);
      const parsed = parseSdJwtVc(serialized);

      expect(parsed.jwt).toBe('jwt-only');
      expect(parsed.disclosures).toEqual([]);
      expect(parsed.keyBindingJwt).toBeUndefined();
    });

    it('should handle serialization format correctly (trailing ~)', () => {
      const disclosures = [createDisclosure('s', 'x', 'y')];
      const serialized = serializeSdJwtVc(createSdJwtVc('jwt', disclosures));
      expect(serialized).toMatch(/^jwt~.+~$/);
    });

    it('should handle key-binding JWT format (no trailing ~)', () => {
      const serialized = serializeSdJwtVc(createSdJwtVc('jwt', [], 'kb'));
      expect(serialized).toBe('jwt~kb');
    });
  });
});

// ── Crypto Tests ─────────────────────────────────────────────────────────────

describe('Crypto utilities', () => {
  describe('generateSalt', () => {
    it('should return a non-empty base64url string', () => {
      const salt = generateSalt();
      expect(salt).toBeTruthy();
      expect(typeof salt).toBe('string');
      expect(salt.length).toBeGreaterThan(0);
    });

    it('should generate unique salts', () => {
      const salts = new Set(Array.from({ length: 50 }, () => generateSalt()));
      expect(salts.size).toBe(50);
    });

    it('should produce base64url-safe output', () => {
      const salt = generateSalt();
      expect(salt).not.toMatch(/[+/=]/);
    });
  });

  describe('sha256', () => {
    it('should produce a 64-character hex string', () => {
      const hash = sha256('hello');
      expect(hash).toMatch(/^[a-f0-9]{64}$/);
    });

    it('should be deterministic', () => {
      expect(sha256('test')).toBe(sha256('test'));
    });

    it('should produce known hash for empty string', () => {
      expect(sha256('')).toBe(
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      );
    });

    it('should produce different hashes for different inputs', () => {
      expect(sha256('a')).not.toBe(sha256('b'));
    });

    it('should handle unicode strings', () => {
      const hash = sha256('héllo wörld 🌍');
      expect(hash).toMatch(/^[a-f0-9]{64}$/);
    });
  });

  describe('canonicalize', () => {
    it('should sort object keys lexicographically', () => {
      expect(canonicalize({ b: 2, a: 1 })).toBe('{"a":1,"b":2}');
    });

    it('should handle nested objects', () => {
      const result = canonicalize({ z: { b: 2, a: 1 }, a: 'first' });
      expect(result).toBe('{"a":"first","z":{"a":1,"b":2}}');
    });

    it('should handle arrays (preserve order)', () => {
      expect(canonicalize([3, 1, 2])).toBe('[3,1,2]');
    });

    it('should handle arrays with objects', () => {
      expect(canonicalize([{ b: 1, a: 2 }])).toBe('[{"a":2,"b":1}]');
    });

    it('should handle null', () => {
      expect(canonicalize(null)).toBe('null');
    });

    it('should handle undefined', () => {
      expect(canonicalize(undefined)).toBe('null');
    });

    it('should handle booleans', () => {
      expect(canonicalize(true)).toBe('true');
      expect(canonicalize(false)).toBe('false');
    });

    it('should handle numbers', () => {
      expect(canonicalize(42)).toBe('42');
      expect(canonicalize(3.14)).toBe('3.14');
      expect(canonicalize(0)).toBe('0');
    });

    it('should handle strings', () => {
      expect(canonicalize('hello')).toBe('"hello"');
    });

    it('should handle empty objects', () => {
      expect(canonicalize({})).toBe('{}');
    });

    it('should handle empty arrays', () => {
      expect(canonicalize([])).toBe('[]');
    });

    it('should produce deterministic output', () => {
      const obj = { c: [1, { z: true, a: false }], a: 'x', b: null };
      expect(canonicalize(obj)).toBe(canonicalize(obj));
    });

    it('should produce identical output for differently-ordered objects', () => {
      const obj1 = { a: 1, b: 2, c: 3 };
      const obj2 = { c: 3, a: 1, b: 2 };
      expect(canonicalize(obj1)).toBe(canonicalize(obj2));
    });
  });

  describe('base64urlEncode / base64urlDecode roundtrip', () => {
    it('should roundtrip a simple string', () => {
      const original = 'Hello, World!';
      expect(base64urlDecode(base64urlEncode(original))).toBe(original);
    });

    it('should roundtrip an empty string', () => {
      expect(base64urlDecode(base64urlEncode(''))).toBe('');
    });

    it('should roundtrip unicode text', () => {
      const original = 'Ünïcödé 🎉';
      expect(base64urlDecode(base64urlEncode(original))).toBe(original);
    });

    it('should roundtrip JSON', () => {
      const json = JSON.stringify({ key: 'value', num: 42 });
      expect(base64urlDecode(base64urlEncode(json))).toBe(json);
    });

    it('should produce base64url-safe output (no +, /, or =)', () => {
      // Use data that would produce +, /, = in standard base64
      const data = '\xff\xfe\xfd\xfc\xfb\xfa';
      const encoded = base64urlEncode(data);
      expect(encoded).not.toMatch(/[+/=]/);
    });

    it('should encode Uint8Array input', () => {
      const bytes = new Uint8Array([72, 101, 108, 108, 111]);
      const encoded = base64urlEncode(bytes);
      expect(base64urlDecode(encoded)).toBe('Hello');
    });
  });

  describe('generateKeyPair', () => {
    it('should generate an ES256 key pair', async () => {
      const kp = await generateKeyPair('ES256');
      expect(kp.algorithm).toBe('ES256');
      expect(kp.type).toBe('ES256VerificationKey');
      expect(kp.id).toMatch(/^urn:uuid:/);
      expect(kp.publicKey).toContain('BEGIN PUBLIC KEY');
      expect(kp.privateKey).toContain('BEGIN PRIVATE KEY');
    });

    it('should generate an EdDSA key pair', async () => {
      const kp = await generateKeyPair('EdDSA');
      expect(kp.algorithm).toBe('EdDSA');
      expect(kp.publicKey).toContain('BEGIN PUBLIC KEY');
      expect(kp.privateKey).toContain('BEGIN PRIVATE KEY');
    });

    it('should generate unique key pairs', async () => {
      const kp1 = await generateKeyPair('ES256');
      const kp2 = await generateKeyPair('ES256');
      expect(kp1.id).not.toBe(kp2.id);
      expect(kp1.publicKey).not.toBe(kp2.publicKey);
    });

    it('should generate an ES384 key pair', async () => {
      const kp = await generateKeyPair('ES384');
      expect(kp.algorithm).toBe('ES384');
      expect(kp.publicKey).toContain('BEGIN PUBLIC KEY');
    });
  });
});
