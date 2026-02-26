import { describe, it, expect } from 'vitest';
import {
  checkImageQuality,
  validateDateField,
  validateEmailField,
  validateNameField,
  validateMrzChecksum,
  createFieldValidator,
  detectTampering,
  createVerificationPipeline,
  createStubOcrEngine,
} from '../src/index.js';

// ── Quality Check ───────────────────────────────────────────────────────────

describe('checkImageQuality', () => {
  it('fails on empty buffer', () => {
    const result = checkImageQuality(Buffer.alloc(0));
    expect(result.passed).toBe(false);
    expect(result.issues).toHaveLength(1);
    expect(result.issues[0].severity).toBe('high');
  });

  it('fails on buffer below default min size', () => {
    const result = checkImageQuality(Buffer.alloc(100));
    expect(result.passed).toBe(false);
    expect(result.issues[0].type).toBe('low_resolution');
    expect(result.issues[0].severity).toBe('medium');
  });

  it('passes on sufficiently large buffer', () => {
    const result = checkImageQuality(Buffer.alloc(20_000));
    expect(result.passed).toBe(true);
    expect(result.issues).toHaveLength(0);
  });

  it('respects custom minResolution threshold', () => {
    const result = checkImageQuality(Buffer.alloc(500), { minResolution: 256 });
    expect(result.passed).toBe(true);
  });
});

// ── Field Validators ────────────────────────────────────────────────────────

describe('validateDateField', () => {
  it('accepts valid ISO 8601 date', () => {
    const r = validateDateField('2024-01-15', 'dob');
    expect(r.valid).toBe(true);
    expect(r.errors).toHaveLength(0);
  });

  it('rejects empty string', () => {
    const r = validateDateField('', 'dob');
    expect(r.valid).toBe(false);
  });

  it('rejects garbage string', () => {
    const r = validateDateField('not-a-date', 'dob');
    expect(r.valid).toBe(false);
    expect(r.errors[0]).toContain('not a valid ISO 8601');
  });
});

describe('validateEmailField', () => {
  it('accepts valid email', () => {
    expect(validateEmailField('user@example.com', 'email').valid).toBe(true);
  });

  it('rejects empty string', () => {
    expect(validateEmailField('', 'email').valid).toBe(false);
  });

  it('rejects string without @', () => {
    expect(validateEmailField('not-an-email', 'email').valid).toBe(false);
  });
});

describe('validateNameField', () => {
  it('accepts alphabetic name', () => {
    expect(validateNameField('John Doe', 'name').valid).toBe(true);
  });

  it('rejects empty string', () => {
    expect(validateNameField('', 'name').valid).toBe(false);
  });

  it('rejects purely numeric string', () => {
    const r = validateNameField('12345', 'name');
    expect(r.valid).toBe(false);
    expect(r.errors[0]).toContain('purely numeric');
  });
});

describe('validateMrzChecksum', () => {
  it('rejects string shorter than 2 characters', () => {
    const r = validateMrzChecksum('A', 'mrz');
    expect(r.valid).toBe(false);
    expect(r.errors[0]).toContain('too short');
  });

  it('validates a correct MRZ check digit', () => {
    // "AB" => A=10, weights[0]=7 => 10*7=70, sum=70, 70%10=0, expected digit='0'
    // so "AB0" should fail because last char is check digit
    // Let's compute: data="AB", expected='0'
    // A(10)*7 + B(11)*3 = 70+33=103, 103%10=3, expected='3'
    const r = validateMrzChecksum('AB3', 'mrz');
    expect(r.valid).toBe(true);
  });

  it('rejects incorrect MRZ check digit', () => {
    const r = validateMrzChecksum('AB0', 'mrz');
    expect(r.valid).toBe(false);
    expect(r.errors[0]).toContain('check digit mismatch');
  });

  it('rejects invalid MRZ characters', () => {
    const r = validateMrzChecksum('a!0', 'mrz');
    expect(r.valid).toBe(false);
    expect(r.errors[0]).toContain('invalid MRZ character');
  });
});

describe('createFieldValidator', () => {
  it('creates a validator that matches a pattern', () => {
    const v = createFieldValidator(/^\d{3}$/, 'must be 3 digits');
    expect(v('123', 'code').valid).toBe(true);
    expect(v('12', 'code').valid).toBe(false);
    expect(v('12', 'code').errors[0]).toContain('must be 3 digits');
  });
});

// ── Tamper Detection ────────────────────────────────────────────────────────

