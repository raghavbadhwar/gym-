/**
 * @credverse/evidence-service — Image / document quality checks
 *
 * Lightweight heuristics that run without heavy image-processing deps.
 * Designed to be extended with real libraries (sharp, opencv, etc.).
 */

import type { QualityCheckResult, QualityIssue } from './types.js';

const DEFAULT_MIN_SIZE_BYTES = 10_240; // 10 KB

/**
 * Run basic quality checks on raw image data.
 *
 * Current checks (no external deps):
 *  - Image buffer is non-empty
 *  - Image exceeds a minimum byte-size threshold (proxy for resolution)
 *
 * Returns a {@link QualityCheckResult} with any issues found.
 */
export function checkImageQuality(
  imageData: Buffer | Uint8Array,
  thresholds?: { minResolution?: number; maxBlur?: number },
): QualityCheckResult {
  const issues: QualityIssue[] = [];
  const minSize = thresholds?.minResolution ?? DEFAULT_MIN_SIZE_BYTES;

  if (imageData.length === 0) {
    issues.push({
      type: 'low_resolution',
      severity: 'high',
      description: 'Image data is empty',
    });
  } else if (imageData.length < minSize) {
    issues.push({
      type: 'low_resolution',
      severity: 'medium',
      description: `Image size (${imageData.length} bytes) is below the minimum threshold (${minSize} bytes)`,
    });
  }

  return { passed: issues.length === 0, issues };
}
