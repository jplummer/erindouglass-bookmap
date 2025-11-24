# Implementation Plan: Book Location Map

## Next Steps

1. Add review links from actual CS Monitor URLs (if available)
2. Add book cover image URLs (if available)
3. Deploy to Squarespace and verify it works
4. Refine locations to be more specific where needed (optional)

**Note:** The project is functional as-is. These are optional improvements.

---

## Project Overview

Build a static, interactive map showing where reviewed books are set, with:
- YAML input file for easy editing
- Python build script for generation
- Leaflet.js with marker clustering
- CartoDB Positron tiles (light, minimal style)
- Auto-zoom to show all markers
- Static HTML output

---

## Project Structure

```
erindouglass-bookmap/
├── books.yaml              # Input file - includes format docs
├── build.py                # Build script
├── requirements.txt        # Python dependencies
├── output/
│   └── index.html          # Generated static map (self-contained)
├── cache/
│   └── geocoding.json      # Cached coordinates (auto-generated)
├── docs/                   # Plan and how-to
│   └── archive/            # Old planning documents
├── README.md               # Setup, usage, and user guide (combined)
└── docs/
    └── squarespace_guide.md  # Squarespace embedding instructions
```

**Note:** HTML template and CSS are embedded directly in `build.py` and generated inline in the output HTML file (self-contained approach).

---

## Technical Decisions

### Dependencies
- **Python 3.7+**
- **pyyaml**: YAML parsing
- **geopy**: Geocoding with Nominatim
- **Note**: HTML template uses Python string formatting (no jinja2 needed)

### Geocoding Service
- **Nominatim** (OpenStreetMap)
  - Free, no API key
  - Rate limit: 1 req/sec
  - Good for occasional use
  - Caching mitigates rate limits

### Map Library
- **Leaflet.js** (CDN)
- **Leaflet.markercluster** (CDN)
- **CartoDB Positron tiles** (free, no API key, light minimal style)

### Output Format
- **Self-contained HTML file** (Option A chosen)
- All CSS embedded in `<style>` tag
- All JavaScript embedded in `<script>` tag
- Book data embedded as JSON in JavaScript
- Single file to upload (no external dependencies)

---

## Future Enhancements (If Needed)

**Note:** Keep it simple. Only add these if there's a real need:

1. **Alternate pin styling**: Explore different marker styles/icons (simple customization)
2. **Custom Markers**: Use book covers as marker icons (nice-to-have, adds complexity)
3. **Filtering/Search**: Only if managing many books becomes difficult
4. **Auto-deploy**: Only if manual build becomes a burden

**Philosophy:** This is a simple tool. Avoid feature creep. If it works for the use case, leave it alone.

---

## Implementation Status

✅ **FUNCTIONAL** - Core functionality implemented and working

### What's Actually Done:
- Self-contained HTML output (single file)
- Format documentation in books.yaml (top and bottom)
- Combined README with user guide
- 36 books added to books.yaml (locations geocoded, but covers/reviews not yet added)
- Build script works: validates YAML, geocodes locations, generates map
- YAML validation (checks structure, required fields, data types, coordinates)
- CartoDB Positron map style (light, minimal)
- Auto-zoom to show all markers on load

### What's Not Fully Tested:
- Squarespace embedding (instructions provided, but not verified in production)
- Edge cases in geocoding (some locations may need manual coordinates)
- All 36 books verified for accuracy

### Known Limitations:
- No book covers or review links added yet (fields supported, just not populated)
- Some locations are generic (e.g., "United States" instead of specific cities)
- Geocoding may fail for ambiguous location names

---

## Success Criteria

- [x] User can add a book by editing YAML file
- [x] Build script runs without errors (with valid YAML)
- [x] Generated map displays books correctly
- [x] Clustering works for duplicate locations
- [x] Popups show book information correctly
- [x] YAML validation catches common errors
- [ ] Map embeds successfully in Squarespace (instructions provided, not yet verified)
- [x] Documentation is clear and complete
- [x] Format documentation included in books.yaml for easy reference

---

## Completed Work (Archived)

### Implementation Summary ✅
- **YAML Schema**: Supports multiple locations per book, optional fields (author, cover, review, year, genre), manual coordinates or auto-geocoding
- **Build Script**: YAML parsing, geocoding with caching, validation, HTML generation, summary statistics
- **Map Features**: CartoDB Positron tiles, marker clustering, auto-zoom to bounds, popups with book info
- **Styling**: Responsive design, clean popups, embedded CSS
- **Documentation**: README with user guide, format docs in books.yaml, Squarespace guide

### Testing Status ✅
- **Tested**: YAML parsing/validation, geocoding with cache, full build process, map display, clustering, auto-zoom
- **Not fully tested**: Squarespace embedding, edge cases, all book location accuracy

### Timeline ✅
Completed in ~8-13 hours across phases: input format (2-3h), build script (2-3h), HTML/JS (2-3h), styling (1-2h), build process (1h), documentation (1-2h), testing (1-2h)
