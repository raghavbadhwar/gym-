# @credverse/issuer-sdk

OpenID4VCI issuance flows, credential templates, and status management for the CredVerse ecosystem.

## Features

- **OpenID4VCI flows** — Issuer metadata, credential offers, token handling, and request/response processing
- **Credential templates** — Define and validate credential structures with built-in templates for common credential types
- **Status list management** — Track credential revocation and suspension using compact bitstring encoding

## Installation

```bash
npm install @credverse/issuer-sdk
```

## Usage

### OpenID4VCI Issuance

```typescript
import {
  createIssuerMetadata,
  createCredentialOffer,
  createTokenResponse,
  validateCredentialRequest,
  createCredentialResponse,
} from '@credverse/issuer-sdk';

// Define issuer metadata
const metadata = createIssuerMetadata({
  issuerUrl: 'https://issuer.example.com',
  configurations: {
    UniversityDegree: {
      format: 'jwt-vc',
      types: ['VerifiableCredential', 'UniversityDegreeCredential'],
      cryptographicBindingMethodsSupported: ['did:key'],
      credentialSigningAlgValuesSupported: ['ES256'],
    },
  },
});

// Create a credential offer
const offer = createCredentialOffer({
  issuerUrl: 'https://issuer.example.com',
  configurationIds: ['UniversityDegree'],
  preAuthorizedCode: 'abc123',
});

// Generate a token response
const tokenResponse = createTokenResponse({ expiresIn: 3600 });

// Validate an incoming credential request
const { valid, errors } = validateCredentialRequest(
  { format: 'jwt-vc', types: ['VerifiableCredential'] },
  ['jwt-vc', 'sd-jwt-vc'],
);

// Create a credential response
const response = createCredentialResponse({
  format: 'jwt-vc',
  credential: 'eyJhbGciOi...',
});
```

### Credential Templates

```typescript
import {
  universityDegreeTemplate,
  employmentCredentialTemplate,
  validateSubjectAgainstTemplate,
  createTemplate,
} from '@credverse/issuer-sdk';

// Use a built-in template
const template = universityDegreeTemplate();

// Validate subject data against a template
const { valid, errors } = validateSubjectAgainstTemplate(template, {
  degree: 'Bachelor of Science',
  university: 'MIT',
  graduationDate: '2024-06-15',
});

// Create a custom template
const customTemplate = createTemplate({
  name: 'ProfessionalCertification',
  description: 'Professional certification credential',
  types: ['VerifiableCredential', 'ProfessionalCertification'],
  fields: [
    { name: 'certName', type: 'string', required: true },
    { name: 'issuedDate', type: 'date', required: true },
    { name: 'expiryDate', type: 'date', required: false },
  ],
});
```

### Status List Management

```typescript
import {
  createStatusList,
  addStatusEntry,
  revokeCredential,
  getCredentialStatus,
} from '@credverse/issuer-sdk';

// Create a status list
let statusList = createStatusList({
  issuer: 'did:web:issuer.example.com',
  purpose: 'revocation',
});

// Add credentials to the list
statusList = addStatusEntry(statusList, 'credential-1');
statusList = addStatusEntry(statusList, 'credential-2');

// Revoke a credential
statusList = revokeCredential(statusList, 'credential-1');

// Check credential status
const status = getCredentialStatus(statusList, 'credential-1');
// { credentialId: 'credential-1', index: 0, status: 'revoked', updatedAt: '...' }
```

## API Reference

### OpenID4VCI

| Function | Description |
|---|---|
| `createIssuerMetadata(params)` | Create issuer metadata |
| `createCredentialOffer(params)` | Create a credential offer |
| `createTokenResponse(params)` | Generate a token response with c_nonce |
| `validateCredentialRequest(request, formats)` | Validate a credential request |
| `createCredentialResponse(params)` | Wrap a credential in a response |

### Templates

| Function | Description |
|---|---|
| `createTemplate(params)` | Create a custom credential template |
| `validateSubjectAgainstTemplate(template, subject)` | Validate subject data against a template |
| `universityDegreeTemplate()` | Built-in university degree template |
| `employmentCredentialTemplate()` | Built-in employment credential template |
| `ageVerificationTemplate()` | Built-in age verification template |

### Status List

| Function | Description |
|---|---|
| `createStatusList(params)` | Create a new status list |
| `addStatusEntry(list, credentialId)` | Add a credential to the list |
| `revokeCredential(list, credentialId)` | Mark a credential as revoked |
| `suspendCredential(list, credentialId)` | Mark a credential as suspended |
| `getCredentialStatus(list, credentialId)` | Look up credential status |
| `encodeStatusList(list)` | Encode the list as a base64url bitstring |
