#!/usr/bin/env python3
"""
Build script for Book Location Map
Reads books.yaml, geocodes locations, and generates static HTML map
"""

import yaml
import json
import os
import time
import sys
import re
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Configuration
INPUT_FILE = "books.yaml"
OUTPUT_DIR = "output"
CACHE_FILE = "cache/geocoding.json"
TEMPLATE_FILE = "templates/map.html"
CSS_FILE = "static/css/map.css"

# Geocoding rate limit (Nominatim requires max 1 request per second)
GEOCODE_DELAY = 1.1  # Slightly more than 1 second to be safe


def validate_yaml(data):
    """
    Validate YAML structure and data.
    Returns (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    if not isinstance(data, dict):
        errors.append("YAML root must be a dictionary")
        return False, errors, warnings
    
    if 'books' not in data:
        errors.append("Missing required 'books' key in YAML")
        return False, errors, warnings
    
    books = data['books']
    if not isinstance(books, list):
        errors.append("'books' must be a list")
        return False, errors, warnings
    
    if len(books) == 0:
        warnings.append("No books found in YAML file")
        return True, errors, warnings
    
    # Validate each book
    for i, book in enumerate(books):
        if not isinstance(book, dict):
            errors.append(f"Book {i+1}: Must be a dictionary")
            continue
        
        # Required: title
        if 'title' not in book:
            errors.append(f"Book {i+1}: Missing required field 'title'")
        elif not isinstance(book['title'], str) or not book['title'].strip():
            errors.append(f"Book {i+1}: 'title' must be a non-empty string")
        
        # Required: locations
        if 'locations' not in book:
            errors.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): Missing required field 'locations'")
        elif not isinstance(book['locations'], list):
            errors.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'locations' must be a list")
        elif len(book['locations']) == 0:
            errors.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'locations' list cannot be empty")
        else:
            # Validate each location
            for j, loc in enumerate(book['locations']):
                if not isinstance(loc, dict):
                    errors.append(f"Book {i+1}, location {j+1}: Must be a dictionary")
                    continue
                
                if 'name' not in loc:
                    errors.append(f"Book {i+1}, location {j+1}: Missing required field 'name'")
                elif not isinstance(loc['name'], str) or not loc['name'].strip():
                    errors.append(f"Book {i+1}, location {j+1}: 'name' must be a non-empty string")
                
                # Validate coordinates if provided
                if 'lat' in loc:
                    try:
                        lat = float(loc['lat'])
                        if lat < -90 or lat > 90:
                            errors.append(f"Book {i+1}, location {j+1}: 'lat' must be between -90 and 90")
                    except (ValueError, TypeError):
                        errors.append(f"Book {i+1}, location {j+1}: 'lat' must be a number")
                
                if 'lng' in loc:
                    try:
                        lng = float(loc['lng'])
                        if lng < -180 or lng > 180:
                            errors.append(f"Book {i+1}, location {j+1}: 'lng' must be between -180 and 180")
                    except (ValueError, TypeError):
                        errors.append(f"Book {i+1}, location {j+1}: 'lng' must be a number")
        
        # Optional fields validation
        if 'author' in book and not isinstance(book['author'], str):
            warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'author' should be a string")
        
        if 'cover' in book:
            if not isinstance(book['cover'], str):
                warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'cover' should be a string")
            elif book['cover'] and not re.match(r'^https?://', book['cover']):
                warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'cover' should be a full URL (starting with http:// or https://)")
        
        if 'review' in book:
            if not isinstance(book['review'], str):
                warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'review' should be a string")
            elif book['review'] and not re.match(r'^https?://', book['review']):
                warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'review' should be a full URL (starting with http:// or https://)")
        
        if 'year' in book:
            if not isinstance(book['year'], (int, str)):
                warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'year' should be a number or string")
        
        if 'genre' in book and not isinstance(book['genre'], str):
            warnings.append(f"Book {i+1} ('{book.get('title', 'Unknown')}'): 'genre' should be a string")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def load_cache():
    """Load cached geocoding results"""
    cache_path = Path(CACHE_FILE)
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save geocoding results to cache"""
    cache_path = Path(CACHE_FILE)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)


