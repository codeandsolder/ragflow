# Golden Test Samples Directory

This directory contains curated sample files for testing document processing, parsing, and extraction functionality in RAGFlow.

## Directory Structure

```
test/samples/
├── documents/
│   ├── pdf/
│   │   ├── sample_simple.pdf
│   │   ├── sample_with_images.pdf
│   │   ├── sample_with_tables.pdf
│   │   └── sample_multilingual.pdf
│   ├── docx/
│   │   ├── sample_simple.docx
│   │   └── sample_with_tables.docx
│   ├── xlsx/
│   │   ├── sample_simple.xlsx
│   │   └── sample_with_formulas.xlsx
│   └── pptx/
│       └── sample_simple.pptx
├── images/
│   ├── sample_text.png
│   ├── sample_table.png
│   └── sample_chart.png
└── expected_outputs/
    ├── pdf_simple.json
    ├── pdf_with_tables.json
    ├── docx_simple.json
    ├── xlsx_simple.json
    └── image_text.json
```

## Purpose

Each sample file serves a specific testing purpose:

### PDF Samples
- **sample_simple.pdf**: Plain text paragraphs for basic extraction testing
- **sample_with_images.pdf**: Tests image extraction and layout preservation
- **sample_with_tables.pdf**: Tests table detection and structure extraction
- **sample_multilingual.pdf**: Tests multilingual content (EN, ZH, JA, etc.)

### DOCX Samples
- **sample_simple.docx**: Basic Word document with paragraphs and headings
- **sample_with_tables.docx**: Tests table parsing in Word documents

### XLSX Samples
- **sample_simple.xlsx**: Basic spreadsheet with data
- **sample_with_formulas.xlsx**: Tests formula evaluation and result extraction

### PPTX Samples
- **sample_simple.pptx**: Basic presentation for slide parsing

### Image Samples
- **sample_text.png**: Text-only image for OCR testing
- **sample_table.png**: Table image for OCR table extraction
- **sample_chart.png**: Chart/graph image for visual element detection

## Expected Outputs

The `expected_outputs/` directory contains JSON fixtures with expected extraction results. These are used to verify that parsers produce correct output.

## How to Generate Samples

### Option 1: Generate Synthetic Samples
Create minimal test files programmatically using libraries like:
- `reportlab` for PDFs
- `python-docx` for Word documents
- `openpyxl` for Excel files
- `python-pptx` for PowerPoint
- `Pillow` for images

### Option 2: Use Public Domain / Open Source Sources
- Wikipedia articles as plain text
- Open government documents
- Creative Commons licensed materials

### Option 3: Manual Creation
Create simple test documents manually using office software.

## Licensing Requirements

- All samples should be either:
  - Synthetic/generated for testing purposes
  - Public domain or Creative Commons licensed
  - Generated from open source tools
- DO NOT use copyrighted material without proper licensing
- Document source and license for each sample in a `SOURCES.md` file

## How to Add New Samples

1. Add the sample file to the appropriate subdirectory
2. Create corresponding expected output JSON in `expected_outputs/`
3. Update this README with the new sample description
4. Document source/licensing in `SOURCES.md`
5. Run tests to verify extraction matches expected output

## Notes

- Keep sample files small (under 1MB) for fast test execution
- Use standard formats and encoding (UTF-8)
- Avoid password-protected files in test samples
- Include variety in layouts, fonts, and structures
