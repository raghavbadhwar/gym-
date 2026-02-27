/**
 * @credverse/wallet-sdk
 * Credential wallet SDK: storage, key management, selective disclosure presentation
 */

// Types
export type {
  WalletCredentialRecord,
  WalletStore,
  CredentialFilter,
  PresentationRequest,
  PresentationResult,
  KeyRecord,
  WalletConfig,
} from './types.js';

// Credential store
export { createInMemoryStore } from './store.js';

// Presentation
export {
  createSelectivePresentation,
  prepareSdJwtPresentation,
  matchCredentialsToRequest,
} from './presentation.js';

// Key management
export type { KeyManager } from './key-manager.js';
export { createKeyManager } from './key-manager.js';
