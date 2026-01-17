#!/usr/bin/env python3
"""
Enrich sparse entries in books.yaml by fetching metadata from Google Books API and Wikipedia.

Usage:
  python3 enrich_books.py                     # Interactive mode (asks per book)
  python3 enrich_books.py --yes               # Auto-approve all changes
  python3 enrich_books.py --dry-run           # Preview changes without writing
  python3 enrich_books.py --locations         # Also lookup locations from Wikipedia
  python3 enrich_books.py --locations --yes   # Auto-approve location changes
  python3 enrich_books.py --book-title "Title" --locations  # Test specific book
"""

import argparse
import sys
import urllib.request
import urllib.parse
import json
import re
from pathlib import Path
from ruamel.yaml import YAML

# Fields we can enrich
ENRICHABLE_FIELDS = ['isbn', 'author', 'year', 'genre', 'cover']

def fetch_google_books_by_isbn(isbn):
    """Fetch book metadata from Google Books API using ISBN."""
    clean_isbn = isbn.replace('-', '').replace(' ', '')
    url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}'
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        if data.get('totalItems', 0) > 0:
            return data['items'][0]['volumeInfo']
    except Exception as e:
        print(f"  Error fetching by ISBN: {e}")
    
    return None

def fetch_google_books_by_title_author(title, author=None):
    """Fetch book metadata from Google Books API using title and author."""
    query = f'intitle:{title}'
    if author:
        query += f'+inauthor:{author}'
    
    url = f'https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}'
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        if data.get('totalItems', 0) > 0:
            return data['items'][0]['volumeInfo']
    except Exception as e:
        print(f"  Error fetching by title/author: {e}")
    
    return None

def extract_metadata(volume_info):
    """Extract relevant fields from Google Books volume info."""
    metadata = {}
    
    # ISBN
    if 'industryIdentifiers' in volume_info:
        for identifier in volume_info['industryIdentifiers']:
            if identifier['type'] in ['ISBN_13', 'ISBN_10']:
                metadata['isbn'] = identifier['identifier']
                break
    
    # Author (first author if multiple)
    if 'authors' in volume_info and volume_info['authors']:
        if len(volume_info['authors']) == 1:
            metadata['author'] = volume_info['authors'][0]
        else:
            # Join multiple authors
            metadata['author'] = ' and '.join(volume_info['authors'])
    
    # Year (from publishedDate)
    if 'publishedDate' in volume_info:
        year_str = volume_info['publishedDate'].split('-')[0]
        try:
            metadata['year'] = int(year_str)
        except ValueError:
            pass
    
    # Genre (from categories - take first one)
    if 'categories' in volume_info and volume_info['categories']:
        category = volume_info['categories'][0]
        # Simplify common categories
        if 'Fiction' in category:
            if 'Historical' in category:
                metadata['genre'] = 'Historical Fiction'
            elif 'Science' in category:
                metadata['genre'] = 'Science Fiction'
            elif 'Young Adult' in category:
                metadata['genre'] = 'Young Adult Fiction'
            else:
                metadata['genre'] = 'Fiction'
        elif 'Biography' in category or 'Memoir' in category:
            metadata['genre'] = 'Biography'
        elif 'History' in category:
            metadata['genre'] = 'History'
        elif 'Mystery' in category or 'Thriller' in category:
            metadata['genre'] = 'Mystery'
        else:
            metadata['genre'] = category
    
    # Cover URL
    if 'imageLinks' in volume_info:
        # Prefer higher resolution images
        if 'thumbnail' in volume_info['imageLinks']:
            cover_url = volume_info['imageLinks']['thumbnail']
            # Try to get higher resolution by modifying zoom parameter
            cover_url = cover_url.replace('zoom=1', 'zoom=0')
            metadata['cover'] = cover_url
    
    return metadata

