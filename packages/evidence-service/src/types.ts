/**
 * @credverse/evidence-service — Type definitions
 * Evidence analysis pipeline: OCR engines, document verification, risk scoring
 */

// ── Geometry ────────────────────────────────────────────────────────────────

/** Bounding box in pixel coordinates */
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** Region of interest within an image */
export interface ImageRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
}

// ── Document Types ──────────────────────────────────────────────────────────

/** Supported document types for evidence analysis */
export type DocumentType =
  | 'passport'
  | 'drivers_license'
  | 'national_id'
  | 'degree'
  | 'transcript'
  | 'employment_letter'
  | 'generic';

// ── OCR ─────────────────────────────────────────────────────────────────────

/** Options for OCR extraction */
export interface OcrOptions {
  language?: string;
  documentType?: DocumentType;
  regions?: ImageRegion[];
}

/** A single extracted field from OCR */
export interface ExtractedField {
  name: string;
  value: string;
  confidence: number;
  boundingBox?: BoundingBox;
}

/** Result of an OCR extraction pass */
export interface OcrResult {
  text: string;
  confidence: number;
  fields: ExtractedField[];
  rawOutput?: unknown;
}

/** Pluggable OCR engine contract */
export interface OcrEngine {
  name: string;
  supportedFormats: string[];
  extract(
    imageData: Buffer | Uint8Array,
    options?: OcrOptions,
  ): Promise<OcrResult>;
}

// ── Quality Checks ──────────────────────────────────────────────────────────

/** Types of quality issues that can be detected */
export type QualityIssueType =
  | 'blur'
  | 'glare'
  | 'tilt'
  | 'low_resolution'
  | 'occlusion';

/** A single quality issue found during image analysis */
export interface QualityIssue {
  type: QualityIssueType;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

/** Result of an image quality check */
export interface QualityCheckResult {
  passed: boolean;
  issues: QualityIssue[];
}

// ── Field Validation ────────────────────────────────────────────────────────

/** Result of validating a single extracted field */
export interface FieldValidationResult {
  fieldName: string;
  valid: boolean;
  errors: string[];
}

/** Validator function signature for a single field */
export type FieldValidator = (
  value: string,
  fieldName: string,
) => FieldValidationResult;

// ── Tamper Detection ────────────────────────────────────────────────────────

/** Types of tampering indicators */
export type TamperIndicatorType =
  | 'font_inconsistency'
  | 'compression_artifact'
  | 'metadata_mismatch'
  | 'copy_paste_zone'
  | 'editing_trace';

/** A single indicator of potential document tampering */
export interface TamperIndicator {
  type: TamperIndicatorType;
  confidence: number;
  description: string;
}

/** Result of tamper detection analysis */
export interface TamperDetectionResult {
  suspicious: boolean;
  indicators: TamperIndicator[];
  riskScore: number;
}

// ── Pipeline ────────────────────────────────────────────────────────────────

/** Full result of the evidence verification pipeline */
export interface VerificationPipelineResult {
  documentType: DocumentType;
  ocrResult: OcrResult;
  qualityCheck: QualityCheckResult;
  fieldValidations: FieldValidationResult[];
  tamperDetection: TamperDetectionResult;
  overallRiskScore: number;
  confidence: number;
  requiresHumanReview: boolean;
  evidenceHash: string;
}

/** Configuration for the evidence verification pipeline */
export interface EvidencePipelineConfig {
  ocrEngine: OcrEngine;
  qualityThresholds?: {
    minResolution?: number;
    maxBlur?: number;
  };
  tamperDetectionEnabled?: boolean;
  humanReviewThreshold?: number;
  fieldValidators?: Record<string, FieldValidator>;
}
