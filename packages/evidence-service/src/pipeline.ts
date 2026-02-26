/**
 * @credverse/evidence-service — Verification pipeline orchestrator
 *
 * Wires together quality checks, OCR extraction, field validation,
 * tamper detection, risk scoring, and evidence hashing into a single
 * async pipeline.
 */

import { createHash } from 'node:crypto';

import type {
  DocumentType,
  EvidencePipelineConfig,
  FieldValidationResult,
  OcrEngine,
  OcrResult,
  QualityCheckResult,
  TamperDetectionResult,
  VerificationPipelineResult,
} from './types.js';
import { checkImageQuality } from './quality-check.js';
import { detectTampering } from './tamper-detection.js';

const DEFAULT_HUMAN_REVIEW_THRESHOLD = 0.7;

// ── Pipeline factory ────────────────────────────────────────────────────────

/**
 * Create a configured verification pipeline.
 *
 * The returned `verify` function runs the full sequence:
 *  1. Quality check
 *  2. OCR extraction
 *  3. Field validation (if validators configured)
 *  4. Tamper detection (if enabled)
 *  5. Weighted risk score computation
 *  6. Human review flagging
 *  7. SHA-256 evidence hash
 */
export function createVerificationPipeline(config: EvidencePipelineConfig) {
  const {
    ocrEngine,
    qualityThresholds,
    tamperDetectionEnabled = true,
    humanReviewThreshold = DEFAULT_HUMAN_REVIEW_THRESHOLD,
    fieldValidators = {},
  } = config;

  async function verify(
    imageData: Buffer | Uint8Array,
    documentType: DocumentType = 'generic',
  ): Promise<VerificationPipelineResult> {
    // 1. Quality check
    const qualityCheck: QualityCheckResult = checkImageQuality(
      imageData,
      qualityThresholds,
    );

    // 2. OCR extraction
    const ocrResult: OcrResult = await ocrEngine.extract(imageData, {
      documentType,
    });

    // 3. Field validation
    const fieldValidations: FieldValidationResult[] = [];
    for (const field of ocrResult.fields) {
      const validator = fieldValidators[field.name];
      if (validator) {
        fieldValidations.push(validator(field.value, field.name));
      }
    }

    // 4. Tamper detection
    let tamperDetection: TamperDetectionResult;
    if (tamperDetectionEnabled) {
      tamperDetection = detectTampering(ocrResult);
    } else {
      tamperDetection = { suspicious: false, indicators: [], riskScore: 0 };
    }

    // 5. Weighted risk score (quality 30%, field validation 30%, tamper 40%)
    const qualityScore = qualityCheck.passed ? 0 : 50;
    const fieldScore =
      fieldValidations.length > 0
        ? (fieldValidations.filter((v) => !v.valid).length /
            fieldValidations.length) *
          100
        : 0;
    const tamperScore = tamperDetection.riskScore;

    const overallRiskScore = Math.round(
      qualityScore * 0.3 + fieldScore * 0.3 + tamperScore * 0.4,
    );

    // 6. Confidence & human review
    const confidence = Math.max(0, 1 - overallRiskScore / 100);
    const requiresHumanReview = confidence < humanReviewThreshold;

    // 7. Evidence hash (SHA-256 of canonical pipeline result)
    const canonical = JSON.stringify({
      documentType,
      ocrText: ocrResult.text,
      ocrConfidence: ocrResult.confidence,
      fields: ocrResult.fields.map((f) => ({
        name: f.name,
        value: f.value,
      })),
      qualityPassed: qualityCheck.passed,
      overallRiskScore,
    });
    const evidenceHash = createHash('sha256').update(canonical).digest('hex');

    return {
      documentType,
      ocrResult,
      qualityCheck,
      fieldValidations,
      tamperDetection,
      overallRiskScore,
      confidence,
      requiresHumanReview,
      evidenceHash,
    };
  }

  return { verify };
}

// ── Stub OCR engine for testing / development ───────────────────────────────

const STUB_FIELDS: Record<string, { name: string; value: string }[]> = {
  passport: [
    { name: 'surname', value: 'DOE' },
    { name: 'given_names', value: 'JOHN' },
    { name: 'nationality', value: 'USA' },
    { name: 'date_of_birth', value: '1990-01-15' },
    { name: 'passport_number', value: 'X12345678' },
    { name: 'expiry_date', value: '2030-01-15' },
  ],
  drivers_license: [
    { name: 'full_name', value: 'JOHN DOE' },
    { name: 'date_of_birth', value: '1990-01-15' },
    { name: 'license_number', value: 'D1234567' },
    { name: 'expiry_date', value: '2028-06-30' },
    { name: 'state', value: 'CA' },
  ],
  degree: [
    { name: 'recipient', value: 'John Doe' },
    { name: 'institution', value: 'State University' },
    { name: 'degree', value: 'Bachelor of Science' },
    { name: 'date_conferred', value: '2022-05-20' },
  ],
  transcript: [
    { name: 'student_name', value: 'John Doe' },
    { name: 'institution', value: 'State University' },
    { name: 'gpa', value: '3.75' },
    { name: 'graduation_date', value: '2022-05-20' },
  ],
  employment_letter: [
    { name: 'employee_name', value: 'John Doe' },
    { name: 'employer', value: 'Acme Corp' },
    { name: 'position', value: 'Software Engineer' },
    { name: 'start_date', value: '2022-08-01' },
  ],
};

/** Create a stub OCR engine that returns mock data keyed by document type. */
export function createStubOcrEngine(): OcrEngine {
  return {
    name: 'stub',
    supportedFormats: ['image/png', 'image/jpeg', 'application/pdf'],

    async extract(imageData, options) {
      const docType = options?.documentType ?? 'generic';
      const fieldDefs = STUB_FIELDS[docType] ?? [
        { name: 'text_block', value: 'Sample extracted text' },
      ];

      const fields = fieldDefs.map((f) => ({
        ...f,
        confidence: 0.85 + Math.random() * 0.1,
      }));

      const text = fields.map((f) => `${f.name}: ${f.value}`).join('\n');

      return {
        text,
        confidence: 0.88,
        fields,
        rawOutput: { engine: 'stub', imageSize: imageData.length },
      };
    },
  };
}
