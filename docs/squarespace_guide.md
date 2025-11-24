# Embedding the Map in Squarespace

There are several ways to add the book location map to your Squarespace site. Choose the method that works best for you.

## Preview Before Embedding

**Always preview your map locally before uploading to Squarespace!**

### Quick Preview

**Option 1: Open directly**
```bash
open output/index.html
```
Or double-click `output/index.html` in Finder.

**Option 2: Local web server (recommended)**
```bash
cd output
python3 -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

This lets you:
- ✅ Check that all books appear correctly
- ✅ Test marker clustering
- ✅ Verify popups show book info
- ✅ Test on different screen sizes
- ✅ Make sure everything looks good before uploading

Once you're happy with the preview, proceed with one of the embedding methods below.

## Method 1: Upload HTML File (Recommended)

This is the simplest method if you have a Squarespace plan that supports file uploads.

### Steps:

1. **Build the map** (if you haven't already):
   ```bash
   python3 build.py
   ```

2. **Upload the HTML file**:
   - Go to your Squarespace site settings
   - Navigate to **Settings** → **Files**
   - Upload `output/index.html`
   - Note the URL where it's hosted (e.g., `https://yoursite.com/s/your-file-id/index.html`)

3. **Embed in a page**:
   - Edit the page where you want the map
   - Add a **Code Block**
   - Paste this code (replace with your file URL):
   ```html
   <iframe src="https://yoursite.com/s/your-file-id/index.html" 
           width="100%" 
           height="600" 
           frameborder="0"
           style="border: none;">
   </iframe>
   ```

## Method 2: Code Block with Inline HTML

If you can't upload files, you can paste the HTML directly into a Code Block.

### Steps:

1. **Build the map**:
   ```bash
   python3 build.py
   ```

2. **Copy the HTML**:
   - Open `output/index.html` in a text editor
   - Copy the entire contents

3. **Paste into Squarespace**:
   - Edit your page
   - Add a **Code Block**
   - Paste the HTML code
   - Save

**Note**: This method embeds the entire map code in your page, which may make the page larger.

## Method 3: External Hosting + iframe

Host the map elsewhere (GitHub Pages, Netlify, your own server) and embed via iframe.

### Steps:

1. **Host the map**:
   - Upload `output/index.html` to your hosting
   - Get the public URL

2. **Embed in Squarespace**:
   - Add a **Code Block** to your page
   - Use the iframe code from Method 1 with your hosted URL

### Free Hosting Options:

- **GitHub Pages**: Free, easy setup
- **Netlify**: Free, drag-and-drop deployment
- **Your own server**: If you have one

## Method 4: Custom Page Template (Advanced)

If you have developer access, you can create a custom page template.

1. Upload `output/index.html` to your template files
2. Create a page that uses this template
3. The map will be part of the page structure

## Styling Tips

### Adjust Map Height

In the iframe code, change the `height` attribute:
```html
<iframe ... height="800" ...></iframe>
```

### Full-Width Map

To make the map span the full width of your page:
```html
<div style="width: 100%; margin: 0; padding: 0;">
  <iframe src="..." 
          width="100%" 
          height="600" 
          frameborder="0"
          style="border: none; display: block;">
  </iframe>
</div>
```

### Responsive Height

For a map that adjusts to screen size:
```html
<div style="position: relative; padding-bottom: 75%; height: 0; overflow: hidden;">
  <iframe src="..." 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;">
  </iframe>
</div>
```

## Troubleshooting

### Map Doesn't Show

- Check that the HTML file uploaded correctly
- Verify the URL in the iframe is correct
- Make sure your Squarespace plan supports Code Blocks

### Map Looks Small

- Increase the `height` attribute in the iframe
- Try the responsive height method above

### Map Doesn't Update

- Rebuild the map: `python3 build.py`
- Re-upload the new `output/index.html`
- Clear your browser cache

## Recommended Approach

**For most users**: Method 1 (Upload HTML + iframe)
- Clean separation
- Easy to update (just re-upload)
- Doesn't bloat your page code

**If you can't upload files**: Method 2 (Code Block with inline HTML)
- Works on all Squarespace plans
- Everything in one place
- Slightly larger page size

