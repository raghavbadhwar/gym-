/**
 * @credverse/evidence-service
 * Evidence analysis pipeline: pluggable OCR engines, document verification, risk scoring
 */

// Types
export type {
  BoundingBox,
  ImageRegion,
  DocumentType,
  OcrOptions,
  ExtractedField,
  OcrResult,
  OcrEngine,
  QualityIssue,
  QualityCheckResult,
  FieldValidationResult,
  FieldValidator,
  TamperIndicator,
  TamperDetectionResult,
  VerificationPipelineResult,
  EvidencePipelineConfig,
} from './types.js';

// Quality checks
export { checkImageQuality } from './quality-check.js';

// Field validators
export {
  validateDateField,
  validateMrzChecksum,
  validateEmailField,
  validateNameField,
  createFieldValidator,
} from './field-validators.js';

// Tamper detection
export { detectTampering } from './tamper-detection.js';

// Pipeline
export {
  createVerificationPipeline,
  createStubOcrEngine,
} from './pipeline.js';
