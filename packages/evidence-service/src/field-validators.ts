/**
 * @credverse/evidence-service — Field-level validators
 *
 * Built-in validators for common credential fields plus a factory
 * for creating custom regex-based validators.
 */

import type { FieldValidationResult, FieldValidator } from './types.js';

// ── Built-in validators ─────────────────────────────────────────────────────

/** Validate an ISO 8601 date string (YYYY-MM-DD or full datetime). */
export function validateDateField(
  value: string,
  fieldName: string,
): FieldValidationResult {
  const errors: string[] = [];

  if (!value || value.trim().length === 0) {
    errors.push(`${fieldName} is empty`);
    return { fieldName, valid: false, errors };
  }

  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    errors.push(`${fieldName} is not a valid ISO 8601 date`);
  }

  return { fieldName, valid: errors.length === 0, errors };
}

/**
 * Validate a Machine Readable Zone check digit using the ICAO 9303 algorithm.
 *
 * Each character is assigned a numeric value (0-9 → 0-9, A-Z → 10-35,
 * '<' → 0) and multiplied by a cycling weight sequence [7, 3, 1].
 * The check digit is the weighted sum mod 10.
 *
 * The **last character** of `mrz` is treated as the expected check digit.
 */
export function validateMrzChecksum(
  mrz: string,
  fieldName: string,
): FieldValidationResult {
  const errors: string[] = [];

  if (mrz.length < 2) {
    errors.push(`${fieldName}: MRZ string is too short`);
    return { fieldName, valid: false, errors };
  }

  const data = mrz.slice(0, -1);
  const expectedDigit = mrz.slice(-1);
  const weights = [7, 3, 1];

  let sum = 0;
  for (let i = 0; i < data.length; i++) {
    const ch = data[i];
    let val: number;

    if (ch >= '0' && ch <= '9') {
      val = Number(ch);
    } else if (ch >= 'A' && ch <= 'Z') {
      val = ch.charCodeAt(0) - 'A'.charCodeAt(0) + 10;
    } else if (ch === '<') {
      val = 0;
    } else {
      errors.push(`${fieldName}: invalid MRZ character '${ch}'`);
      return { fieldName, valid: false, errors };
    }

    sum += val * weights[i % 3];
  }

  const computed = String(sum % 10);
  if (computed !== expectedDigit) {
    errors.push(
      `${fieldName}: check digit mismatch (expected ${computed}, got ${expectedDigit})`,
    );
  }

  return { fieldName, valid: errors.length === 0, errors };
}

/** Validate a basic email address format. */
export function validateEmailField(
  value: string,
  fieldName: string,
): FieldValidationResult {
  const errors: string[] = [];

  if (!value || value.trim().length === 0) {
    errors.push(`${fieldName} is empty`);
    return { fieldName, valid: false, errors };
  }

  // Intentionally simple — real-world validation should use a library
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRe.test(value)) {
    errors.push(`${fieldName} is not a valid email address`);
  }

  return { fieldName, valid: errors.length === 0, errors };
}

/** Validate that a name field is non-empty and not purely numeric. */
export function validateNameField(
  value: string,
  fieldName: string,
): FieldValidationResult {
  const errors: string[] = [];

  if (!value || value.trim().length === 0) {
    errors.push(`${fieldName} is empty`);
    return { fieldName, valid: false, errors };
  }

  if (/^\d+$/.test(value.trim())) {
    errors.push(`${fieldName} must not be purely numeric`);
  }

  return { fieldName, valid: errors.length === 0, errors };
}

// ── Factory ─────────────────────────────────────────────────────────────────

/** Create a reusable regex-based field validator. */
export function createFieldValidator(
  pattern: RegExp,
  errorMessage: string,
): FieldValidator {
  return (value: string, fieldName: string): FieldValidationResult => {
    const errors: string[] = [];

    if (!pattern.test(value)) {
      errors.push(`${fieldName}: ${errorMessage}`);
    }

    return { fieldName, valid: errors.length === 0, errors };
  };
}
