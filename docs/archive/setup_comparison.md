# Setup Comparison: Python vs Node.js vs Alternatives

## Python (Recommended for MacBook)

### Setup Required:
1. **Check if Python 3 is available**: `python3 --version`
   - macOS Ventura (13+) and Sonoma (14+) come with Python 3.9+
   - If not present, install via Homebrew: `brew install python3`
   
2. **Install dependencies**: `pip3 install pyyaml geopy`
   - That's it!

### Pros:
- ✅ Usually pre-installed on macOS
- ✅ Simple package installation
- ✅ Good libraries for YAML and geocoding
- ✅ No build tools needed

### Cons:
- ❌ Might need to install Python 3 if only Python 2.7 is present
- ❌ Virtual environments recommended (but not required for simple scripts)

---

## Node.js

### Setup Required:
1. **Install Node.js**: 
   - Via Homebrew: `brew install node`
   - Or download from nodejs.org
   - Or use nvm (Node Version Manager)

2. **Install dependencies**: `npm install js-yaml node-geocoder`
   - Need to create package.json first

### Pros:
- ✅ Good for web projects
- ✅ npm ecosystem is extensive

### Cons:
- ❌ Not pre-installed
- ❌ Requires Homebrew or manual installation
- ❌ More setup steps

---

## Alternative: Pure Client-Side (No Build Step!)

### Could we skip the build script entirely?

**Option: YAML in browser**
- Use a YAML parser library in the browser (js-yaml)
- Load YAML file directly via fetch
- Parse and render map in browser
- No build step needed!

### Pros:
- ✅ Zero setup - just HTML/JS
- ✅ Edit YAML, refresh browser
- ✅ No Python or Node.js needed

### Cons:
- ❌ Geocoding in browser (might hit rate limits)
- ❌ Need to host YAML file somewhere accessible
- ❌ Less control over geocoding caching

---

## Recommendation

**For minimal setup on MacBook: Python**

1. Check: `python3 --version`
2. If missing: `brew install python3` (one command)
3. Install packages: `pip3 install pyyaml geopy`
4. Done!

**Alternative if you want ZERO setup:**
- Pure client-side solution
- Load YAML directly in browser
- Trade-off: geocoding happens in browser (slower, but works)

---

## Quick Start Commands (Python)

```bash
# Check if Python 3 is installed
python3 --version

# If not installed, install via Homebrew (if you have it)
brew install python3

# Install required packages
pip3 install pyyaml geopy

# Run the build script
python3 build.py
```

That's it! Very minimal setup.

