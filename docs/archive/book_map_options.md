# Book Location Map - Options Analysis

## Overview
Create an interactive map showing where reviewed books are set, maintainable via a simple data file (book title, location(s), optional cover image, optional review link).

## Executive Summary

**Recommended Solution: Static Leaflet.js Map with YAML/CSV Input + Build Script**

This approach provides:
- ✅ **Easy input**: YAML or CSV (much easier than JSON)
- ✅ **Pin clustering**: Automatically handles multiple books in same cities
- ✅ **Static output**: Generate once, host anywhere (Squarespace or self-hosted)
- ✅ **OpenStreetMap**: Free, no API keys, open source
- ✅ **Customizable**: Can style map and pins later
- ✅ **Simple workflow**: Edit file → run script → upload HTML

**How it works:**
1. User edits a YAML or CSV file with book information
2. Run a build script that geocodes locations and generates static HTML
3. Upload the HTML file to Squarespace or self-host
4. Map is fully interactive with clustering for overlapping locations

---

## Option 1: Leaflet.js with JSON Data File
**Technology:** Leaflet.js (open-source mapping library) + JSON/CSV data file

### How it works:
- Create a simple HTML page with Leaflet.js
- Maintain a JSON or CSV file with book data
- Host on GitHub Pages, Netlify, or similar (free)
- Embed in Squarespace via iframe or code block

### Pros:
- ✅ **Free** - No API keys or paid services needed
- ✅ **Full control** - Complete customization of appearance
- ✅ **Easy maintenance** - Just edit a JSON/CSV file
- ✅ **No vendor lock-in** - Open source, portable
- ✅ **Can include images** - Book covers as markers or popups
- ✅ **Works offline** - Can be downloaded and hosted anywhere

### Cons:
- ❌ **Requires hosting** - Need somewhere to host the HTML/JS files
- ❌ **Initial setup** - Someone needs to create the initial HTML/JS
- ❌ **Basic styling** - Default Leaflet styling is functional but not fancy

### Maintenance:
- Edit JSON file: `{"title": "Book Name", "location": "Paris, France", "cover": "url", "review": "url"}`
- Save and push to hosting (or use a simple web interface)

---

## Option 2: Google My Maps
**Technology:** Google's My Maps service

### How it works:
- Create a map in Google My Maps (web interface)
- Add markers manually or import from spreadsheet
- Get embed code for Squarespace

### Pros:
- ✅ **Easiest to use** - Visual interface, no coding
- ✅ **No hosting needed** - Google hosts it
- ✅ **Familiar interface** - Google Maps everyone knows
- ✅ **Can import from spreadsheet** - Bulk import possible
- ✅ **Free** - No cost

### Cons:
- ❌ **Limited customization** - Styling options are basic
- ❌ **Google branding** - Always visible
- ❌ **No custom markers** - Limited marker customization
- ❌ **Images in popups** - Possible but clunky
- ❌ **Less professional** - Looks like a Google product

### Maintenance:
- Use Google My Maps web interface
- Add/edit markers visually
- Or import/export via spreadsheet

---

## Option 3: Mapbox Studio + Custom Code
**Technology:** Mapbox Studio + Mapbox GL JS

### How it works:
- Design custom map style in Mapbox Studio
- Create HTML page with Mapbox GL JS
- Use JSON data file for book locations
- Host and embed in Squarespace

### Pros:
- ✅ **Beautiful maps** - Highly customizable, professional styling
- ✅ **Custom markers** - Can use book covers as markers
- ✅ **Modern look** - Very polished appearance
- ✅ **Good performance** - Fast and smooth

### Cons:
- ❌ **Requires API key** - Free tier available but has limits
- ❌ **More complex setup** - Requires Mapbox account and setup
- ❌ **Requires hosting** - Need to host the HTML/JS
- ❌ **Learning curve** - More technical than other options

### Maintenance:
- Edit JSON data file
- Map styling changes require Mapbox Studio access

---

## Option 4: Static Image Map (Generated)
**Technology:** Python script or web service to generate map image

### How it works:
- Maintain a data file (CSV/JSON)
- Run a script that generates a static map image
- Upload image to Squarespace
- Or use a service that auto-generates from data

### Pros:
- ✅ **Simple** - Just an image, no code
- ✅ **No hosting** - Lives in Squarespace
- ✅ **Fast loading** - No JavaScript needed
- ✅ **Works everywhere** - Any CMS can use it

