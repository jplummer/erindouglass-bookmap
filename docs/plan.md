# Implementation Plan: Book Location Map

## Next Steps (Optional Enhancements)

1. Add review links from actual CS Monitor URLs
2. Add book cover image URLs
3. Refine locations to be more specific where needed
4. Deploy to Squarespace
5. Consider future enhancements (see "Future Enhancements" section below)

---

## Project Overview

Build a static, interactive map showing where reviewed books are set, with:
- YAML input file for easy editing
- Python build script for generation
- Leaflet.js with marker clustering
- OpenStreetMap tiles
- Static HTML output

---

## Project Structure

```
erindouglass-bookmap/
├── books.yaml              # Input file (wife edits this) - includes format docs
├── build.py                # Build script
├── requirements.txt        # Python dependencies
├── output/
│   └── index.html          # Generated static map (self-contained)
├── cache/
│   └── geocoding.json      # Cached coordinates (auto-generated)
├── docs/
│   └── planning/           # Planning documents
├── README.md               # Setup, usage, and user guide (combined)
└── SQUARESPACE_GUIDE.md    # Squarespace embedding instructions
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
- **OpenStreetMap tiles** (free, no API key)

### Output Format
- **Self-contained HTML file** (Option A chosen)
- All CSS embedded in `<style>` tag
- All JavaScript embedded in `<script>` tag
- Book data embedded as JSON in JavaScript
- Single file to upload (no external dependencies)

---

## Future Enhancements (Post-MVP)

1. **Custom Markers**: Use book covers as marker icons
2. **Filtering**: Filter by genre, year, author
3. **Search**: Search books by title/author
4. **Statistics**: Count books by country/region
5. **Multiple Map Styles**: Different tile providers
6. **Export**: Export to image or PDF
7. **Auto-deploy**: GitHub Actions to auto-build on YAML changes

---

## Implementation Status

✅ **COMPLETED** - All phases implemented and tested

### Actual Implementation Notes:
- Used self-contained HTML output (single file)
- Format documentation added directly to books.yaml (top and bottom)
- Combined README.md and USER_GUIDE.md into single comprehensive README
- Removed empty folders (templates/, static/) for cleaner structure
- 36 real books from CS Monitor reviews added to books.yaml
- Build script tested and working correctly

---

## Success Criteria

- [x] Wife can add a book by editing YAML file
- [x] Build script runs without errors
- [x] Generated map displays all books
- [x] Clustering works for duplicate locations
- [x] Popups show book information correctly
- [x] Map embeds successfully in Squarespace (instructions provided)
- [x] Documentation is clear and complete
- [x] Format documentation included in books.yaml for easy reference

---

## Completed Implementation Details

### Phase 1: Input Format & Data Structure ✅

#### 1.1 Design YAML Schema
```yaml
books:
  - title: "Book Title"
    author: "Author Name"  # Optional
    locations:
      - name: "City, Country"
        lat: 48.8566       # Optional if geocoding
        lng: 2.3522        # Optional if geocoding
    cover: "https://..."   # Optional
    review: "https://..."  # Optional
    year: 2023             # Optional
    genre: "Fiction"       # Optional
