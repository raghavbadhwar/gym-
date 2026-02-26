/**
 * @credverse/trust-core — SD-JWT VC selective disclosure utilities
 */

import type { SdJwtDisclosure, SdJwtVc } from './types.js';
import { base64urlEncode, base64urlDecode } from './crypto.js';

/**
 * Create a disclosure triple from its components.
 */
export function createDisclosure(
  salt: string,
  claimName: string,
  claimValue: unknown,
): SdJwtDisclosure {
  return { salt, claimName, claimValue };
}

/**
 * Base64url-encode a disclosure triple as a JSON array `[salt, claimName, claimValue]`.
 */
export function encodeDisclosure(disclosure: SdJwtDisclosure): string {
  const json = JSON.stringify([
    disclosure.salt,
    disclosure.claimName,
    disclosure.claimValue,
  ]);
  return base64urlEncode(json);
}

/**
 * Decode a base64url-encoded disclosure back into its components.
 */
export function decodeDisclosure(encoded: string): SdJwtDisclosure {
  const json = base64urlDecode(encoded);
  const arr = JSON.parse(json) as [string, string, unknown];
  return { salt: arr[0], claimName: arr[1], claimValue: arr[2] };
}

/**
 * Filter disclosures to only those whose claimName is in the selected set.
 */
export function selectDisclosures(
  allDisclosures: SdJwtDisclosure[],
  selectedClaims: string[],
): SdJwtDisclosure[] {
  const selected = new Set(selectedClaims);
  return allDisclosures.filter((d) => selected.has(d.claimName));
}

/**
 * Create an SD-JWT VC envelope from its parts.
 */
export function createSdJwtVc(
  jwt: string,
  disclosures: SdJwtDisclosure[],
  keyBindingJwt?: string,
): SdJwtVc {
  return { jwt, disclosures, keyBindingJwt };
}

/**
 * Parse a compact SD-JWT serialization: `jwt~disclosure1~disclosure2~[kb]`
 *
 * The trailing `~` after the last disclosure separates the optional key-binding JWT.
 * If the serialization ends with `~`, there is no key-binding JWT.
 */
export function parseSdJwtVc(serialized: string): SdJwtVc {
  const parts = serialized.split('~');
  const jwt = parts[0];

  // Last element may be the key-binding JWT (or empty string if trailing ~)
  const lastPart = parts[parts.length - 1];
  const hasKeyBinding = parts.length > 1 && lastPart !== '';

  const disclosureParts = hasKeyBinding ? parts.slice(1, -1) : parts.slice(1);
  // Filter out empty strings (e.g. from trailing ~)
  const disclosures = disclosureParts
    .filter((p) => p.length > 0)
    .map((encoded) => decodeDisclosure(encoded));

  return {
    jwt,
    disclosures,
    keyBindingJwt: hasKeyBinding ? lastPart : undefined,
  };
}

/**
 * Serialize an SD-JWT VC to compact format: `jwt~disclosure1~disclosure2~[kb]`
 */
export function serializeSdJwtVc(sdJwt: SdJwtVc): string {
  const encodedDisclosures = sdJwt.disclosures.map(encodeDisclosure);
  const parts = [sdJwt.jwt, ...encodedDisclosures];
  const base = parts.join('~');
  return sdJwt.keyBindingJwt ? `${base}~${sdJwt.keyBindingJwt}` : `${base}~`;
}
