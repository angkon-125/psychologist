# ZARA UI Documentation

## Overview

The ZARA frontend is a single-page application built with vanilla HTML/CSS/JavaScript. It features a **cyberpunk glassmorphism** design with a dark theme, neon accent colors, and glass-effect panels. The UI serves two major purposes:

1. **Cognitive Mind Dashboard** — Visualize the internal state of the AI mind (emotions, beliefs, goals, identity, memory, etc.)
2. **Emotional Support Companion** — Interactive chat-based emotional support with voice and text input

---

## Layout Structure

```
┌──────────────────────────────────────────────────────────┐
│                      TOP STATUS BAR                       │
├────────┬─────────────────────────────────────────────────┤
│        │                                                   │
│  SIDE  │              MAIN CONTENT AREA                    │
│  BAR   │         (13 switchable sections)                  │
│  NAV   │                                                   │
│        │                                                   │
├────────┴─────────────────────────────────────────────────┤
│                   FOOTER CONSOLE                           │
│  (Thought Stream | Cognitive Input | Influence Meter)     │
└──────────────────────────────────────────────────────────┘
```

### Top Status Bar
| Element | Description |
|---------|-------------|
| System Name | "COGNITIVE MIND v2.0" with cyan-to-blue gradient text |
| Status Indicator | Pulsing green dot + "ONLINE & EVOLVING" text |
| Clock | Real-time monospace clock display |
| Step Counter | Monospace badge showing processing step count |
| Energy Bar | Horizontal progress bar for "Cognitive Energy" |
| Language Toggle | Button to switch between English / বাংলা |

### Sidebar Navigation (280px wide)
Vertical nav with 13 section buttons. Active section gets a cyan left border highlight.

### Main Content Area
Scrollable area that displays one section at a time with fade-in animation.

### Footer — Cognitive Input Console
Three-column grid (collapses on mobile):
- **Left**: Real-Time Thought Stream (scrolling thought items)
- **Center**: Cognitive Input Interface (type selector, textarea, emotion sliders, submit, processing flow, response analysis)
- **Right**: Cognitive Influence Meter (5 radial canvas charts)

---

## Navigation Sections

| # | Section ID | Nav Label | Content |
|---|-----------|-----------|---------|
| 1 | `dashboard` | Main Dashboard | 4-card grid: Cognitive State, Emotional State, Dominant Goal, System Metrics |
| 2 | `companion` | Emotional Support | Full companion chat interface (see below) |
| 3 | `emotions` | Emotion Panel | 8 emotion bars (Curiosity, Fear, Confidence, Doubt, Motivation, Stress, Trust, Frustration) |
| 4 | `needs` | Internal Needs | 7 need bars (Knowledge, Security, Exploration, Social, Achievement, Stability, Autonomy) |
| 5 | `beliefs` | Belief System | Filter buttons (All/Strong/Weak/Conflicted/New) + dynamic belief list |
| 6 | `goals` | Goal Generation | Dynamic grid of goal cards with status tags |
| 7 | `conflicts` | Cognitive Conflicts | Dynamic grid of conflict items with dual-tone tension bars |
| 8 | `identity` | Self-Identity | 6-card grid: Self-Confidence, Self-Consistency, Knowledge Gaps, Decision Quality, Emotional Balance, Value Stability |
| 9 | `memory` | Memory Timeline | Vertical timeline with cyan connector line and glowing dot markers |
| 10 | `graph` | Knowledge Graph | Full-width canvas element for graph visualization |
| 11 | `debate` | Internal Debate | Dynamic grid of agent cards with arguments and stats |
| 12 | `simulation` | Simulation Panel | Scenario card with Risk/Reward scores, Emotional Consequence, Recommended Action |
| 13 | `history` | Input History | Search input + type filter dropdown + dynamic history list with delete buttons |

---

## Emotional Support Companion

The companion section (`#companion`) is the core interactive UI for the emotional support chatbot.

### Crisis Disclaimer Banner
Yellow dashed-border banner at the top:
> ⚠️ This is an offline emotional support companion, not a replacement for professional therapy or medical help.

### Companion Grid Layout (2×2)

```
┌─────────────────────────┬──────────────────┐
│  Panel A: Conversation  │  Panel D: Status  │
│  (Chat Timeline)        │                   │
├─────────────────────────┼──────────────────┤
│  Panel B: Input Controls│  Panel C: Tools   │
└─────────────────────────┴──────────────────┘
```

#### Panel A — Conversation Timeline
- **Session Controls**: "New Session" (green) and "End Session" (red) buttons
- **Chat Container**: Scrollable message area (max-height 480px)
- **Messages**: User messages (cyan bubbles, right-aligned) and Assistant messages (purple bubbles, left-aligned)
- **Placeholder**: Chat bubble icon with prompt text when no session is active

#### Panel B — Input Controls
- **Mode Selector**: Dropdown with Hybrid / Text / Voice modes
- **Text Input Area**:
  - Textarea for typing messages
  - "Read Response Aloud" toggle switch (default: on)
  - "Send" button (cyan-to-blue gradient)
