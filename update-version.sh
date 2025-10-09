#!/bin/bash
# Script to update cache-busting version numbers in all HTML files

# Get current date in YYYYMMDD format
NEW_VERSION=$(date +%Y%m%d)

echo "Updating cache-busting version to: $NEW_VERSION"

# Find and replace version numbers in all HTML files
find . -maxdepth 1 -name "*.html" -type f -exec sed -i.bak "s/styles\.css?v=[0-9]*/styles.css?v=$NEW_VERSION/g" {} \;
find . -maxdepth 1 -name "*.html" -type f -exec sed -i.bak "s/script\.js?v=[0-9]*/script.js?v=$NEW_VERSION/g" {} \;

# Remove backup files
rm -f ./*.bak

echo "✅ Version numbers updated to $NEW_VERSION in:"
echo "   - index.html"
echo "   - thank-you.html"
echo "   - privacy.html"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Commit: git add . && git commit -m 'Update cache busting version to $NEW_VERSION'"
echo "3. Push: git push"
echo "4. (Optional) Purge Cloudflare cache in dashboard"

