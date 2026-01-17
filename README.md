# Book Location Map

An interactive map showing where books are set, generated from a YAML file.

## Quick Start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Edit books.yaml to add your books

# 3. Build the map
python3 build.py

# 4. Preview locally
open output/preview.html  # or output/index.html
```

Generates two files:
- `output/index.html` - Clean production version
- `output/preview.html` - Preview with style chooser panel

See `docs/squarespace_guide.md` for embedding instructions.

---

## Adding Books

### Minimal Example

```yaml
books:
  - title: "Book Title"
    locations:
      - name: "Paris, France"
```

### Full Example

```yaml
books:
  - title: "The Paris Wife"
    author: "Paula McLain"
    isbn: "9780345521309"
    year: 2011
    genre: "Historical Fiction"
    review: "https://example.com/reviews/paris-wife"
    locations:
      - name: "Paris, France"
      - name: "Brest, France"
        lat: 48.3904  # optional coordinates
        lng: -4.4861
```

**Required:** `title`, `locations` (with `name`)  
**Optional:** `author`, `isbn`, `year`, `genre`, `cover`, `review`

**Tips:**
- Be specific with locations: "Paris, France" not "Paris"
- ISBNs auto-generate book covers from Google Books
- Add explicit `cover: "https://..."` URL to override auto-generated covers

---

## Customizing Appearance

Set defaults at the top of `books.yaml`:

```yaml
default_style: watercolor        # Map style
default_pin_style: burgundy_circle  # Pin style

books:
  - title: "Your Book"
    # ...
```

**Map styles:** `positron`, `voyager`, `dark`, `watercolor`, `terrain`, `toner`, `osm`, `humanitarian`, and 18 more (see preview.html)  
**Pin styles:** `burgundy_circle`, `default`, `black_circle`, `small_burgundy_pin`, `small_orange_pin`, `pushpin_emoji`

Use `output/preview.html` to test different combinations visually. Once you've chosen your preferred style, update `books.yaml` with your choices and run `python3 build.py` to regenerate the production map.

---

## Utility Scripts

### Auto-fill Book Metadata

Use `enrich_books.py` to fetch missing metadata (year, genre, cover, etc.) from Google Books API:

```bash
python3 enrich_books.py --dry-run  # preview changes
python3 enrich_books.py            # interactive (asks per book)
python3 enrich_books.py --yes      # auto-approve all
```

Requires ISBNs in `books.yaml` for best results.

### Lookup Book Locations from Wikipedia

Add the `--locations` flag to also search Wikipedia for more specific setting information:

```bash
python3 enrich_books.py --locations --dry-run  # preview location suggestions
python3 enrich_books.py --locations --yes      # auto-approve all
```

This will:
- Search Wikipedia articles for books that only have generic locations (e.g., "United States")
- Extract specific setting details from article text (e.g., "1960s Southern California")
- Suggest adding these more specific locations to your data

Options:
- `--all-locations` - Check all books, not just those with generic locations
- `--book-title "Title"` - Test with a specific book

---

## Troubleshooting

**Location not found:** Be more specific ("Paris, France" not "Paris") or add coordinates manually:
```yaml
locations:
  - name: "Paris, France"
    lat: 48.8566
    lng: 2.3522
```

**Rate limiting:** First build with many new locations may be slow due to geocoding limits. Subsequent builds use cached coordinates.

**Multiple books in same city:** Automatically handled with clustering.

---

## File Structure

```
.
├── books.yaml            # Input file
├── build.py              # Build script
├── enrich_books.py       # Metadata enrichment utility
├── cache/
│   └── geocoding.json    # Cached coordinates
└── output/
    ├── index.html        # Production map
    └── preview.html      # Preview with controls
```

---

## How It Works

1. Edit `books.yaml` with book data
2. Script geocodes locations (cached for speed)
3. Generates static HTML with Leaflet.js
4. Upload `output` folder to hosting

**Features:** Automatic geocoding, marker clustering, multiple map/pin styles, book covers, review links, responsive design.

---

## License

Free to use and modify.
