# Helmet Heads

A 501(c)(3) nonprofit organization providing cycling opportunities for South Carolina youth through localized high school cycling clubs.

## Website Styling System

### Automatic Alternating Section Backgrounds

The website uses an **automatic alternating background system** that requires NO manual CSS changes when adding or removing sections.

#### How It Works

- **Odd-numbered sections** (1st, 3rd, 5th, 7th, etc.) → White background (`var(--white)`)
- **Even-numbered sections** (2nd, 4th, 6th, 8th, etc.) → Light background (`var(--light-color)`)
- **Hero section** → Special gradient (overridden with `!important`)

This is achieved through CSS `nth-of-type` selectors that automatically apply based on section order in the HTML.

#### Current Section Order

1. Hero - Gradient (special case)
2. About - Light background
3. Bike Trains - White
4. Our Program - Light background
5. Pilot Program - White
6. Fundraising - Light background
7. Our Organization - White
8. Updates/Contact - Light background

### Smart Card Background Contrast

Card components automatically contrast with their parent section background:

- **Cards in white sections** → Light background
- **Cards in light sections** → White background

#### Card Classes Using Smart Contrast

The following classes automatically adjust their backgrounds:
- `.about-card`
- `.program-box`
- `.school-card`
- `.leader-card-pilot`
- `.pilot-timeline`
- `.tier`
- `.org-card`
- `.leader-card-org`
- `.contact-info`
- `.signup-form`

### Rules for Future Development

#### ✅ DO

1. **Use `<section>` tags** for all major page sections to ensure automatic background alternation
2. **Use existing card classes** (listed above) when creating new card-like components
3. **Add new card classes** to the smart contrast system if creating new card types:
   ```css
   section:nth-of-type(odd) .your-new-card,
   section:nth-of-type(even) .your-new-card
   ```
4. **Test after adding/removing sections** to verify the alternating pattern still looks correct
5. **Use CSS variables** for colors:
   - `var(--primary-color)` - Main brand color (#71161c)
   - `var(--white)` - White (#ffffff)
   - `var(--light-color)` - Light beige (#f4ede3)
   - `var(--dark-color)` - Dark text (#1e2728)
   - `var(--gray-color)` - Body text (#6b7280)

#### ❌ DON'T

1. **DON'T hardcode background colors** on individual section classes (`.about`, `.program`, etc.)
2. **DON'T hardcode background colors** on card classes - let the smart system handle it
3. **DON'T use divs instead of sections** for major page sections
4. **DON'T add inline styles** for backgrounds that would override the system
5. **DON'T mix section order** without considering visual flow - white-light-white-light pattern

### Adding New Sections

When adding a new section:

```html
<section id="new-section" class="new-section">
    <div class="container">
        <h2 class="section-title">Your Title</h2>
        <!-- Content with card classes if needed -->
    </div>
</section>
```

The background will automatically alternate based on its position. No CSS background property needed in `.new-section`!

### Adding New Card Components

If creating a new card/box component:

1. Create the base styles without background:
   ```css
   .my-new-card {
       padding: 2rem;
       border-radius: var(--border-radius);
       box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
       /* NO background property here */
   }
   ```

2. Add it to the smart contrast system at the top of `styles.css`:
   ```css
   /* Cards in white sections get light background */
   section:nth-of-type(odd) .my-new-card {
       background: var(--light-color);
   }
   
   /* Cards in light sections get white background */
   section:nth-of-type(even) .my-new-card {
       background: var(--white);
   }
   ```

### Color System

The site uses a maroon/burgundy color scheme:

- **Primary**: `#71161c` (Brookland-Cayce maroon)
- **Light background**: `#f4ede3` (warm beige)
- **Dark text**: `#1e2728`
- **Gray text**: `#6b7280`

### Responsive Design

The site includes three breakpoints:
- `@media (max-width: 968px)` - Tablets
- `@media (max-width: 768px)` - Mobile landscape
- `@media (max-width: 480px)` - Mobile portrait

## Project Structure

- `index.html` - Main landing page
- `styles.css` - All styling with automatic background system
- `script.js` - Navigation and interactive features
- `privacy.html` - Privacy policy page
- `thank-you.html` - Post-donation thank you page

## Tech Stack

- Pure HTML/CSS/JavaScript (no frameworks)
- Font Awesome 7.0.1 for icons
- Google Fonts (Inter)
- Givebutter widgets for donations and email signup
- Google Analytics & Meta Pixel for tracking
- Microsoft Clarity for heatmaps
- Tawk.to for live chat

## Development Notes

- The site is designed to be maintainable by non-technical users
- All color changes can be made via CSS variables at the top of `styles.css`
- The automatic styling system minimizes manual CSS work when adding content
- Widget IDs are hardcoded in HTML for Givebutter integration