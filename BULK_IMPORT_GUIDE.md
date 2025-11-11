# ULTRA DOJO AI - Bulk Import Guide
**Version:** 3.0
**Date:** 2025-11-11

---

## Overview

The bulk import feature allows you to import multiple RAG nuggets and Golden Standards at once from JSON files, instead of adding them one by one through the admin panel.

---

## Features Added

### 1. Backend Endpoints

#### **POST** `/api/v1/admin/rag/bulk-import`
- Imports multiple RAG nuggets from JSON array
- Validates each nugget (title, content required)
- Generates embeddings and stores in Qdrant
- Returns success/error counts with detailed error messages

#### **POST** `/api/v1/admin/golden-standards/bulk-import`
- Imports multiple golden standards from JSON array
- Validates each standard (trigger_context, golden_response required)
- Stores in PostgreSQL and generates Qdrant embeddings
- Returns success/error counts with detailed error messages

### 2. Frontend UI

#### **RAG Tab (Admin Panel)**
- "Bulk Import JSON" button in the nuggets list header
- File upload accepts `.json` files only
- Results modal shows success/error counts
- Automatic list refresh after import

#### **Feedback Tab (Admin Panel)**
- "Bulk Import JSON" button next to "Utwórz Złoty Standard"
- File upload accepts `.json` files only
- Results modal shows success/error counts
- Automatic groups refresh after import

---

## JSON File Format

### RAG Nuggets Format

**File:** `sample_rag_nuggets.json`

```json
[
  {
    "title": "Model 3 Long Range - zasięg WLTP 2024",
    "content": "Tesla Model 3 Long Range (2024) osiąga zasięg do 629 km...",
    "type": "technical",
    "tags": ["model_3", "long_range", "zasięg"],
    "keywords": "model 3, zasięg, long range, wltp",
    "archetype_filter": ["range_conscious", "tech_enthusiast"]
  },
  {
    "title": "Another nugget...",
    "content": "Content here...",
    "type": "financial",
    "tags": ["leasing", "b2b"],
    "keywords": "keywords here",
    "archetype_filter": ["business_buyer"]
  }
]
```

**Required Fields:**
- `title` (string) - Title of the nugget
- `content` (string) - Main content/knowledge

**Optional Fields:**
- `type` (string) - Category (technical, financial, competitive, objection_handling, etc.)
- `tags` (array of strings) - Tags for filtering
- `keywords` (string) - Keywords for search
- `archetype_filter` (array of strings) - Target customer archetypes

### Golden Standards Format

**File:** `sample_golden_standards.json`

```json
[
  {
    "trigger_context": "Klient pyta o zasięg Model 3 w zimie",
    "golden_response": "Świetne pytanie! Model 3 Long Range ma zasięg WLTP 629 km...",
    "tags": ["zasięg", "zima", "model_3"],
    "category": "technical"
  },
  {
    "trigger_context": "Klient obawia się długiego czasu ładowania",
    "golden_response": "Rozumiem tę obawę - to najczęstsza obiekcja...",
    "tags": ["ładowanie", "czas", "obiekcja"],
    "category": "objection_handling"
  }
]
```

**Required Fields:**
- `trigger_context` (string) - The situation/question that triggers this standard
- `golden_response` (string) - The ideal response to provide

**Optional Fields:**
- `tags` (array of strings) - Tags for categorization
- `category` (string) - Category (technical, objection_handling, competitive, etc.)

---

## How to Use

### Step 1: Prepare Your JSON File

1. Create a JSON file with your data following the format above
2. Ensure it's a valid JSON array (starts with `[` and ends with `]`)
3. Each item should be a valid object with required fields

### Step 2: Import via Admin Panel

