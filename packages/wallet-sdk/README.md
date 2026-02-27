# @credverse/wallet-sdk

Credential wallet SDK for the CredVerse ecosystem. Provides credential storage, key management, and selective disclosure presentation.

## Installation

```bash
npm install @credverse/wallet-sdk
```

## Usage

### Credential Store

```ts
import { createInMemoryStore } from '@credverse/wallet-sdk';

const store = createInMemoryStore();

store.save({
  id: 'cred-1',
  credential: myCredential,
  format: 'ldp-vc',
  issuedAt: new Date().toISOString(),
  issuerDid: 'did:web:example.com',
  tags: ['education'],
  metadata: {},
});

const results = store.query({ issuer: 'did:web:example.com', tag: 'education' });
```

### Selective Disclosure Presentation

```ts
import { createSelectivePresentation } from '@credverse/wallet-sdk';

const result = createSelectivePresentation({
  holder: 'did:key:z6Mk...',
  credential: storedCredential,
  disclosedClaims: ['name', 'degree'],
});
// result.presentation contains a VP with only name and degree in credentialSubject
```

### SD-JWT Presentation

```ts
import { prepareSdJwtPresentation } from '@credverse/wallet-sdk';

const result = prepareSdJwtPresentation({
  holder: 'did:key:z6Mk...',
  sdJwtVc: mySdJwt,
  selectedClaims: ['email'],
});
// result.sdJwtVc contains only the selected disclosures
```

### Key Management

```ts
import { createKeyManager } from '@credverse/wallet-sdk';

const km = createKeyManager();
const key = await km.generateKey('EdDSA');
console.log(key.did); // did:key:z6Mk...

const { newKey, oldKey } = await km.rotateKey(key.id, 'ES256');
```

## API

| Export | Description |
|--------|-------------|
| `createInMemoryStore()` | In-memory credential store implementing `WalletStore` |
| `createSelectivePresentation(params)` | Create a VP with only disclosed claims |
| `prepareSdJwtPresentation(params)` | Create an SD-JWT VP with selected disclosures |
| `matchCredentialsToRequest(store, request)` | Find credentials matching a presentation request |
| `createKeyManager()` | In-memory key manager with generation & rotation |

## License

See repository root.