describe('detectTampering', () => {
  it('returns clean result for high-confidence fields', () => {
    const r = detectTampering({
      text: 'Some reasonably long text here for testing',
      confidence: 0.95,
      fields: [
        { name: 'f1', value: 'v1', confidence: 0.9 },
        { name: 'f2', value: 'v2', confidence: 0.88 },
      ],
    });
    expect(r.suspicious).toBe(false);
    expect(r.riskScore).toBe(0);
    expect(r.indicators).toHaveLength(0);
  });

  it('flags low-confidence fields', () => {
    const r = detectTampering({
      text: 'Some reasonably long text here for testing',
      confidence: 0.5,
      fields: [{ name: 'name', value: 'x', confidence: 0.1 }],
    });
    expect(r.indicators.some((i) => i.type === 'editing_trace')).toBe(true);
  });

  it('flags high confidence variance', () => {
    // Population variance threshold is 0.3; max variance for [0,1] values is 0.25,
    // so we use out-of-range confidence to exercise the variance logic.
    const r = detectTampering({
      text: 'Some reasonably long text here for testing',
      confidence: 0.5,
      fields: [
        { name: 'a', value: 'v', confidence: 0.5 },
        { name: 'b', value: 'v', confidence: 1.8 },
      ],
    });
    expect(r.indicators.some((i) => i.type === 'font_inconsistency')).toBe(true);
  });

  it('flags minimal text', () => {
    const r = detectTampering({
      text: 'short',
      confidence: 0.9,
      fields: [],
    });
    expect(r.indicators.some((i) => i.type === 'compression_artifact')).toBe(true);
  });

  it('flags image editing software in metadata', () => {
    const r = detectTampering(
      { text: 'Some reasonably long text here', confidence: 0.9, fields: [] },
      { software: 'Adobe Photoshop' },
    );
    expect(r.indicators.some((i) => i.type === 'metadata_mismatch')).toBe(true);
  });
});

// ── Pipeline ────────────────────────────────────────────────────────────────

describe('createVerificationPipeline', () => {
  it('runs full pipeline with stub engine and returns expected shape', async () => {
    const pipeline = createVerificationPipeline({
      ocrEngine: createStubOcrEngine(),
    });

    const result = await pipeline.verify(Buffer.alloc(20_000), 'passport');

    expect(result.documentType).toBe('passport');
    expect(result.ocrResult.fields.length).toBeGreaterThan(0);
    expect(result.qualityCheck.passed).toBe(true);
    expect(result.evidenceHash).toMatch(/^[0-9a-f]{64}$/);
    expect(typeof result.overallRiskScore).toBe('number');
    expect(typeof result.confidence).toBe('number');
    expect(typeof result.requiresHumanReview).toBe('boolean');
  });

  it('applies field validators when configured', async () => {
    const pipeline = createVerificationPipeline({
      ocrEngine: createStubOcrEngine(),
      fieldValidators: {
        date_of_birth: validateDateField,
        expiry_date: validateDateField,
      },
    });

    const result = await pipeline.verify(Buffer.alloc(20_000), 'passport');
    expect(result.fieldValidations.length).toBe(2);
    expect(result.fieldValidations.every((v) => v.valid)).toBe(true);
  });

  it('detects quality issues on small images', async () => {
    const pipeline = createVerificationPipeline({
      ocrEngine: createStubOcrEngine(),
    });

    const result = await pipeline.verify(Buffer.alloc(100), 'generic');
    expect(result.qualityCheck.passed).toBe(false);
    expect(result.overallRiskScore).toBeGreaterThan(0);
  });

  it('skips tamper detection when disabled', async () => {
    const pipeline = createVerificationPipeline({
      ocrEngine: createStubOcrEngine(),
      tamperDetectionEnabled: false,
    });

    const result = await pipeline.verify(Buffer.alloc(20_000), 'degree');
    expect(result.tamperDetection.suspicious).toBe(false);
    expect(result.tamperDetection.riskScore).toBe(0);
  });

  it('produces deterministic evidence hash for same input', async () => {
    // Use a custom stub that returns fixed confidence to avoid randomness
    const fixedEngine = {
      name: 'fixed',
      supportedFormats: ['image/png'],
      async extract() {
        return {
          text: 'name: John',
          confidence: 0.9,
          fields: [{ name: 'name', value: 'John', confidence: 0.9 }],
        };
      },
    };

    const pipeline = createVerificationPipeline({ ocrEngine: fixedEngine });
    const a = await pipeline.verify(Buffer.alloc(20_000), 'generic');
    const b = await pipeline.verify(Buffer.alloc(20_000), 'generic');
    expect(a.evidenceHash).toBe(b.evidenceHash);
  });
});
