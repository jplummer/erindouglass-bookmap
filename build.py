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

# Try to import API key from config file
try:
    from config import STADIA_API_KEY
except ImportError:
    STADIA_API_KEY = os.getenv('STADIA_API_KEY', '')
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
            
            # Handle cover image: explicit cover URL or auto-generate from ISBN
            if 'cover' in book and book['cover']:
                # Check if it's a local file path (starts with "covers/")
                if book['cover'].startswith('covers/'):
                    # Convert to Google Books static link using ISBN
                    if 'isbn' in book and book['isbn']:
                        processed_book['cover'] = f"https://books.google.com/books?vid=ISBN{book['isbn']}&printsec=frontcover&img=1&zoom=1"
                    else:
                        processed_book['cover'] = book['cover']
                else:
                    # Use explicit URL as-is
                    processed_book['cover'] = book['cover']
            elif 'isbn' in book and book['isbn']:
                # Auto-generate cover URL from ISBN using Google Books static link
                processed_book['cover'] = f"https://books.google.com/books?vid=ISBN{book['isbn']}&printsec=frontcover&img=1&zoom=1"
            
            if 'review' in book:
                processed_book['review'] = book['review']
            if 'year' in book:
                processed_book['year'] = book['year']
            if 'genre' in book:
                processed_book['genre'] = book['genre']
            
            processed_books.append(processed_book)
    
    return processed_books