- **Voice Input Area**:
  - "Start Recording" button (red gradient) / "Stop & Process" button (cyan, with pulse animation)
  - "Push-to-Talk" toggle switch (default: on)
  - Live Transcript box (hidden by default, shows real-time STT output)

#### Panel C — Support Tools
6 tool buttons in a 2×2 grid:

| Tool | Icon | Action | Description |
|------|------|--------|-------------|
| Calm Me Down | 🧘 | `calm` | Instant centering prompts |
| Breathing Exercise | 🌬️ | `breathing` | Guided paced breathing |
| Journaling Prompt | 📝 | `journal` | Guided writing exercises |
| Self-Reflection | ❓ | `reflection` | Insightful growth queries |
| Mood Check-in | 📊 | `mood-checkin` | Assess emotional state |
| Session Summary | 📋 | `summary` | Analyze emotional timeline |

#### Panel D — Companion Status
| Field | ID | Highlight Color |
|-------|----|-----------------|
| Active Mode | `companionActiveMode` | Cyan |
| System Emotion | `companionCurrentEmotion` | Purple |
| Confidence | `companionEmotionConfidence` | Default |
| Safety State | `companionSafetyBadge` | Green/Yellow/Red badge |
| Listening Indicator | `indicatorMic` | Red flashing dot (when active) |
| Speaking Indicator | `indicatorSpeaker` | Green pulsing dot (when active) |
| Audio Meter | `audioMeterFill` | Cyan bar (shown during voice input) |
| Offline Badge | — | Green dot + "Offline Secured (No Cloud)" |

---

## Footer — Cognitive Input Console

### Left: Real-Time Thought Stream
- Vertical scrolling list of thought items
- Each item has a purple left border, timestamp, and thought text
- Shows internal cognitive processes in real-time

### Center: Cognitive Input Interface
1. **Input Type Selector** — 9 pill-shaped buttons:
   - Observation, Emotion, Memory, Belief, Goal, Question, Experience, Relationship Event, Environmental Event
2. **Text Input** — 3-row textarea for injecting thoughts
3. **Voice Input** — Microphone button (SVG icon) with listening animation
4. **Emotion Injection Sliders** — 8 sliders in a 2-column grid:

| Slider | ID | Default |
|--------|----|---------|
| Happiness | `sliderHappiness` | 50 |
| Sadness | `sliderSadness` | 20 |
| Fear | `sliderFear` | 15 |
| Anger | `sliderAnger` | 10 |
| Curiosity | `sliderCuriosity` | 70 |
| Trust | `sliderTrust` | 60 |
| Motivation | `sliderMotivation` | 65 |
| Stress | `sliderStress` | 30 |

5. **Submit Button** — "Inject Into Mind" with animated gradient border
6. **Processing Flow** — 7-step vertical flow (hidden until submit):
   - Input Received → Context Analysis → Belief Evaluation → Memory Storage → Emotion Update → Goal Assessment → Identity Impact
7. **Response Panel** — 5 analysis items (hidden until processing completes):
   - Detected Concepts, Affected Beliefs, Updated Emotions, Memory Impact, Predicted Outcome

### Right: Cognitive Influence Meter
5 radial canvas charts (120×120px each):
- Emotions, Goals, Identity, Beliefs, Memory

---

## Design System

### Color Palette

| Variable | Value | Usage |
|----------|-------|-------|
| `--bg-primary` | `#0a0a0f` | Page background |
| `--bg-secondary` | `#12121a` | Input backgrounds, bar tracks |
| `--bg-tertiary` | `#1a1a25` | Tertiary surfaces |
| `--glass-bg` | `rgba(255,255,255,0.03)` | Panel backgrounds |
| `--glass-border` | `rgba(255,255,255,0.08)` | Panel borders |
| `--neon-cyan` | `#00f0ff` | Primary accent (links, active states, highlights) |
| `--neon-blue` | `#0066ff` | Secondary accent (gradients) |
| `--neon-purple` | `#a855f7` | Tertiary accent (agent names, assistant bubbles) |
| `--neon-green` | `#00ff88` | Success/positive (status dot, confidence values) |
| `--neon-red` | `#ff3366` | Danger/negative (errors, stress, record button) |
| `--neon-orange` | `#ff9500` | Warning (fear, frustration, paused states) |
| `--text-primary` | `#e0e0e0` | Body text |
| `--text-secondary` | `#90909a` | Labels, muted text |

### Glass Effects
- `backdrop-filter: blur(20px)` on panels, sidebar, top bar
- `border: 1px solid rgba(255,255,255,0.08)` for subtle glass borders
- `box-shadow: 0 8px 32px rgba(0,0,0,0.2)` for depth

### Typography
- **Body**: `'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif`
- **Monospace** (clocks, values, timestamps): `'Courier New', monospace`
- **Section titles**: 1.75rem, 700 weight
- **Card headers**: 0.85rem, uppercase, letter-spacing 1px

