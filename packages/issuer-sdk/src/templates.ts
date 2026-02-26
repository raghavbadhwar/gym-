/**
 * @credverse/issuer-sdk — Credential templates
 *
 * Provides factory functions for creating credential templates and
 * validating subject data against template definitions.
 */

import crypto from 'node:crypto';
import type { VCFormat } from '@credverse/trust-core';
import type { CredentialTemplate, TemplateField } from './types.js';

/**
 * Create a credential template defining the structure of a credential type.
 */
export function createTemplate(params: {
  name: string;
  description?: string;
  types?: string[];
  fields: TemplateField[];
  format?: VCFormat;
}): CredentialTemplate {
  return {
    id: `urn:uuid:${crypto.randomUUID()}`,
    name: params.name,
    description: params.description ?? '',
    types: params.types ?? ['VerifiableCredential'],
    subjectFields: params.fields,
    format: params.format ?? 'jwt-vc',
  };
}

/**
 * Validate credential subject data against a template.
 * Checks that required fields exist and that field types match.
 */
export function validateSubjectAgainstTemplate(
  template: CredentialTemplate,
  subject: Record<string, unknown>,
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  for (const field of template.subjectFields) {
    const value = subject[field.name];

    if (field.required && (value === undefined || value === null)) {
      errors.push(`Missing required field: ${field.name}`);
      continue;
    }

    if (value === undefined || value === null) {
      continue;
    }

    const actualType = typeof value;

    switch (field.type) {
      case 'string':
        if (actualType !== 'string') {
          errors.push(`Field "${field.name}" must be a string, got ${actualType}`);
        }
        break;
      case 'number':
        if (actualType !== 'number') {
          errors.push(`Field "${field.name}" must be a number, got ${actualType}`);
        }
        break;
      case 'boolean':
        if (actualType !== 'boolean') {
          errors.push(`Field "${field.name}" must be a boolean, got ${actualType}`);
        }
        break;
      case 'date':
        if (actualType !== 'string' || isNaN(Date.parse(value as string))) {
          errors.push(`Field "${field.name}" must be a valid date string`);
        }
        break;
    }
  }

  return { valid: errors.length === 0, errors };
}

// ── Built-in template factories ─────────────────────────────────────────────

/** University degree credential template */
export function universityDegreeTemplate(): CredentialTemplate {
  return createTemplate({
    name: 'UniversityDegree',
    description: 'A credential representing a university degree',
    types: ['VerifiableCredential', 'UniversityDegreeCredential'],
    fields: [
      { name: 'degree', type: 'string', required: true, description: 'Degree name' },
      { name: 'university', type: 'string', required: true, description: 'Issuing university' },
      { name: 'graduationDate', type: 'date', required: true, description: 'Date of graduation' },
      { name: 'gpa', type: 'number', required: false, description: 'Grade point average' },
    ],
  });
}

/** Employment credential template */
export function employmentCredentialTemplate(): CredentialTemplate {
  return createTemplate({
    name: 'EmploymentCredential',
    description: 'A credential representing employment history',
    types: ['VerifiableCredential', 'EmploymentCredential'],
    fields: [
      { name: 'employer', type: 'string', required: true, description: 'Employer name' },
      { name: 'jobTitle', type: 'string', required: true, description: 'Job title' },
      { name: 'startDate', type: 'date', required: true, description: 'Employment start date' },
      { name: 'endDate', type: 'date', required: false, description: 'Employment end date' },
      { name: 'current', type: 'boolean', required: false, description: 'Currently employed' },
    ],
  });
}

/** Age verification credential template */
export function ageVerificationTemplate(): CredentialTemplate {
  return createTemplate({
    name: 'AgeVerification',
    description: 'A credential for verifying minimum age requirements',
    types: ['VerifiableCredential', 'AgeVerificationCredential'],
    fields: [
      { name: 'birthDate', type: 'date', required: true, description: 'Date of birth' },
      { name: 'ageOver', type: 'number', required: true, description: 'Minimum age threshold' },
      { name: 'verified', type: 'boolean', required: true, description: 'Age verification status' },
    ],
  });
}