def geocode_location(location_name, cache, geolocator):
    """
    Geocode a location name to coordinates.
    Uses cache if available, otherwise queries Nominatim.
    """
    # Normalize location name for cache key
    cache_key = location_name.lower().strip()
    
    # Check cache first
    if cache_key in cache:
        cached = cache[cache_key]
        return cached['lat'], cached['lng'], cached['name']
    
    # Geocode if not in cache
    print(f"  Geocoding: {location_name}...")
    try:
        time.sleep(GEOCODE_DELAY)  # Rate limiting
        location = geolocator.geocode(location_name, timeout=10)
        
        if location:
            lat, lng = location.latitude, location.longitude
            # Cache the result
            cache[cache_key] = {
                'lat': lat,
                'lng': lng,
                'name': location_name
            }
            return lat, lng, location_name
        else:
            print(f"  Warning: Could not geocode '{location_name}'")
            return None, None, location_name
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"  Error geocoding '{location_name}': {e}")
        return None, None, location_name


def process_books(books_data, cache):
    """Process books data, geocoding locations as needed"""
    geolocator = Nominatim(user_agent="book-location-map")
    processed_books = []
    
    for book in books_data:
        if 'title' not in book:
            print(f"Warning: Skipping book without title: {book}")
            continue
        
        if 'locations' not in book or not book['locations']:
            print(f"Warning: Skipping '{book['title']}' - no locations specified")
            continue
        
        processed_locations = []
        for loc in book['locations']:
            if 'name' not in loc:
                continue
            
            # Use provided coordinates or geocode
            if 'lat' in loc and 'lng' in loc:
                lat, lng = loc['lat'], loc['lng']
                location_name = loc['name']
            else:
                lat, lng, location_name = geocode_location(loc['name'], cache, geolocator)
            
            if lat is not None and lng is not None:
                processed_locations.append({
                    'name': location_name,
                    'lat': lat,
                    'lng': lng
                })
        
        if processed_locations:
            processed_book = {
                'title': book['title'],
                'locations': processed_locations
            }
            
            # Add optional fields
            if 'author' in book:
                processed_book['author'] = book['author']
            if 'cover' in book:
                processed_book['cover'] = book['cover']
            if 'review' in book:
                processed_book['review'] = book['review']
            if 'year' in book:
                processed_book['year'] = book['year']
            if 'genre' in book:
                processed_book['genre'] = book['genre']
            
            processed_books.append(processed_book)
    
    return processed_books


def generate_map_js(books_data):
    """Generate JavaScript code to initialize the map"""
    js = """
    // Initialize map
    const map = L.map('map').setView([20, 0], 2);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Create marker cluster group
    const markers = L.markerClusterGroup({
        chunkedLoading: true,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });
    
    // Book data
    const booksData = """ + json.dumps(books_data, indent=4) + """;
    
    // Create markers for each book location
    const bounds = [];
    
    booksData.forEach(book => {
        book.locations.forEach(location => {
            // Create popup content
            let popupContent = '<div class="book-popup">';
            
            if (book.cover) {
                popupContent += `<img src="${book.cover}" alt="${book.title}" class="book-cover" />`;
            }
            
            popupContent += `<h3>${book.title}</h3>`;
            
            if (book.author) {
                popupContent += `<p class="author">${book.author}</p>`;
            }
            
            popupContent += `<p class="location">📍 ${location.name}</p>`;
            
            if (book.year || book.genre) {
                popupContent += '<p class="meta">';
                if (book.year) popupContent += book.year;
                if (book.year && book.genre) popupContent += ' • ';
                if (book.genre) popupContent += book.genre;
                popupContent += '</p>';
            }
            
            if (book.review) {
                popupContent += `<a href="${book.review}" target="_blank" class="review-link">Read Review →</a>`;
            }
            
            popupContent += '</div>';
            
            // Create marker
            const marker = L.marker([location.lat, location.lng]);
            marker.bindPopup(popupContent);
            markers.addLayer(marker);
            
            bounds.push([location.lat, location.lng]);
        });
    });
    
    // Add markers to map
    map.addLayer(markers);
    
    // Fit map to show all markers
    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
    }
    """
    return js


