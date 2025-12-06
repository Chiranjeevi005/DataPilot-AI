DataPilot AI - Backend Processing (Phase 5)

## PDF & Complex JSON Processing
As of Phase 5, the worker pipeline supports:

### PDF Extraction
- **Library**: `pdfplumber`
- **Workflow**:
  1.  Attempts to identify tables on each page.
  2.  Scores detected tables based on size, numeric content, and completeness.
  3.  Selects the highest-scoring table for analysis (EDA).
  4.  **Fallback**: If no good tables are found, extracts text (up to 5000 chars) and returns it in `text_extract` field with a "non_tabular_pdf" issue.
- **Limitations**:
  - Scanned PDFs (images) are NOT currently supported (requires OCR).
  - Merged cells and complex multi-header tables may need manual cleanup.

### JSON Normalization
- **Library**: `pandas.json_normalize` & custom heuristics.
- **Workflow**:
  1.  If input is a list of objects, normalizes directly.
  2.  If input is a dict, searches for common keys (`rows`, `data`, `items`, etc.) containing a list.
  3.  Flattens nested structures where possible.
  4.  **Fallback**: If no tabular structure is found, returns a snippet of the JSON in `text_extract`.

## Testing Phase 5
1.  Run the backend (upload API) and worker.
2.  Use `python scripts/test_phase5.py` to generate sample `invoices.pdf` and `customers.json`, upload them, and verify results.
