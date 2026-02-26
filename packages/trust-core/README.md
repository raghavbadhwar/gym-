# @credverse/trust-core

Foundational module for the **CredVerse Trust Layer** providing W3C-aligned types and utilities.

## Exports

| Module | Description |
|--------|-------------|
| **types** | W3C VC Data Model v2, DID Core, SD-JWT VC, and key management interfaces |
| **did** | DID creation (`did:key`, `did:web`) and resolution utilities |
| **vc** | Verifiable Credential / Presentation creation and structural validation |
| **sd-jwt** | SD-JWT VC selective disclosure encoding, decoding, and serialization |
| **crypto** | SHA-256, base64url, JSON canonicalization, salt generation, key pair generation |

## Usage

```typescript
import {
  createDidKey,
  createVerifiableCredential,
  validateCredentialStructure,
  generateKeyPair,
  sha256,
} from '@credverse/trust-core';

// Generate a key pair
const keyPair = await generateKeyPair('EdDSA');

// Create a DID
const did = createDidKey(new Uint8Array(32));

// Issue a credential
const vc = createVerifiableCredential({
  issuer: did,
  subject: { name: 'Alice', degree: 'BSc Computer Science' },
  types: ['UniversityDegreeCredential'],
});

// Validate structure
const result = validateCredentialStructure(vc);
console.log(result); // { valid: true, errors: [] }
```

## Development

```bash
npm install
npm test
```
