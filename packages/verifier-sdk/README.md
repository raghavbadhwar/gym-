# @credverse/verifier-sdk

OpenID4VP verification flows, OPA-style policy engine, and signed verification receipts for the CredVerse ecosystem.

## Features

- **OpenID4VP Presentation Exchange** — Create authorization requests, validate responses, and build presentation definitions
- **Policy Engine** — Evaluate OPA-style policy rules against credential data with dot-notation field resolution
- **Verification Receipts** — Create, serialize, and validate signed verification receipts

## Installation

```bash
npm install @credverse/verifier-sdk
```

## Usage

### OpenID4VP Flow

```typescript
import {
  createPresentationDefinition,
  createAuthorizationRequest,
  validateAuthorizationResponse,
} from '@credverse/verifier-sdk';

// Build a presentation definition
const definition = createPresentationDefinition({
  descriptors: [
    {
      id: 'kyc-credential',
      name: 'KYC Verification',
      purpose: 'Verify identity',
      fields: [{ path: ['$.credentialSubject.kycVerified'] }],
    },
  ],
});

// Create an authorization request
const request = createAuthorizationRequest({
  clientId: 'did:web:verifier.example.com',
  redirectUri: 'https://verifier.example.com/callback',
  presentationDefinition: definition,
});

// Validate the response
const { valid, errors } = validateAuthorizationResponse(response, request.state, request.nonce);
```

### Policy Engine

```typescript
import {
  evaluatePolicies,
  ageCheckPolicy,
  kycCredentialPolicy,
  createPolicyRule,
} from '@credverse/verifier-sdk';

const policies = [
  ageCheckPolicy(18),
  kycCredentialPolicy(),
  createPolicyRule({
    name: 'Country Check',
    field: 'credentialSubject.country',
    operator: 'in',
    value: ['US', 'CA', 'GB'],
  }),
];

const data = {
  credentialSubject: { age: 25, kycVerified: true, country: 'US' },
};

const { results, allPassed, decision } = evaluatePolicies(policies, data);
// decision: 'approved'
```

### Verification Receipts

```typescript
import {
  createVerificationReceipt,
  serializeReceipt,
  validateReceipt,
} from '@credverse/verifier-sdk';

const receipt = createVerificationReceipt({
  verifierId: 'did:web:verifier.example.com',
  subjectDid: 'did:key:z6Mkf...',
  policiesApplied: ['age-check', 'kyc-check'],
  decision: 'approved',
  evidenceHashes: ['sha256-abc123'],
});

const json = serializeReceipt(receipt);
const { valid, errors } = validateReceipt(receipt);
```

## API Reference

### OpenID4VP

| Function | Description |
|---|---|
| `createAuthorizationRequest()` | Creates a VP authorization request with generated nonce |
| `validateAuthorizationResponse()` | Validates the response structure |
| `createPresentationDefinition()` | Helper to build presentation definitions |

### Policy Engine

| Function | Description |
|---|---|
| `evaluatePolicy()` | Evaluates a single policy rule against data |
| `evaluatePolicies()` | Evaluates multiple policies with aggregate decision |
| `createPolicyRule()` | Factory function for policy rules |
| `resolveFieldValue()` | Resolves dot-notation paths in nested objects |
| `ageCheckPolicy()` | Sample: minimum age check |
| `kycCredentialPolicy()` | Sample: KYC credential required |
| `employerCredentialPolicy()` | Sample: employer credential check |

### Verification Receipts

| Function | Description |
|---|---|
| `createVerificationReceipt()` | Creates a receipt with timestamp and UUID |
| `serializeReceipt()` | Canonical JSON serialization |
| `validateReceipt()` | Validates receipt structure |
