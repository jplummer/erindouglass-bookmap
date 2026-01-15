# Book Location Map

An interactive map showing where reviewed books are set, generated from a simple YAML file.

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

Or install individually:
```bash
pip3 install pyyaml geopy
```

### 2. Add Your Books

Edit `books.yaml` and add your books with their locations (see [Adding Books](#adding-books) section below for details).

### 3. Build the Map

```bash
python3 build.py
```

This will:
- Read `books.yaml`
- Geocode any locations that don't have coordinates
- Cache geocoding results for future builds
- Generate **two HTML files**:
  - `output/index.html` - Clean production version (for Squarespace)
  - `output/preview.html` - Preview with style chooser panel

### 4. Preview & Test Styles

**Before embedding in Squarespace, preview the map locally:**

**To test different map styles:**
```bash
open output/preview.html
```
This opens the preview version with a style chooser panel in the top-right corner. Try out 8 different map styles:
- CartoDB: Positron (default), Voyager, Dark Matter
- OpenStreetMap: Standard, Humanitarian
- Stamen: Terrain, Toner, Watercolor

**To preview the production version (what users will see):**
```bash
open output/index.html
```
This is the clean version with no style chooser (identical to what will appear on Squarespace).

**Using a local server (recommended for testing):**
```bash
cd output
python3 -m http.server 8000
```
Then open:
- `http://localhost:8000/preview.html` - test styles
- `http://localhost:8000/index.html` - see production version

### 5. Deploy

Upload the `output` folder to your hosting or Squarespace site. See `SQUARESPACE_GUIDE.md` for detailed embedding instructions.

---

## Adding Books

### Basic Format

Each book needs at least a title and one location:

```yaml
books:
  - title: "Book Title"
    locations:
      - name: "City, Country"
```

### Complete Example

Here's a book with all available fields:

```yaml
books:
  - title: "The Paris Wife"
    author: "Paula McLain"
    locations:
      - name: "Paris, France"
      - name: "Brest, France"
    cover: "https://example.com/covers/paris-wife.jpg"
    review: "https://example.com/reviews/paris-wife"
    year: 2011
    genre: "Historical Fiction"
```

### Field Reference

**Required Fields:**
- **`title`**: The book's title
- **`locations`**: At least one location where the book is set
  - **`name`**: Location name (e.g., "Paris, France")
  - **`lat`** and **`lng`**: Optional coordinates (if you know them)

**Optional Fields:**
- **`author`**: Author's name
- **`cover`**: URL to book cover image
- **`review`**: URL to your review of the book
- **`year`**: Publication year
- **`genre`**: Book genre

### Adding a New Book

1. Open `books.yaml` in any text editor
2. Add a new entry under `books:`
3. Use the format shown above
4. Save the file
5. Run `python3 build.py` to regenerate the map

### Multiple Locations

If a book is set in multiple places, list them all:

```yaml
- title: "The Kite Runner"
  locations:
    - name: "Kabul, Afghanistan"
    - name: "Fremont, California, USA"
```

### Using Coordinates

If you know the exact coordinates, you can include them to skip geocoding:

```yaml
- title: "A Moveable Feast"
  locations:
    - name: "Paris, France"
      lat: 48.8566
      lng: 2.3522
```

### Tips

**Location Names:**
- Be specific: "Paris, France" is better than just "Paris"
- Include country for clarity
- Use standard place names for best geocoding results

**Book Covers:**
- Use full URLs (starting with `http://` or `https://`)
- Images should be publicly accessible
- Recommended size: 200-300px wide

**Review Links:**
- Use full URLs to your review pages
- Links open in a new tab when clicked on the map

### After Making Changes

1. Save `books.yaml`
2. Run the build script: `python3 build.py`
3. Check `output/index.html` in your browser
4. Upload the updated file to your website

---

## File Structure

```
.
├── books.yaml          # Input file - edit this to add books
├── build.py            # Build script
├── requirements.txt    # Python dependencies
├── cache/
│   └── geocoding.json  # Cached coordinates (auto-generated)
└── output/
    └── index.html      # Generated map (upload this)
```

---

## How It Works

1. **Input**: Edit `books.yaml` with book information
2. **Geocoding**: The script converts location names to coordinates using OpenStreetMap's Nominatim service
3. **Caching**: Coordinates are cached so future builds are faster
4. **Generation**: Creates a static HTML file with Leaflet.js map
5. **Clustering**: Multiple books in the same city automatically cluster together

---

## Features

- ✅ Easy YAML input format
- ✅ Automatic geocoding (or use manual coordinates)
- ✅ Individual pins with smart offset for duplicate locations
- ✅ Off-screen indicators showing count and direction of hidden pins
- ✅ Book covers and review links in popups
- ✅ Static HTML output (no server needed)
- ✅ 8 map styles to choose from (Positron, Voyager, Dark Matter, OSM, Humanitarian, Terrain, Toner, Watercolor)
- ✅ Dual output: clean production file + preview with style chooser
- ✅ Responsive design

---

## Troubleshooting

### Location Not Found

If a location can't be geocoded:
- Try being more specific: "Paris, France" instead of "Paris"
- Check spelling
- Add coordinates manually in the YAML:
  ```yaml
  locations:
    - name: "Paris, France"
      lat: 48.8566
      lng: 2.3522
  ```

### Multiple Books in Same City

This is handled automatically! The map will cluster markers together. When you zoom in, they'll separate. When you click a cluster, it will expand to show all books.

### Rate Limiting

Nominatim (the geocoding service) has a rate limit of 1 request per second. The script handles this automatically, but if you're adding many books at once, the first build may take a while. Subsequent builds use cached coordinates and are much faster.

---

## Customization

The map styling is embedded in the generated HTML. To customize:
1. Edit the CSS in `build.py` (in the `generate_html` function)
2. Or create `static/css/map.css` and it will be included automatically

---

## License

Free to use and modify.
