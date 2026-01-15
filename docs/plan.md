# Implementation Plan: Book Location Map

## Project Overview

Static interactive map showing where reviewed books are set.

**Features:**
- YAML input file for easy editing
- Python build script for generation
- Leaflet.js for interactive mapping
- Individual pins with smart offset for duplicates
- Off-screen indicators showing hidden pins
- 19 map style options (CartoDB, OSM, Stamen, ESRI, etc.)
- 6 pin style options
- Dual output: production + preview with style chooser
- Self-contained HTML files

---

## Current Status

✅ **POLISHING** - Project is working and deployable

**Completed:**
- 44 books with covers and review links in books.yaml
- Build script with YAML validation and geocoding cache
- Self-contained HTML output (production + preview)
- Format documentation in books.yaml
- Multiple map/pin styles (default: positron map, burgundy circles)
- Auto-generated cover images from Google Books (embeddable, no local files)
- Metadata enrichment tool (`enrich_books.py`) for auto-filling book data from Google Books API
- Combined README with setup and user guide
- Squarespace embedding instructions

**Not Yet Verified:**
- Squarespace embedding in production (instructions provided)
- Some locations may need refinement (some are generic like "United States")

**Known Limitations:**
- Geocoding may fail for ambiguous location names
- Book covers depend on Google Books having them indexed by ISBN

---

## Project Structure

```
erindouglass-bookmap/
├── books.yaml              # Input file - includes format docs
├── build.py                # Build script
├── enrich_books.py         # Utility to auto-fill metadata from APIs
├── requirements.txt        # Python dependencies
├── output/
│   ├── index.html          # Production: clean, for Squarespace
│   └── preview.html        # Preview: with style chooser panel
├── cache/
│   └── geocoding.json      # Cached coordinates (auto-generated)
├── docs/
│   ├── plan.md             # This file
│   ├── squarespace_guide.md
│   └── archive/            # Old planning documents
└── README.md               # Setup, usage, and user guide
```

**Note:** HTML template and CSS are embedded directly in `build.py` and generated inline in the output HTML files (self-contained approach).

---

## Technical Decisions

### Dependencies
- **Python 3.7+**
- **pyyaml**: YAML parsing
- **ruamel.yaml**: YAML editing with formatting preservation
- **geopy**: Geocoding with Nominatim
- **python-dotenv**: Environment configuration

### Geocoding Service
- **Nominatim** (OpenStreetMap)
  - Free, no API key
  - Rate limit: 1 req/sec
  - Caching mitigates rate limits

### Map Library
- **Leaflet.js** (CDN)
- **Leaflet.markercluster** (CDN)
- **CartoDB Positron tiles** (default: free, no API key, light minimal style)

### Output Format
- **Self-contained HTML files**: all CSS/JavaScript embedded inline
- Book data embedded as JSON
- Upload HTML files from `output` folder (book covers load from Google Books)

---

## Optional Next Steps

**Note:** The project is functional as-is. These are optional improvements:

4. Improve styling of book detail tiles
1. Deploy to Squarespace and verify embedding works
2. Refine generic locations to be more specific where needed

---

## Future Enhancements (If Needed)

**Note:** Keep it simple. Only add these if there's a real need:

1. **Filtering/Search**: Only if managing many books becomes difficult
2. **Auto-deploy**: Only if manual build becomes a burden

**Philosophy:** This is a simple tool. Avoid feature creep. If it works for the use case, leave it alone.
