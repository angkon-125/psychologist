## Overview
The frontend employs a **custom CSS design system** built on vanilla CSS with no external frameworks (no Tailwind, Bootstrap, or component libraries). The aesthetic is a **dark cyberpunk/glassmorphism theme** featuring neon accents, translucent glass panels, and smooth animations.

## Design Token Architecture
All styling is centralized in `psychologist/frontend/style.css` using CSS custom properties defined in `:root`:

### Color Palette
- **Backgrounds**: Deep dark gradients (`#0a0a0f` → `#0d0d14`) creating depth
- **Glass Surfaces**: Semi-transparent layers (`rgba(255, 255, 255, 0.03)`) with `backdrop-filter: blur(20px)`
- **Neon Accent Colors**:
  - Cyan (`#00f0ff`) — primary accent, active states, highlights
  - Blue (`#0066ff`) — secondary accent, gradients
  - Purple (`#a855f7`) — tertiary accent, identity elements
  - Green (`#00ff88`) — success/safe states, energy indicators
  - Red (`#ff3366`) — danger/error/crisis states
  - Orange (`#ff9500`) — warning/paused states
- **Text**: Light gray hierarchy (`#e0e0e0` primary, `#90909a` secondary)

### Typography
- **Font Stack**: `'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif`
- **Monospace**: `'Courier New', monospace` for numeric displays (clocks, percentages, counters)
- **Weight Scale**: 600–800 for emphasis; standard weights for body text

### Spacing & Layout
- **Border Radius**: `16px` global standard for cards/panels; smaller radii (6–12px) for buttons/badges
- **Transition**: `all 0.3s cubic-bezier(0.4, 0, 0.2, 1)` — consistent easing across all interactive elements
- **Grid System**: CSS Grid with `auto-fit` and `minmax()` for responsive card layouts

## Component Patterns

### Glass Cards
Universal container pattern used throughout:
```css
.card {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border-radius: var(--border-radius);
    border: 1px solid var(--glass-border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
```
Hover effects add subtle lift (`translateY(-2px)`) and cyan-tinted glow.

### Gradient Text
Headings and key metrics use gradient clipping:
```css
background: linear-gradient(90deg, var(--neon-cyan), var(--neon-blue));
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### Progress Bars & Meters
Emotion/need/conflict bars use gradient fills with colored box-shadows matching their semantic meaning (cyan for curiosity, red for fear/stress, green for confidence).

### Animated Glow Effects
- **Pulse animations** on status dots, listening indicators, and recording buttons
- **Box-shadow glows** on active elements (buttons, sliders, progress fills)
- **Border pulse animation** on submit button with rotating gradient border

### Badge System
Semantic badges for state indication:
- `.badge-conflicted` — red tinted
- `.badge-new` — cyan tinted
- `.status-active/paused/completed/abandoned` — color-coded per state
- `.safety-badge` — green/yellow/red for safety levels

## Layout Structure
Three-tier layout:
1. **Top Bar** — System name, status indicator, clock, energy meter, language toggle
2. **Sidebar + Main Content** — Navigation sidebar (280px fixed) with scrollable content area
3. **Bottom Console** — Fixed footer with three-column grid (thought stream | input interface | influence meters)

The Emotional Support Companion section uses a specialized 2×2 grid layout with four panels (conversation, status, input, tools).

## Responsive Strategy
Breakpoints at 1200px, 1024px, and 768px:
- **≤1200px**: Bottom console stacks to single column; radial charts wrap horizontally
- **≤1024px**: Companion grid collapses to single column
- **≤768px**: Sidebar becomes horizontal scrollable nav; top bar centers vertically; grids collapse to single column

## Internationalization
Embedded i18n system in `script.js` with two locales (`en`, `bn_bd`). Uses `data-i18n` attributes for text content and `data-i18n-placeholder` for input placeholders. Language preference persisted in `localStorage`.

## Canvas Visualizations
Two canvas-based visual components:
- **Knowledge Graph** — Node-link diagram with glowing nodes and connecting edges
- **Radial Influence Charts** — Circular progress meters for cognitive influence domains

Both redraw dynamically via JavaScript with shadow blur effects for neon glow.

## Key Files
- `psychologist/frontend/style.css` — Complete design system (1857 lines)
- `psychologist/frontend/index.html` — Semantic HTML structure with data-i18n attributes
- `psychologist/frontend/script.js` — UI logic, i18n engine, canvas rendering, dynamic updates
- `psychologist/frontend/languages/en.json` / `bn_bd.json` — External translation files (backup/reference)