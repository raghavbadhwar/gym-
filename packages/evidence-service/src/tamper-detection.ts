/**
 * @credverse/evidence-service — Tamper detection heuristics
 *
 * Lightweight statistical checks on OCR output to flag potentially
 * manipulated documents. Designed to be extended with ML / image-forensic
 * libraries.
 */

import type {
  OcrResult,
  TamperDetectionResult,
  TamperIndicator,
} from './types.js';

const LOW_FIELD_CONFIDENCE = 0.4;
const VARIANCE_THRESHOLD = 0.3;
const MIN_TEXT_LENGTH = 10;

/**
 * Analyse OCR results (and optional file metadata) for signs of tampering.
 *
 * Current heuristics:
 *  1. Fields with very low individual confidence → potential manipulation
 *  2. High variance between field confidences → inconsistent document
 *  3. Very little extracted text → blank or replaced content
 *
 * Returns a risk score 0-100 and relevant {@link TamperIndicator} entries.
 */
export function detectTampering(
  ocrResult: OcrResult,
  metadata?: Record<string, unknown>,
): TamperDetectionResult {
  const indicators: TamperIndicator[] = [];

  // ── 1. Low-confidence fields ────────────────────────────────────────────
  for (const field of ocrResult.fields) {
    if (field.confidence < LOW_FIELD_CONFIDENCE) {
      indicators.push({
        type: 'editing_trace',
        confidence: 1 - field.confidence,
        description: `Field "${field.name}" has unusually low OCR confidence (${(field.confidence * 100).toFixed(1)}%)`,
      });
    }
  }

  // ── 2. Confidence variance ──────────────────────────────────────────────
  if (ocrResult.fields.length >= 2) {
    const confidences = ocrResult.fields.map((f) => f.confidence);
    const mean = confidences.reduce((a, b) => a + b, 0) / confidences.length;
    const variance =
      confidences.reduce((sum, c) => sum + (c - mean) ** 2, 0) /
      confidences.length;

    if (variance > VARIANCE_THRESHOLD) {
      indicators.push({
        type: 'font_inconsistency',
        confidence: Math.min(variance / 0.5, 1),
        description: `High confidence variance across fields (${variance.toFixed(3)}) suggests inconsistent content`,
      });
    }
  }

  // ── 3. Minimal text ─────────────────────────────────────────────────────
  if (ocrResult.text.trim().length < MIN_TEXT_LENGTH) {
    indicators.push({
      type: 'compression_artifact',
      confidence: 0.6,
      description: 'Very little text extracted — document may be blank or replaced',
    });
  }

  // ── 4. Metadata mismatch (extensible) ───────────────────────────────────
  if (metadata) {
    const software = metadata['software'] ?? metadata['Software'];
    if (typeof software === 'string' && /photoshop|gimp/i.test(software)) {
      indicators.push({
        type: 'metadata_mismatch',
        confidence: 0.7,
        description: `Document metadata references image editing software: ${software}`,
      });
    }
  }

  // ── Risk score ──────────────────────────────────────────────────────────
  const riskScore =
    indicators.length === 0
      ? 0
      : Math.min(
          100,
          indicators.reduce((sum, i) => sum + i.confidence * 40, 0),
        );

  return {
    suspicious: riskScore > 30,
    indicators,
    riskScore: Math.round(riskScore),
  };
}