def generate_map_js(books_data, include_style_switcher=False, default_style='positron', default_pin_style='default'):
    """Generate JavaScript code to initialize the map"""
    
    # API key only in preview mode, rely on domain restrictions in production
    api_key_param = f'?api_key={STADIA_API_KEY}' if (include_style_switcher and STADIA_API_KEY) else ''
    
    js = """
    // Initialize map (temporary view, will be adjusted to fit markers)
    const map = L.map('map');
    
    // Define available tile layers
    const tileLayers = {
        'positron': {
            url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'voyager': {
            url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'dark': {
            url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'osm': {
            url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 19 }
        },
        'humanitarian': {
            url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a>',
            options: { maxZoom: 19 }
        },
        'terrain': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 18 }
        },
        'toner': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'watercolor': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 16 }
        },
        'alidade_smooth': {
            url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'alidade_smooth_dark': {
            url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'osm_bright': {
            url: 'https://tiles.stadiamaps.com/tiles/osm_bright/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'outdoors': {
            url: 'https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'opentopomap': {
            url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
            options: { maxZoom: 17 }
        },
        'cyclosm': {
            url: 'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Map style: &copy; <a href="https://www.cyclosm.org">CyclOSM</a>',
            options: { maxZoom: 20 }
        },
        'esri_world': {
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, Maxar, Earthstar Geographics, and the GIS User Community',
            options: { maxZoom: 19 }
        },
        'wikimedia': {
            url: 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="https://wikimediafoundation.org/wiki/Maps_Terms_of_Use">Wikimedia maps</a>',
            options: { maxZoom: 18 }
        },
        'toner_lite': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'voyager_nolabels': {
            url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'positron_nolabels': {
            url: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'dark_nolabels': {
            url: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            options: { subdomains: 'abcd', maxZoom: 19 }
        },
        'osm_de': {
            url: 'https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 18 }
        },
        'toner_background': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_toner_background/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'toner_lines': {
            url: 'https://tiles.stadiamaps.com/tiles/stamen_toner_lines/{z}/{x}/{y}{r}.png""" + api_key_param + """',
            attribution: '&copy; <a href="https://stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            options: { maxZoom: 20 }
        },
        'esri_world_street': {
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
            options: { maxZoom: 19 }
        },
        'esri_world_topo': {
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attribution: '&copy; <a href="https://www.esri.com/">Esri</a>',
            options: { maxZoom: 19 }
        },
        'esri_natgeo': {
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
            attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, National Geographic',
            options: { maxZoom: 16 }
        }
        // Additional providers (require API keys):
        // Mapbox: https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}
        // Thunderforest: https://{s}.tile.thunderforest.com/{style}/{z}/{x}/{y}.png?apikey={apikey}
        // Maptiler: https://api.maptiler.com/maps/{style}/256/{z}/{x}/{y}.png?key={key}
    };
    
    // Start with configured default style
    let currentLayer = '""" + default_style + """';
    let activeLayer = L.tileLayer(tileLayers[currentLayer].url, {
        attribution: tileLayers[currentLayer].attribution,
        ...tileLayers[currentLayer].options
    }).addTo(map);"""
    
    if include_style_switcher:
        js += """
    
    // Map style switcher function (preview mode only)
    window.switchStyle = function(styleName) {
        if (tileLayers[styleName]) {
            map.removeLayer(activeLayer);
            currentLayer = styleName;
            activeLayer = L.tileLayer(tileLayers[currentLayer].url, {
                attribution: tileLayers[currentLayer].attribution,
                ...tileLayers[currentLayer].options
            }).addTo(map);
            
            // Update active button
            document.querySelectorAll('.style-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-style="${styleName}"]`).classList.add('active');
        }
    };
    
    // Pin style switcher function (preview mode only)
    window.switchPinStyle = function(styleName) {
        if (pinStyles[styleName]) {
            currentPinStyle = styleName;
            
            // Clear and recreate markers
            markerLayer.clearLayers();
            
            markerDataStore.forEach(stored => {
                const marker = pinStyles[currentPinStyle].createMarker(stored.lat, stored.lng);
                marker.bindPopup(createPopupContent(stored.markerData));
                marker.addTo(markerLayer);
            });
            
            // Update active button
            document.querySelectorAll('.pin-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-pin="${styleName}"]`).classList.add('active');
            
            // Update offscreen indicators
            setTimeout(updateOffscreenIndicators, 100);
        }
    };
    
    // Panel toggle function (preview mode only)
    window.togglePanel = function() {
        const panel = document.getElementById('stylePanel');
        panel.classList.toggle('collapsed');
    };"""
    
    js += """
    
    // Book data
    const booksData = """ + json.dumps(books_data, indent=4) + """;
    
    // Define pin styles
    const pinStyles = {
        'default': {
            name: 'Default Blue',
            createMarker: (lat, lng) => L.marker([lat, lng])
        },
        'burgundy_circle': {
            name: 'Burgundy Circles',
            createMarker: (lat, lng) => L.circleMarker([lat, lng], {
                radius: 8,
                fillColor: '#8B2635',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            })
        },
        'black_circle': {
            name: 'Black Circles',
            createMarker: (lat, lng) => L.circleMarker([lat, lng], {
                radius: 8,
                fillColor: '#2c3e50',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            })
        },
        'small_burgundy_pin': {
            name: 'Small Burgundy Pin',
            createMarker: (lat, lng) => {
                const icon = L.divIcon({
                    className: 'custom-pin burgundy-pin',
                    html: '<div class="pin-content"></div>',
                    iconSize: [20, 32],
                    iconAnchor: [10, 32],
                    popupAnchor: [0, -32]
                });
                return L.marker([lat, lng], { icon: icon });
            }
        },
        'small_orange_pin': {
            name: 'Small Orange Pin',
            createMarker: (lat, lng) => {
                const icon = L.divIcon({
                    className: 'custom-pin orange-pin',
                    html: '<div class="pin-content"></div>',
                    iconSize: [20, 32],
                    iconAnchor: [10, 32],
                    popupAnchor: [0, -32]
                });
                return L.marker([lat, lng], { icon: icon });
            }
        },
        'pushpin_emoji': {
            name: 'Pushpin Emoji',
            createMarker: (lat, lng) => {
                const icon = L.divIcon({
                    className: 'emoji-icon-marker',
                    html: '<div class="emoji-icon">📌</div>',
                    iconSize: [30, 30],
                    iconAnchor: [15, 15],
                    popupAnchor: [0, -15]
                });
                return L.marker([lat, lng], { icon: icon });
            }
        }
    };
    
    // Current pin style
    let currentPinStyle = '""" + default_pin_style + """';
    
    // Store marker data for recreation
    let markerDataStore = [];
    let markerLayer = L.layerGroup().addTo(map);
    
    // Function to create popup content
    function createPopupContent(markerData) {
        let popupContent = '<div class="book-popup">';
        
        if (markerData.book.cover) {
            popupContent += `<img src="${markerData.book.cover}" alt="${markerData.book.title}" class="book-cover" />`;
        }
        
        popupContent += '<div class="book-details">';
        
        if (markerData.book.genre) {
            popupContent += `<p class="genre">${markerData.book.genre}</p>`;
        }
        
        popupContent += `<h3>${markerData.book.title}</h3>`;
        
        if (markerData.book.author) {
            popupContent += `<p class="author">${markerData.book.author}</p>`;
        }
        
        popupContent += `<p class="location">${markerData.location.name}</p>`;
        
        if (markerData.book.review) {
            popupContent += `<a href="${markerData.book.review}" target="_blank" class="review-link">Read Erin's review</a>`;
        }
        
        popupContent += '</div>';
        popupContent += '</div>';
        return popupContent;
    }
    
    // Function to create all markers with current style
    function createMarkers() {
        // Clear existing markers
        markerLayer.clearLayers();
        
        // Collect all markers with their data
        const allMarkers = [];
        booksData.forEach(book => {
            book.locations.forEach(location => {
                allMarkers.push({
                    book: book,
                    location: location,
                    lat: location.lat,
                    lng: location.lng
                });
            });
        });
        
        // Detect duplicate coordinates and apply offset
        const coordCounts = {};
        const coordOffsets = {};
        
        // Count occurrences of each coordinate
        allMarkers.forEach(marker => {
            const key = `${marker.lat},${marker.lng}`;
            coordCounts[key] = (coordCounts[key] || 0) + 1;
            coordOffsets[key] = 0;
        });
        
        // Create markers with offset for duplicates
        const bounds = [];
        markerDataStore = [];
        
        allMarkers.forEach(markerData => {
            const key = `${markerData.lat},${markerData.lng}`;
            let lat = markerData.lat;
            let lng = markerData.lng;
            
            // If this coordinate has duplicates, apply a jittery offset
            if (coordCounts[key] > 1) {
                const index = coordOffsets[key];
                const total = coordCounts[key];
                
                // Base angle distributed around circle, plus random jitter
                const baseAngle = (index / total) * 2 * Math.PI;
                const angleJitter = (Math.random() - 0.5) * Math.PI / 2; // ±45° jitter
                const angle = baseAngle + angleJitter;
                
                // Distance with randomness: 120-280km range
                const baseOffset = 2.0; // ~200km
                const distJitter = (Math.random() - 0.5) * 1.6; // ±80km variation
                const offsetDist = baseOffset + distJitter;
                
                lat += offsetDist * Math.cos(angle);
                lng += offsetDist * Math.sin(angle);
                
                coordOffsets[key]++;
            }
            
            // Store for later recreation
            markerDataStore.push({
                markerData: markerData,
                lat: lat,
                lng: lng
            });
            
            // Create marker with current style
            const marker = pinStyles[currentPinStyle].createMarker(lat, lng);
            marker.bindPopup(createPopupContent(markerData));
            marker.addTo(markerLayer);
            
            bounds.push([lat, lng]);
        });
        
        return bounds;
    }
    
    // Initial marker creation
    const bounds = createMarkers();
    
    // Set default view (centered on Europe/North America, zoom level 3)
    // This prevents extreme outliers from forcing a too-wide view
    // Off-screen indicators will show markers outside this view
    if (bounds.length > 0) {
        // Calculate center of all markers
        let centerLat = bounds.reduce((sum, b) => sum + b[0], 0) / bounds.length;
        let centerLng = bounds.reduce((sum, b) => sum + b[1], 0) / bounds.length;
        
        // Set view with moderate zoom (3 = continent level, good for global view)
        map.setView([centerLat, centerLng], 3);
    }
    
    // Create offscreen marker indicators
    const directions = ['north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest'];
    const indicators = {};
    
    directions.forEach(dir => {
        const indicator = document.createElement('div');
        indicator.className = `offscreen-indicator ${dir}`;
        indicator.id = `indicator-${dir}`;
        document.getElementById('map').appendChild(indicator);
        indicators[dir] = indicator;
    });
    
    // Store all marker positions for offscreen tracking
    const allMarkerPositions = bounds.map(pos => ({ lat: pos[0], lng: pos[1] }));
    
    // Function to update offscreen indicators
    function updateOffscreenIndicators() {
        const mapBounds = map.getBounds();
        const counts = {
            north: 0, south: 0, east: 0, west: 0,
            northeast: 0, northwest: 0, southeast: 0, southwest: 0
        };
        
        allMarkerPositions.forEach(pos => {
            if (!mapBounds.contains([pos.lat, pos.lng])) {
                const isNorth = pos.lat > mapBounds.getNorth();
                const isSouth = pos.lat < mapBounds.getSouth();
                const isEast = pos.lng > mapBounds.getEast();
                const isWest = pos.lng < mapBounds.getWest();
                
                // Determine direction
                if (isNorth && isEast) counts.northeast++;
                else if (isNorth && isWest) counts.northwest++;
                else if (isSouth && isEast) counts.southeast++;
                else if (isSouth && isWest) counts.southwest++;
                else if (isNorth) counts.north++;
                else if (isSouth) counts.south++;
                else if (isEast) counts.east++;
                else if (isWest) counts.west++;
            }
        });
        
        // Update indicator visibility and text
        Object.keys(counts).forEach(dir => {
            const indicator = indicators[dir];
            if (counts[dir] > 0) {
                indicator.textContent = counts[dir];
                indicator.classList.add('visible');
            } else {
                indicator.classList.remove('visible');
            }
        });
    }
    
    // Update indicators on map movement
    map.on('moveend', updateOffscreenIndicators);
    map.on('zoomend', updateOffscreenIndicators);
    
    // Initial update after a delay (to let map settle)
    setTimeout(updateOffscreenIndicators, 200);
    """
    return js


