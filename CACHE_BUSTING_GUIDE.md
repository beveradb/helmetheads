# Cache Busting Guide for Helmet Heads Website

## Overview
This guide explains how to ensure visitors always see the latest version of your website after deployments to Cloudflare Pages.

## What I've Implemented

### 1. Version Query Strings
All HTML files now reference CSS and JS files with version numbers:
```html
<link rel="stylesheet" href="styles.css?v=20251009">
<script src="script.js?v=20251009"></script>
```

### 2. `_headers` File
Created a `_headers` file that controls how Cloudflare Pages caches different file types:
- **HTML files**: No caching (always check for updates)
- **CSS/JS files**: Cache but always revalidate
- **Images/Videos**: Cache for 1 hour
- **Fonts**: Cache for 1 year (immutable)

## How to Use Going Forward

### Every Time You Make Changes to CSS or JavaScript:

**Step 1:** Update the version number in ALL HTML files

Change the version date to today's date (format: YYYYMMDD):
```html
<!-- Before -->
<link rel="stylesheet" href="styles.css?v=20251009">

<!-- After (example for Jan 15, 2025) -->
<link rel="stylesheet" href="styles.css?v=20250115">
```

Update in these files:
- `index.html`
- `thank-you.html`
- `privacy.html`

**Step 2:** Commit and push your changes
```bash
git add .
git commit -m "Update cache busting version"
git push
```

**Step 3:** Purge Cloudflare Cache (if needed)
1. Go to your Cloudflare dashboard
2. Navigate to your domain
3. Click **Caching** → **Configuration**
4. Click **Purge Everything**

## Alternative: Automated Version Number

Instead of manually updating dates, you could use the current timestamp:
```html
<link rel="stylesheet" href="styles.css?v=<?php echo time(); ?>">
```

Or use Git commit hash (requires build process):
```html
<link rel="stylesheet" href="styles.css?v=abc123">
```

## Testing

After deployment:
1. **Clear browser cache** on your phone/computer (or use incognito mode)
2. **Hard refresh**: 
   - Chrome/Edge: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Safari: `Cmd+Option+R`
3. **Check the network tab** in browser DevTools to verify the version number

## Troubleshooting

### Still seeing old CSS on your phone?
1. Clear browser cache/data on your phone
2. Purge Cloudflare cache (dashboard)
3. Wait 5-10 minutes for CDN propagation
4. Try accessing in private/incognito mode

### When to purge Cloudflare cache?
- After major deployments with critical fixes
- If users report seeing old content after updates
- Not needed for every small change (the headers file handles most cases)

## Best Practices

1. **Always update version numbers** when you modify CSS or JS
2. **Use consistent date format** (YYYYMMDD) for easy tracking
3. **Test in incognito mode** after deployments to verify cache busting
4. **Keep version numbers in sync** across all HTML files
5. **Consider using build tools** (like Vite, Webpack) that automatically hash filenames for production

## Why This Works

- **Query strings** make browsers treat `styles.css?v=1` and `styles.css?v=2` as different files
- **_headers file** tells Cloudflare how aggressively to cache each file type
- **Cloudflare Pages** automatically serves the latest deployed version of files
- **Browser cache** is bypassed when the query string changes

## Resources

- [Cloudflare Pages Caching Documentation](https://developers.cloudflare.com/pages/configuration/serving-pages/#caching-and-performance)
- [Cloudflare Headers Documentation](https://developers.cloudflare.com/pages/configuration/headers/)

