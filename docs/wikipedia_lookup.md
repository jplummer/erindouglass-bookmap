# Wikipedia Location Lookup

## Overview

The enrichment script now includes Wikipedia lookup to find more specific book settings/locations.

## How It Works

1. **Searches Wikipedia** for book articles using variations of the title:
   - "Book Title (novel)"
   - "Book Title (book)"
   - "Book Title"

2. **Extracts location mentions** from article introductions using pattern matching:
   - Explicit setting descriptions: "set in...", "takes place in..."
   - Story descriptions: "story of...in..."
   - Time-period locations: "fifteenth-century Constantinople"
   - Present-day references: "present-day Idaho"

3. **Suggests locations** for books that:
   - Have no location data
   - Only have generic locations (e.g., "United States", "United Kingdom", "Germany")

## Usage

```bash
# Preview what locations would be found
python3 enrich_books.py --locations --dry-run

# Interactive mode (asks for confirmation per book)
python3 enrich_books.py --locations

# Auto-approve all location changes
python3 enrich_books.py --locations --yes

# Check ALL books, even those with specific locations
python3 enrich_books.py --locations --all-locations --dry-run

# Test with a specific book
python3 enrich_books.py --locations --book-title "Cloud Cuckoo Land" --dry-run
```

## Example Results

### Lessons in Chemistry
- **Before:** `locations: - name: United States`
- **Wikipedia found:** "1960s Southern California"
- **Result:** More specific setting information

### The Lincoln Highway
- **Before:** `locations: - name: United States`
- **Wikipedia found:** "Nebraska to New York City over ten days"
- **Result:** Route/journey details

### Cloud Cuckoo Land
- **Wikipedia found:** "Constantinople", "Idaho"
- **Result:** Confirms existing locations or finds additional details

## Limitations

1. **Coverage:** Not all books have Wikipedia articles
   - More popular/notable books have better coverage
   - Newer books may not have articles yet

2. **Location mentions:** Not all Wikipedia book articles mention specific settings
   - Depends on how the article is written
   - Introductory paragraphs may not include location details

3. **Extraction accuracy:** Pattern-based extraction may:
   - Miss some location mentions
   - Extract overly verbose phrases
   - Require manual review/cleanup

## Success Rate

In testing with 44 books:
- 13 books had generic locations that needed enrichment
- 2 books successfully enriched with Wikipedia data (~15% success rate)
- Most books either lacked Wikipedia articles or didn't mention specific locations in the intro

## When to Use

Best for:
- Books with only country-level locations (United States, England, etc.)
- Well-known/popular books likely to have Wikipedia articles
- Historical fiction that often has detailed setting information

Less useful for:
- Very new books (2024-2026) without Wikipedia coverage yet
- Books already with specific city-level locations
- Less popular titles without Wikipedia articles

## Future Improvements

Possible enhancements:
- Search full Wikipedia article text, not just intro
- Use Wikipedia's structured data (infoboxes) if available
- Try additional sources (Goodreads, Open Library subject tags)
- Add LLM-based extraction for better accuracy
- Manual review mode to approve/edit suggestions