### Gradient Text
Used on state values, identity values, metric values:
```css
background: linear-gradient(90deg, var(--neon-cyan), var(--neon-blue));
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### Emotion Bar Colors
Each emotion/need bar has a unique gradient + glow:

| Bar | Gradient |
|-----|----------|
| Curiosity, Exploration | Cyan → Blue |
| Fear, Security | Orange → Red |
| Confidence, Achievement | Green → #00d070 |
| Doubt | Orange → #cc7000 |
| Motivation, Autonomy | Purple → #7c3aed |
| Stress | #ff6b6b → Red |
| Trust, Social | #3b82f6 → Blue |
| Frustration | #f59e0b → Orange |
| Knowledge | #10b981 → Green |
| Stability | #6366f1 → #8b5cf6 |

### Animations

| Name | Effect | Usage |
|------|--------|-------|
| `pulse-glow` | Opacity 1→0.6→1 over 2s | Status dot, speaking indicator |
| `fadeIn` | Opacity 0→1 + translateY(10px→0) over 0.5s | Section transitions |
| `slideUpFade` | Opacity 0→1 + translateY(10px→0) over 0.4s | Chat message entrance |
| `borderPulse` | Background-position shift over 3s | Submit button border glow |
| `voicePulse` | Box-shadow ripple over 1.5s | Record stop button |
| `flash` | Opacity 0.2→1 alternating over 1s | Microphone indicator (listening) |

---

## Interactive Elements

### Toggle Switches
Custom iOS-style switches (40×20px):
- Off: gray dot on dark background
- On: cyan dot with cyan-tinted track

### Pill Buttons
Rounded (50px radius) filter/type selectors:
- Default: transparent with glass border
- Active: cyan border + cyan text + translucent cyan background

### Filter Buttons
Square (8px radius) filter toggles for Belief System:
- Same default/active pattern as pill buttons

### Session Buttons
- New Session: green text/border, green tint background
- End Session: red text/border, red tint background

### Sliders (Emotion Injection)
- Track: 8px height, dark background
- Thumb: 18px circle, cyan with glow shadow
- Value displayed in monospace cyan text to the right

---

## Responsive Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| **>1200px** | Full 3-column footer console; sidebar + main content layout |
| **≤1200px** | Footer console collapses to single column (center first, then sides); radial charts go horizontal |
| **≤1024px** | Companion grid collapses to single column (all 4 panels stack) |
| **≤768px** | Sidebar becomes horizontal scrollable bar at top; top bar stacks vertically; grids collapse to single column; emotion sliders go single column |

---

## Internationalization (i18n)

- **Languages**: English (`en`) and Bangla/Bengali (`bn_bd`)
- **Toggle**: Button in top-right corner switches between languages
- **Mechanism**: Elements use `data-i18n` attributes for text content and `data-i18n-placeholder` for placeholders
- **Storage**: Language preference persisted in `localStorage` (`cognitiveMindLanguage`)
- **Translation files**: `frontend/languages/en.json` and `frontend/languages/bn_bd.json`
- **Embedded**: `script.js` also contains an embedded translations object for fallback

---

## Key DOM IDs Reference

### Dashboard
`cognitiveState`, `dominantEmotion`, `dominantGoal`, `confidenceLevel`, `stabilityScore`, `cognitiveEnergy`, `energyFill`, `stepCounter`

### Emotion Panel
`curiosityFill`, `fearFill`, `confidenceFill`, `doubtFill`, `motivationFill`, `stressFill`, `trustFill`, `frustrationFill` + corresponding `*Percent` elements

### Companion
`companionChatContainer`, `companionTextMsg`, `companionSendBtn`, `startSessionBtn`, `endSessionBtn`, `modeSelector`, `speakResponseToggle`, `voiceStartBtn`, `voiceStopBtn`, `pttToggle`, `liveTranscriptBox`, `liveTranscriptText`, `companionActiveMode`, `companionCurrentEmotion`, `companionEmotionConfidence`, `companionSafetyBadge`, `indicatorMic`, `indicatorSpeaker`, `audioMeterFill`

### Footer Console
`thoughtStream`, `cognitiveInput`, `micBtn`, `submitBtn`, `sliderHappiness`–`sliderStress` (+ `*Val` elements), `processingFlow` (steps `step1`–`step7`), `responsePanel` (`responseConcepts`, `responseBeliefs`, `responseEmotions`, `responseMemory`, `responsePrediction`)

### Canvas Elements
`knowledgeGraph`, `radialEmotion`, `radialGoals`, `radialIdentity`, `radialBeliefs`, `radialMemory`

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `frontend/index.html` | 709 | HTML structure, all sections and elements |
| `frontend/style.css` | 1857 | Complete styling, design system, responsive rules |
| `frontend/script.js` | 1500 | App logic, API calls, DOM manipulation, i18n, simulations |
| `frontend/languages/en.json` | 222 | English translation strings |
| `frontend/languages/bn_bd.json` | — | Bangla translation strings |