def generate_html(books_data):
    """Generate the HTML file with embedded map"""
    map_js = generate_map_js(books_data)
    
    # Read CSS if it exists
    css_content = ""
    css_path = Path(CSS_FILE)
    if css_path.exists():
        with open(css_path, 'r') as f:
            css_content = f.read()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Locations Map</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    
    <!-- Custom CSS -->
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        
        #map {{
            width: 100%;
            height: 100vh;
        }}
        
        .book-popup {{
            min-width: 200px;
            max-width: 300px;
        }}
        
        .book-popup .book-cover {{
            width: 100%;
            max-width: 150px;
            height: auto;
            display: block;
            margin: 0 auto 10px;
            border-radius: 4px;
        }}
        
        .book-popup h3 {{
            font-size: 16px;
            margin-bottom: 5px;
            color: #333;
        }}
        
        .book-popup .author {{
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            font-style: italic;
        }}
        
        .book-popup .location {{
            font-size: 13px;
            color: #555;
            margin-bottom: 5px;
        }}
        
        .book-popup .meta {{
            font-size: 12px;
            color: #888;
            margin-bottom: 10px;
        }}
        
        .book-popup .review-link {{
            display: inline-block;
            padding: 6px 12px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 13px;
            margin-top: 5px;
        }}
        
        .book-popup .review-link:hover {{
            background-color: #0056b3;
        }}
        
        {css_content}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    
    <!-- Map initialization -->
    <script>
{map_js}
    </script>
</body>
</html>"""
    
    return html


def main():
    """Main build function"""
    print("Building book location map...")
    
    # Load books data
    print(f"Loading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML syntax in {INPUT_FILE}")
        print(f"   {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {INPUT_FILE}")
        sys.exit(1)
    
    # Validate YAML structure and data
    print("Validating YAML structure...")
    is_valid, errors, warnings = validate_yaml(data)
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not is_valid:
        print(f"\n❌ Validation failed ({len(errors)} errors):")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease fix the errors above and try again.")
        sys.exit(1)
    
    if is_valid and not warnings:
        print("✓ YAML validation passed")
    elif is_valid:
        print(f"✓ YAML validation passed (with {len(warnings)} warnings)")
    
    books = data['books']
    print(f"Found {len(books)} books")
    
    # Load cache
    cache = load_cache()
    print(f"Loaded {len(cache)} cached locations")
    
    # Process books (geocode locations)
    print("Processing books and geocoding locations...")
    processed_books = process_books(books, cache)
    
    # Save cache
    save_cache(cache)
    print(f"Cached {len(cache)} locations")
    
    # Generate HTML
    print("Generating HTML...")
    html = generate_html(processed_books)
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write HTML file
    output_file = output_path / "index.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated {output_file}")
    print(f"✓ Map contains {len(processed_books)} books")
    
    # Summary statistics
    total_locations = sum(len(book['locations']) for book in processed_books)
    books_with_covers = sum(1 for book in processed_books if 'cover' in book and book['cover'])
    books_with_reviews = sum(1 for book in processed_books if 'review' in book and book['review'])
    
    print(f"\n📊 Summary:")
    print(f"   - Books: {len(processed_books)}")
    print(f"   - Total locations: {total_locations}")
    print(f"   - Books with covers: {books_with_covers}")
    print(f"   - Books with reviews: {books_with_reviews}")
    
    print("\nNext steps:")
    print(f"  1. Open {output_file} in a browser to preview")
    print("  2. Upload the output folder to your hosting/Squarespace")


if __name__ == "__main__":
    main()

