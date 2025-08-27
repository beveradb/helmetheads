# GiveButter Integration Guide

This document outlines the steps needed to complete the GiveButter widget integration for the Helmet Heads website.

## Overview

The website has been prepared for GiveButter widget integration with placeholder containers in the fundraising section. Two main widgets need to be implemented:

1. **Goal Bar Widget** - To display fundraising progress
2. **Donation Button Widget** - To accept donations

## Integration Steps

### 1. Install GiveButter Library

Add the GiveButter library script to the `<head>` section of `index.html`:

```html
<!-- Add this to the <head> section -->
<script src="https://js.givebutter.com/elements/latest.js"></script>
```

### 2. Configure Goal Bar Widget

Replace the placeholder in the `#givebutter-goal-widget` div with the actual GiveButter goal bar widget code from your campaign dashboard.

### 3. Configure Donation Button Widget

Replace the placeholder button in the `#givebutter-button-widget` div with the actual GiveButter donation button widget code.

## Widget Locations

- **Goal Bar**: Located in the fundraising section, replaces the fake progress bar
- **Donation Button**: Located in the fundraising section, replaces the placeholder donate button

## Styling

The CSS has been configured to properly style the GiveButter widgets:
- `.givebutter-widget-container` - General container styling
- `#givebutter-goal-widget` - Specific styling for goal bar
- `#givebutter-button-widget` - Specific styling for donation button

## Colors

The website uses Brookland-Cayce High School colors:
- Primary Red: `#71161c`
- Light Beige: `#f4ede3`
- Dark Grey: `#1e2728`

Configure the GiveButter widgets to match these colors for consistent branding.

## Next Steps

1. Create a GiveButter campaign
2. Generate widget codes from the GiveButter dashboard
3. Replace placeholder content with actual widget codes
4. Test donation functionality
5. Deploy to production

## Reference

- [GiveButter Widget Documentation](https://help.givebutter.com/en/articles/6464859-how-to-use-givebutter-widgets-on-your-website)
- Current website: https://helmetheads.club