### Cons:
- ❌ **Not interactive** - Can't click markers
- ❌ **Less engaging** - Static vs. interactive
- ❌ **Requires regeneration** - Need to run script when updating
- ❌ **Limited detail** - Can't zoom or explore

### Maintenance:
- Edit data file
- Run generation script
- Upload new image to Squarespace

---

## Option 5: Squarespace Code Block with Embedded Map
**Technology:** Leaflet.js or Google Maps embedded directly in Squarespace

### How it works:
- Create HTML/JS code block in Squarespace
- Include map code directly in the page
- Data file hosted elsewhere or inline

### Pros:
- ✅ **Lives in Squarespace** - No external hosting
- ✅ **Integrated** - Part of the site

### Cons:
- ❌ **Squarespace limitations** - Code blocks have restrictions
- ❌ **Harder to maintain** - Editing code in Squarespace is clunky
- ❌ **Data file hosting** - Still need somewhere for the data file
- ❌ **Less flexible** - Limited by Squarespace's code block capabilities

---

## Option 6: Web App with Simple Admin Interface
**Technology:** Simple web app (e.g., using a static site generator or simple backend)

### How it works:
- Build a simple web app with an admin interface
- User logs in, adds/edits books via form
- Map auto-updates
- Embed in Squarespace

### Pros:
- ✅ **Easiest maintenance** - Web form interface
- ✅ **No file editing** - No need to edit JSON/CSV
- ✅ **User-friendly** - Designed for non-technical users

### Cons:
- ❌ **Most complex to build** - Requires backend or service
- ❌ **Requires hosting** - Need server or service
- ❌ **Ongoing costs** - May need paid hosting/service
- ❌ **Overkill?** - Might be more than needed

---

## Updated Requirements & Revised Recommendations

### Key Requirements:
1. **Input format**: YAML, Markdown, or CSV (not JSON - too difficult to edit)
2. **Ease of use**: Critical - must be simple to maintain
3. **Pin clustering**: Handle multiple books in same cities (no overlapping pins)
4. **Static generation**: Generate map as needed, otherwise static
5. **OpenStreetMap**: Interested in using OSM tiles
6. **Hosting**: Can self-host or embed static output in Squarespace

---

## Revised Recommendation: **Static Leaflet.js with Build Step**

### **Best Solution: Leaflet.js + Static Generation + YAML/CSV Input**

This approach combines the best of all worlds:

1. **Easy input**: Edit YAML or CSV files (human-friendly)
2. **Build step**: Script transforms input → JSON → static HTML
3. **Pin clustering**: Leaflet.markercluster plugin handles overlapping pins
4. **OpenStreetMap**: Leaflet uses OSM tiles by default (free, no API key)
5. **Static output**: Generate once, host anywhere (Squarespace or self-hosted)
6. **Customizable**: Can style map and pins later

### How It Works:

```
books.yaml (or books.csv)
    ↓
[Build Script] → Transforms to JSON + generates HTML
    ↓
index.html (static, self-contained)
    ↓
Upload to Squarespace or self-host
```

### Architecture:

1. **Input File** (YAML or CSV):
   - User edits this file
   - Simple, readable format
   - No JSON syntax to worry about

2. **Build Script** (Python/Node.js):
   - Reads YAML/CSV
   - Geocodes locations (if needed)
   - Generates static HTML with embedded data
   - Runs only when updating books

3. **Output** (Static HTML):
   - Self-contained HTML file
   - Includes Leaflet.js + clustering plugin
   - Uses OpenStreetMap tiles
   - All data embedded (or can load from JSON)
   - Upload to Squarespace or host anywhere

### Pros:
- ✅ **Easy maintenance**: Edit YAML/CSV (much easier than JSON)
- ✅ **Pin clustering**: Automatic handling of overlapping locations
- ✅ **Static output**: Fast, no server needed, works anywhere
- ✅ **OpenStreetMap**: Free, no API keys, open source
- ✅ **Customizable**: Can style map and markers later
- ✅ **Self-contained**: Single HTML file or simple folder structure
- ✅ **Squarespace-friendly**: Can upload HTML or embed via iframe

### Cons:
- ❌ **Build step required**: Need to run script when updating (but can automate)
- ❌ **Geocoding**: May need to convert city names to lat/lng (one-time or script handles it)

### Pin Clustering Solution:
- Use **Leaflet.markercluster** plugin
- Automatically groups nearby pins
- Shows count when zoomed out
- Expands to individual pins when zoomed in
- Handles multiple books in same city elegantly