#### For RAG Nuggets:
1. Open Admin Panel → RAG Tab
2. Click "Bulk Import JSON" button (top right)
3. Select your JSON file
4. Wait for processing (you'll see "Importing..." status)
5. Results modal will appear showing success/error counts

#### For Golden Standards:
1. Open Admin Panel → Feedback Tab
2. Click "Bulk Import JSON" button (top right, blue button)
3. Select your JSON file
4. Wait for processing (you'll see "Importing..." status)
5. Results modal will appear showing success/error counts

### Step 3: Review Results

The results modal shows:
- **Success Count** - Number of items imported successfully (green box)
- **Error Count** - Number of items that failed (red box, if any)
- **Error Details** - First 10 errors with item numbers and reasons

### Step 4: Verify Import

- **RAG Nuggets:** Check the nuggets list - new items should appear
- **Golden Standards:** The feedback groups will reload automatically

---

## Sample Files Provided

Two sample files have been created in the project root:

### 1. `sample_rag_nuggets.json`
Contains 10 example nuggets covering:
- Technical specs (Model 3 range, performance)
- Features (Autopilot, OTA updates)
- Infrastructure (Supercharger network)
- Financial (leasing, tax benefits)
- Competitive analysis (vs BMW i4)
- Objection handling (range anxiety, charging time)

### 2. `sample_golden_standards.json`
Contains 5 example golden standards covering:
- Technical questions (range in winter)
- Objections (charging time concerns)
- Financial (cost of ownership)
- Competitive (Tesla vs BMW i4)
- B2B (leasing for companies)

---

## Error Handling

### Common Errors:

1. **"Missing title or content"**
   - Solution: Ensure all nuggets have both `title` and `content` fields

2. **"Missing trigger_context or golden_response"**
   - Solution: Ensure all standards have both required fields

3. **"Invalid JSON format"**
   - Solution: Validate your JSON using a JSON validator (jsonlint.com)
   - Ensure it's an array, not a single object

4. **"Expected an array"**
   - Solution: Your JSON should start with `[` and end with `]`

### Partial Success:

If some items succeed and others fail:
- Status will be "partial"
- Successfully imported items will be saved
- Error modal will show which items failed and why
- You can fix the errors and re-import only the failed items

---

## API Response Format

Both endpoints return the same response structure:

```json
{
  "status": "success" | "partial" | "error",
  "data": {
    "success_count": 8,
    "error_count": 2,
    "errors": [
      "Item 3: Missing title or content",
      "Item 7: Invalid embedding generation"
    ]
  }
}
```

---

## Best Practices

### 1. Start Small
- Test with 5-10 items first
- Verify they import correctly
- Then import larger batches

### 2. Use Descriptive Titles
- Make titles searchable and specific
- Include key terms that sellers will search for

### 3. Add Relevant Tags
- Tags improve filtering and discovery
- Use consistent tag naming (lowercase, underscores)

### 4. Target Archetypes
- Use `archetype_filter` to target specific customer types
- Common archetypes: `range_conscious`, `tech_enthusiast`, `business_buyer`, `cost_conscious`

### 5. Categorize Content
- Use `type` or `category` to organize content
- Common types: `technical`, `financial`, `competitive`, `objection_handling`, `lifestyle`

### 6. Keep Responses Natural
- Golden responses should sound conversational, not scripted
- Include empathy phrases ("Rozumiem...", "Świetne pytanie!")
- Use specific numbers and examples

### 7. Test After Import
- Verify nuggets appear in the list
- Test RAG search to ensure they're being retrieved
- Check if golden standards are properly categorized

---

## Troubleshooting

### Import Button Not Working?
- Check browser console for errors
- Ensure backend is running on `http://localhost:8000`
- Verify admin key is correct (`ultra-admin-key-2024`)

### No Results After Import?
- Check if the results modal appeared
- Look at the error count - might be validation issues
- Verify JSON file format

### Embeddings Taking Long?
- Large batches (100+ items) may take 30-60 seconds
- Each item needs an embedding generated via Gemini API
- Be patient - the UI will show "Importing..." status

### Backend Errors?
- Restart backend: `cd backend && uvicorn app.main:app --reload`
- Check backend logs for detailed error messages
- Verify Qdrant and PostgreSQL are running

---

## Technical Details

### Backend Implementation

**RAG Import Process:**
1. Parse and validate JSON
2. For each nugget:
   - Validate required fields (title, content)
   - Generate embedding via Gemini (text-embedding-004)
   - Create Qdrant point with metadata
   - Add to batch
3. Bulk upsert to Qdrant
4. Return success/error counts

**Golden Standards Import Process:**
1. Parse and validate JSON
2. For each standard:
   - Validate required fields (trigger_context, golden_response)
   - Insert into PostgreSQL `golden_standards` table
   - Generate embedding via Gemini
   - Create Qdrant point with type="golden_standard"
   - Upsert to Qdrant
3. Commit database transaction
4. Return success/error counts

### Frontend Implementation

**Flow:**
1. User clicks "Bulk Import JSON" button
2. Hidden file input opens
3. User selects JSON file
4. File is read as text and parsed
5. Validation: Must be an array
6. POST request to backend with JSON data
7. Show "Importing..." status during processing
8. Results modal appears with success/error counts
9. List automatically refreshes

---

## Future Enhancements

Potential improvements for v4.0:

1. **CSV Import** - Support CSV format in addition to JSON
2. **Drag & Drop** - Allow drag-and-drop file upload
3. **Preview Mode** - Show preview of items before importing
4. **Progress Bar** - Real-time progress for large imports
5. **Undo Import** - Ability to rollback a bulk import
6. **Duplicate Detection** - Warn about duplicate titles/contexts
7. **Template Generator** - Export current nuggets as template
8. **Scheduled Imports** - Auto-import from Google Sheets/Airtable

---

## Summary

Bulk import significantly speeds up knowledge base expansion:

- **Before:** 1 nugget every 2-3 minutes (manual form) = 20-30 nuggets/hour
- **After:** 100 nuggets in ~30 seconds (bulk import) = 12,000 nuggets/hour

**To expand from 101 to 500 nuggets:**
- Manual: ~20-30 hours of work
- Bulk import: ~2-3 minutes

**Next Steps:**
1. Use the provided sample files to test the feature
2. Create your own JSON files with domain-specific knowledge
3. Import in batches of 50-100 for optimal performance
4. Monitor the results and fix any validation errors

---

**Questions or Issues?**
Check the backend logs in `backend/logs/` for detailed error messages.