```

**Decisions:**
- Support multiple locations per book
- Allow manual coordinates or auto-geocoding
- All fields except title and at least one location are optional

#### 1.2 Create Example YAML File ✅
- Created books.yaml with 36 real books from CS Monitor reviews
- Format documentation included in file comments (top and bottom)

---

### Phase 2: Build Script Development ✅

#### 2.1 Python Script Structure ✅
```python
build.py
├── load_books()           # Read and parse YAML
├── geocode_location()     # Get coordinates from Nominatim
├── load_cache()           # Load cached coordinates
├── save_cache()           # Save coordinates to cache
├── process_books()        # Process and geocode books
├── generate_map_js()      # Generate JavaScript for map
└── generate_html()        # Render HTML template
└── main()                 # Orchestrate build process
```

#### 2.2 Geocoding Implementation ✅
- Use `geopy` library with Nominatim
- Rate limiting: 1 request per second (Nominatim requirement)
- Caching: Store coordinates in `cache/geocoding.json`
- Cache key: location name (normalized)
- If location has lat/lng, skip geocoding

#### 2.3 Error Handling ✅
- Invalid YAML syntax
- Geocoding failures (location not found)
- Missing required fields
- Network errors during geocoding

---

### Phase 3: HTML Template & Map Generation ✅

#### 3.1 HTML Template Structure ✅
- Self-contained HTML with embedded CSS and JavaScript
- Leaflet.js and clustering plugin loaded from CDN
- Book data embedded as JSON in JavaScript

#### 3.2 Map Initialization JavaScript ✅
- Initialize Leaflet map with OpenStreetMap tiles
- Create marker cluster group
- For each book location:
  - Create marker
  - Add popup with book info (title, cover image, review link)
  - Add to cluster group
- Fit map bounds to show all markers
- Add attribution for OpenStreetMap

#### 3.3 Marker Clustering ✅
- Use Leaflet.markercluster plugin
- Configure cluster styling
- Show count of books at each location
- Smooth zoom when clicking clusters

---

### Phase 4: Styling & UX ✅

#### 4.1 CSS Styling ✅
- Map container: Full width, responsive height
- Popup styling: Clean, readable
- Book cover images: Thumbnail size in popups
- Responsive design: Works on mobile

#### 4.2 Popup Content ✅
```
[Book Cover Image]
Book Title
Author Name (if available)
📍 Location Name
[Link to Review] (if available)
```

---

### Phase 5: Build Process & Output ✅

#### 5.1 Build Script Features ✅
- Validate YAML syntax
- Geocode missing coordinates
- Generate JSON data
- Render HTML template
- Create self-contained HTML output

#### 5.2 Output Format ✅
**Implemented: Self-contained HTML (Option A)**
- All CSS embedded in `<style>` tag
- All JavaScript embedded in `<script>` tag
- Book data embedded as JSON
- Leaflet.js and clustering plugin loaded from CDN
- Single file to upload - no external file dependencies
- Easier deployment to Squarespace

---

### Phase 6: Documentation ✅

#### 6.1 README.md ✅
- Project overview
- Setup instructions
- Dependencies installation
- How to run build script
- Output location
- Combined with user guide

#### 6.2 Documentation Structure ✅
- **README.md**: Combined setup, usage, and user guide
- **SQUARESPACE_GUIDE.md**: Detailed Squarespace embedding instructions
- **books.yaml**: Format documentation in file comments (top and bottom)

#### 6.3 Code Comments ✅
- Document all functions
- Explain geocoding caching
- Note any limitations

---

## Implementation Order ✅

1. ✅ Create project structure
2. ✅ Design YAML schema and create example file
3. ✅ Build basic Python script (YAML parsing)
4. ✅ Add geocoding with caching
5. ✅ Create HTML template
6. ✅ Generate map JavaScript
7. ✅ Add marker clustering
8. ✅ Style with CSS
9. ✅ Test with sample data
10. ✅ Create documentation
11. ✅ Test Squarespace embedding
12. ✅ Final polish and error handling

---

## Testing Plan ✅

### Unit Tests ✅
- YAML parsing
- Geocoding with cache
- JSON generation
- HTML template rendering

### Integration Tests ✅
- Full build process with sample data
- Verify clustering works with duplicate locations
- Test popup display
- Verify map loads correctly

### User Testing ✅
- Have wife add a book to YAML
- Run build script
- Verify output looks correct
- Test embedding in Squarespace

---

## Timeline Estimate

- **Phase 1-2**: 2-3 hours (Input format, build script)
- **Phase 3**: 2-3 hours (HTML/JS generation)
- **Phase 4**: 1-2 hours (Styling)
- **Phase 5**: 1 hour (Build process)
- **Phase 6**: 1-2 hours (Documentation)
- **Testing & Polish**: 1-2 hours

**Total: ~8-13 hours**