### Input Format Examples:

**YAML format** (recommended - easiest to read/edit):
```yaml
books:
  - title: "The Paris Wife"
    locations:
      - name: "Paris, France"
    cover: "https://example.com/covers/paris-wife.jpg"
    review: "https://site.com/reviews/paris-wife"
  
  - title: "The Kite Runner"
    locations:
      - name: "Kabul, Afghanistan"
    cover: "https://example.com/covers/kite-runner.jpg"
    review: "https://site.com/reviews/kite-runner"
  
  - title: "A Moveable Feast"
    locations:
      - name: "Paris, France"  # Will cluster with "The Paris Wife"
    cover: "https://example.com/covers/moveable-feast.jpg"
    review: "https://site.com/reviews/moveable-feast"
```

**CSV format** (alternative):
```csv
title,location,cover_url,review_url
The Paris Wife,Paris France,https://...,https://...
The Kite Runner,Kabul Afghanistan,https://...,https://...
A Moveable Feast,Paris France,https://...,https://...
```

### Workflow:

1. **Initial setup** (one time):
   - Create build script
   - Set up input file template
   - Configure map styling (optional)

2. **Adding a book**:
   - Add entry to YAML/CSV file
   - Run build script: `python build.py` or `npm run build`
   - Upload generated HTML to Squarespace or hosting
   - Done!

3. **Future customization**:
   - Edit CSS for map styling
   - Change marker icons
   - Adjust clustering settings
   - All in the build script/config

---

## Alternative: Pure Static with Manual Geocoding

If you want to avoid geocoding entirely, you can manually specify coordinates:

**YAML with coordinates**:
```yaml
books:
  - title: "The Paris Wife"
    locations:
      - name: "Paris, France"
        lat: 48.8566
        lng: 2.3522
```

This eliminates the need for geocoding but requires looking up coordinates (or the build script can do it once and save them).

---

## Implementation Details

### Build Script Options

**Option A: Python Script**
- Use `pyyaml` or `pandas` to read YAML/CSV
- Use geocoding library (e.g., `geopy` with Nominatim - free, no API key)
- Generate HTML with embedded JSON data
- Simple to run: `python build.py`

**Option B: Node.js Script**
- Use `js-yaml` or `csv-parser` to read input
- Use geocoding library (e.g., `node-geocoder` with OpenStreetMap)
- Generate HTML with embedded JSON data
- Simple to run: `npm run build`

**Option C: GitHub Actions / CI**
- Automate build on file changes
- Push to hosting automatically
- Zero manual steps after initial setup

### Geocoding Strategy

**Free Options (no API key needed):**
- **Nominatim** (OpenStreetMap geocoding) - Free, rate-limited but fine for occasional use
- **Manual entry** - Look up coordinates once, save in file
- **Cached geocoding** - Build script remembers previous lookups

**Recommended**: Use Nominatim with caching - first time it looks up coordinates, saves them in the file, future builds are instant.

### Output Structure

```
bookmap/
├── books.yaml          # Input file
├── build.py            # Build script
├── index.html          # Generated static HTML
└── assets/             # Optional: CSS, custom markers, etc.
```

Or for Squarespace:
- Generate `index.html`
- Upload to Squarespace file storage
- Embed via iframe or code block

---

## Next Steps

### Recommended Path Forward:

1. **Build a prototype** with:
   - YAML input file format
   - Python or Node.js build script
   - Leaflet.js with marker clustering
   - OpenStreetMap tiles
   - Static HTML output

2. **Test the workflow**:
   - Add a few sample books
   - Run build script
   - Verify clustering works for duplicate locations
   - Test embedding in Squarespace

3. **Create documentation**:
   - Simple guide for adding/editing books
   - How to run the build script
   - How to upload/embed in Squarespace

4. **Future enhancements** (can add later):
   - Custom map styling
   - Custom marker icons (book covers as markers?)
   - Filtering by genre/year
   - Popup styling with book covers

### Questions to Decide:

1. **Input format preference**: YAML, CSV, or Markdown?
2. **Build script language**: Python or Node.js? (Python might be easier if you're familiar)
3. **Geocoding**: Auto-geocode from city names, or manually enter coordinates?
4. **Hosting**: Squarespace file storage, or self-hosted?

I can build the complete solution once you confirm preferences, or I can build a flexible version that supports multiple input formats.