def generate_html(books_data, preview_mode=False, default_style='positron', default_pin_style='default'):
    """Generate the HTML file with embedded map"""
    map_js = generate_map_js(books_data, include_style_switcher=preview_mode, default_style=default_style, default_pin_style=default_pin_style)
    
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
        
        .leaflet-popup-close-button {{
            top: 6px !important;
            right: 6px !important;
        }}
        
        .book-popup {{
            display: flex;
            gap: 12px;
            min-width: 250px;
            max-width: 350px;
        }}
        
        .book-popup .book-cover {{
            width: 80px;
            height: auto;
            flex-shrink: 0;
            border-radius: 4px;
            align-self: flex-start;
        }}
        
        .book-popup .book-details {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            flex-grow: 1;
        }}
        
        .book-popup .genre {{
            font-size: 10pt;
            color: #888;
            margin: 0 0 2px 0;
            font-style: italic;
        }}
        
        .book-popup h3 {{
            font-size: 16pt;
            margin: 0;
            color: #000;
            line-height: 1.1;
        }}
        
        .book-popup .author {{
            font-size: 16pt;
            color: #000;
            margin: 0;
            line-height: 1.1;
        }}
        
        .book-popup .location {{
            font-size: 10pt;
            color: #888;
            margin: 2px 0 0 0;
        }}
        
        .book-popup .review-link {{
            font-size: 10pt;
            color: #007bff;
            text-decoration: none;
            margin-top: auto;
            display: inline-block;
            align-self: flex-end;
        }}
        
        .book-popup .review-link::after {{
            content: ' →';
        }}
        
        .book-popup .review-link:hover {{
            text-decoration: underline;
        }}
        
        /* Offscreen marker indicators */
        .offscreen-indicator {{
            position: absolute;
            background-color: rgba(0, 123, 255, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: none;
            white-space: nowrap;
        }}
        
        .offscreen-indicator.visible {{
            display: block;
        }}
        
        .offscreen-indicator::before {{
            content: '→';
            margin-right: 4px;
        }}
        
        .offscreen-indicator.north {{
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
        }}
        
        .offscreen-indicator.north::before {{
            content: '↑';
        }}
        
        .offscreen-indicator.south {{
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
        }}
        
        .offscreen-indicator.south::before {{
            content: '↓';
        }}
        
        .offscreen-indicator.east {{
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
        }}
        
        .offscreen-indicator.west {{
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
        }}
        
        .offscreen-indicator.west::before {{
            content: '←';
        }}
        
        .offscreen-indicator.northeast {{
            top: 20px;
            right: 20px;
        }}
        
        .offscreen-indicator.northeast::before {{
            content: '↗';
        }}
        
        .offscreen-indicator.northwest {{
            top: 20px;
            left: 20px;
        }}
        
        .offscreen-indicator.northwest::before {{
            content: '↖';
        }}
        
        .offscreen-indicator.southeast {{
            bottom: 20px;
            right: 20px;
        }}
        
        .offscreen-indicator.southeast::before {{
            content: '↘';
        }}
        
        .offscreen-indicator.southwest {{
            bottom: 20px;
            left: 20px;
        }}
        
        .offscreen-indicator.southwest::before {{
            content: '↙';
        }}
        
        /* Custom pin styles */
        .custom-pin {{
            background: transparent;
            border: none;
        }}
        
        .custom-pin .pin-content {{
            width: 20px;
            height: 32px;
            position: relative;
        }}
        
        .custom-pin .pin-content::before {{
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            left: 0;
            top: 0;
        }}
        
        .custom-pin .pin-content::after {{
            content: '';
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: white;
            left: 6px;
            top: 6px;
        }}
        
        .burgundy-pin .pin-content::before {{
            background: #8B2635;
            border: 2px solid white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        
        .orange-pin .pin-content::before {{
            background: #D2691E;
            border: 2px solid white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        
        .emoji-icon-marker {{
            background: transparent;
            border: none;
            text-align: center;
        }}
        
        .emoji-icon-marker .emoji-icon {{
            font-size: 24px;
            filter: drop-shadow(0 2px 3px rgba(0,0,0,0.4));
        }}
        
        {css_content}"""
    
    # Add preview-specific styles
    if preview_mode:
        html += """
        
        /* Combined style chooser panel (preview mode only) */
        .style-panel {
            position: fixed;
            top: 8px;
            right: 8px;
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 240px;
            transition: all 0.3s ease;
        }
        
        .style-panel.collapsed .panel-content {
            display: none;
        }
        
        .panel-toggle {
            padding: 6px 10px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            width: 100%;
            text-align: left;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        
        .panel-toggle:hover {
            background: #0056b3;
        }
        
        .toggle-icon {
            font-size: 10px;
            transition: transform 0.3s;
        }
        
        .style-panel.collapsed .toggle-icon {
            transform: rotate(180deg);
        }
        
        .panel-content {
            padding: 8px;
        }
        
        .panel-section {
            margin-bottom: 10px;
        }
        
        .panel-section:last-child {
            margin-bottom: 0;
        }
        
        .panel-section h3 {
            margin: 0 0 5px 0;
            font-size: 10px;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .note {
            font-size: 8px;
            color: #999;
            margin-bottom: 8px;
            font-style: italic;
            text-align: center;
        }
        
        .style-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 3px;
        }
        
        .pin-grid {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        
        .style-btn,
        .pin-btn {
            padding: 5px 3px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 2px;
            cursor: pointer;
            font-size: 9px;
            transition: all 0.2s;
            text-align: center;
            line-height: 1.2;
        }
        
        .style-btn:hover,
        .pin-btn:hover {
            border-color: #007bff;
            background: #f8f9fa;
        }
        
        .style-btn.active,
        .pin-btn.active {
            border-color: #007bff;
            background: #007bff;
            color: white;
            font-weight: bold;
        }"""
    
    html += """
    </style>
</head>
<body>
    <div id="map"></div>"""
    
    # Add style chooser panel in preview mode
    if preview_mode:
        # Generate buttons with active class on default style
        styles = [
            ('positron', 'Positron'),
            ('voyager', 'Voyager'),
            ('dark', 'Dark'),
            ('osm', 'OSM'),
            ('humanitarian', 'HOT'),
            ('terrain', 'Terrain'),
            ('toner', 'Toner'),
            ('watercolor', 'Watercolor'),
            ('alidade_smooth', 'Alidade'),
            ('alidade_smooth_dark', 'Alidade Dark'),
            ('osm_bright', 'OSM Bright'),
            ('outdoors', 'Outdoors'),
            ('opentopomap', 'TopoMap'),
            ('cyclosm', 'CyclOSM'),
            ('esri_world', 'Satellite'),
            ('wikimedia', 'Wikimedia'),
            ('toner_lite', 'Toner Lite'),
            ('voyager_nolabels', 'Voyager NL'),
            ('positron_nolabels', 'Positron NL'),
            ('dark_nolabels', 'Dark NL'),
            ('osm_de', 'OSM DE'),
            ('toner_background', 'Toner BG'),
            ('toner_lines', 'Toner Lines'),
            ('esri_world_street', 'Esri Street'),
            ('esri_world_topo', 'Esri Topo'),
            ('esri_natgeo', 'Nat Geo')
        ]
        
        buttons_html = ""
        for style_id, style_name in styles:
            active_class = " active" if style_id == default_style else ""
            buttons_html += f'            <button class="style-btn{active_class}" data-style="{style_id}" onclick="switchStyle(\'{style_id}\')">{style_name}</button>\n'
        
        # Generate pin style buttons
        pin_styles_list = [
            ('default', 'Blue Pin'),
            ('burgundy_circle', 'Burgundy Circle'),
            ('black_circle', 'Black Circle'),
            ('small_burgundy_pin', 'Burgundy Drop'),
            ('small_orange_pin', 'Orange Drop'),
            ('pushpin_emoji', 'Pushpin 📌')
        ]
        
        pin_buttons_html = ""
        for pin_id, pin_name in pin_styles_list:
            active_class = " active" if pin_id == default_pin_style else ""
            pin_buttons_html += f'            <button class="pin-btn{active_class}" data-pin="{pin_id}" onclick="switchPinStyle(\'{pin_id}\')">{pin_name}</button>\n'
        
        html += f"""
    
    <!-- Combined Style Panel (preview mode only) -->
    <div class="style-panel" id="stylePanel">
        <button class="panel-toggle" onclick="togglePanel()">
            <span>Map & Pin Styles</span>
            <span class="toggle-icon">▼</span>
        </button>
        <div class="panel-content">
            <p class="note">Preview only - not included in production</p>
            
            <div class="panel-section">
                <h3>Pin Styles</h3>
                <div class="pin-grid">
{pin_buttons_html.rstrip()}
                </div>
            </div>
            
            <div class="panel-section">
                <h3>Map Tiles</h3>
                <div class="style-grid">
{buttons_html.rstrip()}
                </div>
            </div>
        </div>
    </div>"""
    
    html += f"""
    
    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
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
    
    # Get default style from config (default to 'positron' if not specified)
    default_style = data.get('default_style', 'positron')
    print(f"Using map style: {default_style}")
    
    # Get default pin style from config (default to 'burgundy_circle' if not specified)
    default_pin_style = data.get('default_pin_style', 'burgundy_circle')
    print(f"Using pin style: {default_pin_style}")
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate production HTML (clean, no style chooser)
    print("Generating production HTML...")
    html_production = generate_html(processed_books, preview_mode=False, default_style=default_style, default_pin_style=default_pin_style)
    output_file = output_path / "index.html"
    with open(output_file, 'w') as f:
        f.write(html_production)
    print(f"✓ Generated {output_file} (production)")
    
    # Generate preview HTML (with style chooser)
    print("Generating preview HTML...")
    html_preview = generate_html(processed_books, preview_mode=True, default_style=default_style, default_pin_style=default_pin_style)
    preview_file = output_path / "preview.html"
    with open(preview_file, 'w') as f:
        f.write(html_preview)
    print(f"✓ Generated {preview_file} (with style chooser)")
    
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
    print(f"  1. Open {preview_file} to test styles")
    print(f"  2. Open {output_file} to see production version")
    print("  3. Upload index.html to Squarespace (clean, no style chooser)")


if __name__ == "__main__":
    main()