def fetch_wikipedia_data(title, author=None):
    """Fetch Wikipedia article data for a book."""
    # Try variations of the title
    search_titles = [
        f"{title} (novel)",
        f"{title} (book)",
        title
    ]
    
    for search_title in search_titles:
        url = f'https://en.wikipedia.org/w/api.php?action=query&format=json&titles={urllib.parse.quote(search_title)}&prop=extracts&exintro=1&explaintext=1'
        
        try:
            # Wikipedia requires a User-Agent header
            req = urllib.request.Request(url, headers={
                'User-Agent': 'BookMapEnricher/1.0 (Educational Project)'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if page_id != '-1' and 'extract' in page_data:
                    # Found a valid page
                    return page_data['extract']
        except Exception as e:
            continue
    
    return None

def extract_locations_from_text(text):
    """Extract location mentions from Wikipedia text."""
    if not text:
        return []
    
    locations = []
    
    # Pattern to extract location phrases from common setting descriptions
    setting_patterns = [
        r'set in ([^.]+?)(?:\.|,| and | in the)',
        r'takes? place in ([^.]+?)(?:\.|,| and | in the)',
        r'located in ([^.]+?)(?:\.|,| and )',
        r'story (?:is )?set in ([^.]+?)(?:\.|,| and )',
        r'(?:novel|book|story) (?:is )?set in ([^.]+?)(?:\.|,| and )',
        r'centers? (?:around|on) [^.]*?(?:in|from) ([^.]+?)(?:\.|,| that | and )',
        r'story of [^.]*?(?:in|from) ([^.]+?)(?:\.|,| after | who | before | and )',
    ]
    
    for pattern in setting_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            location_text = match.group(1).strip()
            # Clean up the location text
            location_text = re.sub(r'\s+', ' ', location_text)
            
            # Remove temporal phrases (e.g., "over ten days", "in three weeks")
            location_text = re.sub(r'\s+(?:over|in|during|for)\s+\w+\s+(?:days|weeks|months|years)', '', location_text, flags=re.IGNORECASE)
            
            # Remove time periods from the start (e.g., "1960s Southern California" -> "Southern California")
            location_text = re.sub(r'^\d{4}s?\s+', '', location_text)
            location_text = re.sub(r'^(early|mid|late)[\s-]\d{4}s?\s+', '', location_text, flags=re.IGNORECASE)
            location_text = re.sub(r'^(fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second)[\s-]century\s+', '', location_text, flags=re.IGNORECASE)
            
            # Handle journey/route patterns (e.g., "from Nebraska to New York City" -> ["Nebraska", "New York City"])
            journey_match = re.search(r'(?:from\s+)?([A-Z][a-zA-Z\s]+?)\s+to\s+([A-Z][a-zA-Z\s]+?)$', location_text.strip())
            if journey_match:
                # Extract both start and end locations
                start_loc = journey_match.group(1).strip()
                end_loc = journey_match.group(2).strip()
                if 3 < len(start_loc) < 100:
                    locations.append(start_loc)
                if 3 < len(end_loc) < 100:
                    locations.append(end_loc)
                continue
            
            # Split on "and" to separate multiple locations
            for loc in re.split(r' and | & ', location_text):
                loc = loc.strip().strip(',')
                # Skip very long or very short matches
                if 3 < len(loc) < 100 and not loc.lower().startswith('the '):
                    locations.append(loc)
    
    # Look for specific place name patterns
    place_patterns = [
        # Time period + place: "fifteenth-century Constantinople" -> extract just "Constantinople"
        r'\b(?:fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty-first|twenty-second)-century\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        # Present-day place: "present-day Idaho" -> extract just "Idaho"
        r'\bpresent-day\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        # City, State/Country: "Paris, France"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    
    for pattern in place_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            if len(match.groups()) == 2:
                # For City, Country combine them
                loc = f"{match.group(1)}, {match.group(2)}"
            else:
                # For time-period or present-day patterns, extract just the place
                loc = match.group(1)
            if loc and 3 < len(loc) < 100:
                locations.append(loc.strip())
    
    # Remove duplicates and filter out non-locations
    seen = set()
    unique_locations = []
    for loc in locations:
        loc_lower = loc.lower()
        loc_clean = loc.strip()
        
        # Skip if it's just a year (e.g., "1954", "1960s")
        if re.match(r'^\d{4}s?$', loc_clean):
            continue
        
        # Skip common non-location phrases
        skip_phrases = ['the united states', 'the united kingdom', 'the novel', 'the book', 'the story']
        if loc_lower in skip_phrases or loc_lower in seen:
            continue
        
        # Skip very generic or too long phrases
        if len(loc_clean) < 3 or len(loc_clean) > 100:
            continue
        
        seen.add(loc_lower)
        unique_locations.append(loc_clean)
    
    return unique_locations[:5]  # Limit to 5 most relevant locations

def get_wikipedia_locations(book):
    """Fetch location data from Wikipedia for a book."""
    title = book.get('title', '')
    author = book.get('author', '')
    
    print(f"  Searching Wikipedia for: {title}")
    
    wiki_text = fetch_wikipedia_data(title, author)
    if not wiki_text:
        print(f"  No Wikipedia article found")
        return None
    
    locations = extract_locations_from_text(wiki_text)
    
    if locations:
        print(f"  Found locations: {', '.join(locations)}")
        return locations
    else:
        print(f"  No locations extracted from Wikipedia")
        return None

def get_enrichment_for_book(book):
    """Fetch enrichment data for a book entry."""
    title = book.get('title', 'Unknown')
    
    # Try fetching by ISBN first if available
    if book.get('isbn'):
        print(f"  Fetching by ISBN: {book['isbn']}")
        volume_info = fetch_google_books_by_isbn(book['isbn'])
        if volume_info:
            return extract_metadata(volume_info)
    
    # Fallback to title/author search
    author = book.get('author')
    print(f"  Fetching by title/author: {title}" + (f" by {author}" if author else ""))
    volume_info = fetch_google_books_by_title_author(title, author)
    if volume_info:
        return extract_metadata(volume_info)
    
    return None

def identify_missing_fields(book):
    """Identify which fields are missing or could be enriched."""
    missing = []
    for field in ENRICHABLE_FIELDS:
        if field not in book or not book[field]:
            missing.append(field)
    return missing

def display_changes(book, enrichment, missing_fields):
    """Display what changes would be made to a book entry."""
    title = book.get('title', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"Book: {title}")
    print(f"Missing fields: {', '.join(missing_fields) if missing_fields else 'None'}")
    print(f"{'='*60}")
    
    changes = []
    # Only show changes for fields that are actually missing
    for field in missing_fields:
        if field in enrichment:
            changes.append((field, enrichment[field]))
    
    if not changes:
        print("No enrichment data available for missing fields.")
        return False
    
    for field, value in changes:
        print(f"  {field}: {value} (NEW)")
    
    return True

def apply_enrichment(book, enrichment):
    """Apply enrichment data to book entry (only fills missing fields)."""
    applied = []
    for field, value in enrichment.items():
        if field in ENRICHABLE_FIELDS:
            if not book.get(field):
                book[field] = value
                applied.append(field)
    return applied

def main():
    parser = argparse.ArgumentParser(
        description='Enrich sparse entries in books.yaml with metadata from Google Books API and Wikipedia'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to file'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-approve all changes without confirmation'
    )
    parser.add_argument(
        '--locations',
        action='store_true',
        help='Also look up location/setting data from Wikipedia'
    )
    parser.add_argument(
        '--all-locations',
        action='store_true',
        help='Look up locations for ALL books, not just those with generic locations'
    )
    parser.add_argument(
        '--book-title',
        type=str,
        help='Process only a specific book by title (for testing)'
    )
    
    args = parser.parse_args()
    
    books_file = Path('books.yaml')
    if not books_file.exists():
        print(f"Error: {books_file} not found")
        sys.exit(1)
    
    # Use ruamel.yaml to preserve formatting and comments
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096  # Prevent line wrapping
    
    # Load books.yaml
    print(f"Loading {books_file}...")
    with open(books_file, 'r') as f:
        data = yaml.load(f)
    
    books = data.get('books', [])
    print(f"Found {len(books)} books")
    
    # Find books with missing fields
    sparse_books = []
    for i, book in enumerate(books):
        missing = identify_missing_fields(book)
        if missing:
            sparse_books.append((i, book, missing))
    
    if not sparse_books:
        print("\nNo sparse entries found. All books are complete!")
        return
    
    print(f"\nFound {len(sparse_books)} books with missing fields")
    
    if args.dry_run:
        print("\n[DRY RUN MODE - No changes will be written]")
    
    # Process each sparse book
    enriched_count = 0
    skipped_count = 0
    location_enriched_count = 0
    
    for idx, book, missing_fields in sparse_books:
        title = book.get('title', 'Unknown')
        
        print(f"\n[{idx + 1}/{len(books)}] Processing: {title}")
        
        # Fetch enrichment data
        enrichment = get_enrichment_for_book(book)
        
        if not enrichment:
            print("  Could not find metadata for this book")
            skipped_count += 1
            continue
        
        # Display proposed changes
        has_changes = display_changes(book, enrichment, missing_fields)
        
        if not has_changes:
            skipped_count += 1
            continue
        
        # Ask for confirmation (unless --yes flag)
        if not args.yes and not args.dry_run:
            response = input("\nApply these changes? [y/N/q]: ").strip().lower()
            if response == 'q':
                print("\nQuitting...")
                break
            if response != 'y':
                print("Skipped.")
                skipped_count += 1
                continue
        
        # Apply changes (unless dry run)
        if not args.dry_run:
            applied = apply_enrichment(book, enrichment)
            if applied:
                enriched_count += 1
                print(f"✓ Applied changes to fields: {', '.join(applied)}")
        else:
            enriched_count += 1
    
    # Additional pass for location enrichment if requested
    if args.locations:
        print("\n" + "="*60)
        print("LOCATION ENRICHMENT PHASE")
        print("="*60)
        
        # Find books that need location data
        books_needing_locations = []
        generic_locations = ['United States', 'USA', 'United Kingdom', 'UK', 'England', 'Germany', 'France', 'China', 'Russia']
        
        for i, book in enumerate(books):
            # Filter by title if specified
            if args.book_title and book.get('title', '') != args.book_title:
                continue
            
            locations = book.get('locations', [])
            
            if args.all_locations:
                # Check all books
                books_needing_locations.append((i, book))
            elif not locations:
                # No locations at all
                books_needing_locations.append((i, book))
            elif any(loc.get('name', '').strip() in generic_locations for loc in locations):
                # Has only generic locations
                books_needing_locations.append((i, book))
        
        if args.book_title:
            print(f"\nProcessing single book: {args.book_title}")
        else:
            print(f"\nFound {len(books_needing_locations)} books that could use more specific location data")
        
        for idx, book in books_needing_locations:
            title = book.get('title', 'Unknown')
            print(f"\n[{idx + 1}/{len(books)}] Processing locations for: {title}")
            
            # Get Wikipedia locations
            wiki_locations = get_wikipedia_locations(book)
            
            if wiki_locations:
                print(f"\nProposed locations to add:")
                for loc in wiki_locations:
                    print(f"  - {loc}")
                
                # Ask for confirmation (unless --yes flag)
                if not args.yes and not args.dry_run:
                    response = input("\nAdd these locations? [y/N/q]: ").strip().lower()
                    if response == 'q':
                        print("\nQuitting location enrichment...")
                        break
                    if response != 'y':
                        print("Skipped.")
                        continue
                
                # Apply location changes (unless dry run)
                if not args.dry_run:
                    # Initialize locations array if it doesn't exist
                    if 'locations' not in book:
                        book['locations'] = []
                    
                    # Add new locations (avoid duplicates)
                    existing_names = {loc.get('name', '').lower() for loc in book.get('locations', [])}
                    added = []
                    for loc_name in wiki_locations:
                        if loc_name.lower() not in existing_names:
                            book['locations'].append({'name': loc_name})
                            added.append(loc_name)
                    
                    if added:
                        location_enriched_count += 1
                        print(f"✓ Added locations: {', '.join(added)}")
                else:
                    location_enriched_count += 1
    
    # Write back to file (unless dry run)
    total_changes = enriched_count + location_enriched_count
    if not args.dry_run and total_changes > 0:
        print(f"\nWriting changes to {books_file}...")
        with open(books_file, 'w') as f:
            yaml.dump(data, f)
        print(f"✓ Successfully enriched {enriched_count} books with metadata")
        if args.locations and location_enriched_count > 0:
            print(f"✓ Successfully added locations to {location_enriched_count} books")
    else:
        print(f"\n[DRY RUN] Would have enriched {enriched_count} books with metadata")
        if args.locations and location_enriched_count > 0:
            print(f"[DRY RUN] Would have added locations to {location_enriched_count} books")
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} books")

if __name__ == '__main__':
    main()
