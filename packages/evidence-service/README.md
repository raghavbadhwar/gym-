# @credverse/evidence-service

Evidence analysis pipeline for the CredVerse ecosystem — pluggable OCR engines, document verification, and risk scoring.

## Overview

This package provides a composable pipeline that turns a raw document image into a structured verification result including:

- **Quality checks** — validates image data is non-empty and meets minimum size thresholds
- **OCR extraction** — delegates to a pluggable `OcrEngine` implementation
- **Field validation** — built-in validators for dates, MRZ checksums, emails, and names
- **Tamper detection** — heuristic analysis of OCR confidence patterns
- **Risk scoring** — weighted combination of quality, validation, and tamper signals
- **Evidence hashing** — SHA-256 hash of the canonical pipeline result

## Quick Start

```typescript
import {
  createVerificationPipeline,
  createStubOcrEngine,
  validateDateField,
} from '@credverse/evidence-service';

const pipeline = createVerificationPipeline({
  ocrEngine: createStubOcrEngine(),
  tamperDetectionEnabled: true,
  humanReviewThreshold: 0.7,
  fieldValidators: {
    date_of_birth: validateDateField,
  },
});

const result = await pipeline.verify(imageBuffer, 'passport');
console.log(result.overallRiskScore); // 0-100
console.log(result.requiresHumanReview); // boolean
```

## API

### Pipeline

| Export | Description |
|--------|-------------|
| `createVerificationPipeline(config)` | Returns `{ verify }` — runs the full evidence pipeline |
| `createStubOcrEngine()` | Stub OCR engine for testing / development |

### Quality

| Export | Description |
|--------|-------------|
| `checkImageQuality(imageData, thresholds?)` | Basic image quality checks |

### Field Validators

| Export | Description |
|--------|-------------|
| `validateDateField(value, fieldName)` | ISO 8601 date validation |
| `validateMrzChecksum(mrz, fieldName)` | ICAO 9303 MRZ check digit |
| `validateEmailField(value, fieldName)` | Basic email format |
| `validateNameField(value, fieldName)` | Non-empty, non-numeric name |
| `createFieldValidator(pattern, msg)` | Regex-based validator factory |

### Tamper Detection

| Export | Description |
|--------|-------------|
| `detectTampering(ocrResult, metadata?)` | Heuristic tamper analysis |

## Extending

### Custom OCR Engine

Implement the `OcrEngine` interface and pass it to the pipeline:

```typescript
import type { OcrEngine } from '@credverse/evidence-service';

const myEngine: OcrEngine = {
  name: 'tesseract',
  supportedFormats: ['image/png', 'image/jpeg'],
  async extract(imageData, options) {
    // call tesseract.js or a cloud OCR API
    return { text: '...', confidence: 0.95, fields: [] };
  },
};
```

### Custom Field Validators

Use `createFieldValidator` for simple patterns or write a full `FieldValidator` function:

```typescript
import { createFieldValidator } from '@credverse/evidence-service';

const validateZipCode = createFieldValidator(
  /^\d{5}(-\d{4})?$/,
  'must be a valid US zip code',
);
```
