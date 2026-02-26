/**
 * @credverse/verifier-sdk — OPA-style policy engine
 * Evaluates policy rules against credential data using dot-notation field resolution.
 */

import type {
  PolicyCondition,
  PolicyEvaluationResult,
  PolicyOperator,
  PolicyRule,
  VerificationDecision,
} from './types.js';

/** Resolves a dot-notation field path against a nested data object. */
export function resolveFieldValue(
  data: Record<string, unknown>,
  fieldPath: string,
): unknown {
  const segments = fieldPath.split('.');
  let current: unknown = data;

  for (const segment of segments) {
    if (current === null || current === undefined) return undefined;
    if (typeof current !== 'object') return undefined;
    current = (current as Record<string, unknown>)[segment];
  }

  return current;
}

/** Evaluates a single policy rule against the provided data. */
export function evaluatePolicy(
  rule: PolicyRule,
  data: Record<string, unknown>,
): PolicyEvaluationResult {
  const { condition } = rule;
  const fieldValue = resolveFieldValue(data, condition.field);

  const result = applyOperator(condition.operator, fieldValue, condition.value);

  return {
    policyId: rule.id,
    passed: result.passed,
    ...(result.reason !== undefined && { reason: result.reason }),
  };
}

/** Evaluates multiple policy rules and produces an aggregate decision. */
export function evaluatePolicies(
  rules: PolicyRule[],
  data: Record<string, unknown>,
): { results: PolicyEvaluationResult[]; allPassed: boolean; decision: VerificationDecision } {
  const results = rules.map((rule) => evaluatePolicy(rule, data));
  const allPassed = results.every((r) => r.passed);

  let decision: VerificationDecision;
  if (allPassed) {
    decision = 'approved';
  } else {
    const failedCount = results.filter((r) => !r.passed).length;
    decision = failedCount > results.length / 2 ? 'denied' : 'review_required';
  }

  return { results, allPassed, decision };
}

/** Factory function to create a policy rule. */
export function createPolicyRule(params: {
  id?: string;
  name: string;
  description?: string;
  field: string;
  operator: PolicyOperator;
  value: unknown;
}): PolicyRule {
  return {
    id: params.id ?? crypto.randomUUID(),
    name: params.name,
    description: params.description ?? '',
    condition: {
      field: params.field,
      operator: params.operator,
      value: params.value,
    },
  };
}

// ── Sample policy factories ─────────────────────────────────────────────────

/** Creates a policy that checks a subject meets a minimum age. Uses `greater_than` with `minimumAge - 1` since no `>=` operator exists. */
export function ageCheckPolicy(minimumAge: number): PolicyRule {
  return createPolicyRule({
    name: 'Minimum Age Check',
    description: `Subject must be at least ${minimumAge} years old`,
    field: 'credentialSubject.age',
    operator: 'greater_than',
    value: minimumAge - 1,
  });
}

/** Creates a policy that verifies a KYC credential type exists. */
export function kycCredentialPolicy(): PolicyRule {
  return createPolicyRule({
    name: 'KYC Credential Required',
    description: 'A KYC-verified credential type must be present',
    field: 'credentialSubject.kycVerified',
    operator: 'equals',
    value: true,
  });
}

/** Creates a policy that verifies the credential is from a required employer. */
export function employerCredentialPolicy(requiredEmployer: string): PolicyRule {
  return createPolicyRule({
    name: 'Employer Credential Check',
    description: `Credential must be issued by ${requiredEmployer}`,
    field: 'credentialSubject.employer',
    operator: 'equals',
    value: requiredEmployer,
  });
}

// ── Internal helpers ────────────────────────────────────────────────────────

function applyOperator(
  operator: PolicyCondition['operator'],
  fieldValue: unknown,
  expected: unknown,
): { passed: boolean; reason?: string } {
  switch (operator) {
    case 'equals':
      return fieldValue === expected
        ? { passed: true }
        : { passed: false, reason: `Expected ${String(expected)}, got ${String(fieldValue)}` };

    case 'not_equals':
      return fieldValue !== expected
        ? { passed: true }
        : { passed: false, reason: `Expected value to differ from ${String(expected)}` };

    case 'greater_than':
      return typeof fieldValue === 'number' && typeof expected === 'number' && fieldValue > expected
        ? { passed: true }
        : { passed: false, reason: `Expected > ${String(expected)}, got ${String(fieldValue)}` };

    case 'less_than':
      return typeof fieldValue === 'number' && typeof expected === 'number' && fieldValue < expected
        ? { passed: true }
        : { passed: false, reason: `Expected < ${String(expected)}, got ${String(fieldValue)}` };

    case 'contains':
      if (typeof fieldValue === 'string' && typeof expected === 'string') {
        return fieldValue.includes(expected)
          ? { passed: true }
          : { passed: false, reason: `"${fieldValue}" does not contain "${expected}"` };
      }
      if (Array.isArray(fieldValue)) {
        return fieldValue.includes(expected)
          ? { passed: true }
          : { passed: false, reason: `Array does not include ${String(expected)}` };
      }
      return { passed: false, reason: `Field is not a string or array` };

    case 'exists':
      return fieldValue !== undefined && fieldValue !== null
        ? { passed: true }
        : { passed: false, reason: `Field does not exist` };

    case 'in':
      return Array.isArray(expected) && expected.includes(fieldValue)
        ? { passed: true }
        : { passed: false, reason: `${String(fieldValue)} is not in allowed set` };

    default:
      return { passed: false, reason: `Unknown operator: ${String(operator)}` };
  }
}
