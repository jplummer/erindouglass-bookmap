#!/usr/bin/env python3
"""
Enrich sparse entries in books.yaml by fetching metadata from Google Books API.

Usage:
  python3 enrich_books.py              # Interactive mode (asks per book)
  python3 enrich_books.py --yes        # Auto-approve all changes
  python3 enrich_books.py --dry-run    # Preview changes without writing
"""

import argparse
import sys
import urllib.request
import urllib.parse
import json
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
        description='Enrich sparse entries in books.yaml with metadata from Google Books API'
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
    
    # Write back to file (unless dry run)
    if not args.dry_run and enriched_count > 0:
        print(f"\nWriting changes to {books_file}...")
        with open(books_file, 'w') as f:
            yaml.dump(data, f)
        print(f"✓ Successfully enriched {enriched_count} books")
    else:
        print(f"\n[DRY RUN] Would have enriched {enriched_count} books")
    
    if skipped_count > 0:
        print(f"Skipped {skipped_count} books")

if __name__ == '__main__':
    main()
