# Design Specifications - Enhanced Blocked Pages

## Design Philosophy

The blocked page experience should be:
- **Clear & Honest**: Users should immediately understand they've been intentionally blocked
- **Educational**: Provide context and teach digital wellness
- **Respectful**: Treat users with dignity, avoiding condescending language
- **Age-Appropriate**: Match visual style and messaging to user age
- **Accessible**: WCAG 2.1 AA compliant for all users
- **Performant**: Fast loading, smooth animations, responsive design

---

## Design System

### Color Palette

#### Default Theme
```css
/* Primary Colors */
--primary-blue: #4F46E5;      /* Indigo 600 - Trust, authority */
--primary-blue-light: #818CF8; /* Indigo 400 - Highlights */
--primary-blue-dark: #3730A3;  /* Indigo 800 - Depth */

/* Status Colors */
--status-blocked: #DC2626;     /* Red 600 - Blocked state */
--status-warning: #F59E0B;     /* Amber 500 - Warning */
--status-info: #3B82F6;        /* Blue 500 - Information */
--status-success: #10B981;     /* Green 500 - Success */

/* Neutral Colors */
--gray-50: #F9FAFB;
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;
--gray-300: #D1D5DB;
--gray-500: #6B7280;
--gray-700: #374151;
--gray-900: #111827;

/* Gradients */
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-warning: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
--gradient-info: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
```

#### Kids Theme (Ages 6-11)
```css
/* Bright, Playful Colors */
--primary: #FF6B9D;           /* Pink - Friendly */
--secondary: #FDB750;         /* Orange - Energetic */
--accent: #A78BFA;            /* Purple - Fun */
--background: #FFF8F0;        /* Warm beige */

/* Softer blocked state */
--status-blocked: #FF6B9D;    /* Gentler red/pink */
```

#### Teens Theme (Ages 12-17)
```css
/* Modern, Minimalist Colors */
--primary: #06B6D4;           /* Cyan - Modern */
--secondary: #8B5CF6;         /* Purple - Cool */
--accent: #10B981;            /* Green - Fresh */
--background: #FFFFFF;        /* Clean white */

/* Muted blocked state */
--status-blocked: #EF4444;    /* Clear red, not harsh */
```

#### Dark Mode
```css
/* Dark Background Palette */
--bg-primary: #1F2937;        /* Gray 800 */
--bg-secondary: #111827;      /* Gray 900 */
--bg-elevated: #374151;       /* Gray 700 */

/* Adjusted text colors */
--text-primary: #F9FAFB;      /* Gray 50 */
--text-secondary: #D1D5DB;    /* Gray 300 */

/* Status colors (slightly brighter for dark bg) */
--status-blocked: #F87171;    /* Red 400 */
--status-info: #60A5FA;       /* Blue 400 */
```

### Typography

#### Font Stack
```css
/* Primary Font: System Font Stack for performance */
--font-family-base: -apple-system, BlinkMacSystemFont, "Segoe UI",
                    Roboto, "Helvetica Neue", Arial, sans-serif;

/* Optional: Custom Font for Headings (if needed) */
--font-family-heading: "Inter", var(--font-family-base);

/* Monospace for technical info */
--font-family-mono: "SF Mono", Monaco, "Cascadia Code", monospace;
```

#### Font Sizes
```css
/* Type Scale (1.250 - Major Third) */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */
--text-5xl: 3rem;        /* 48px */

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

#### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System

```css
/* 8px base unit */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
```

### Border Radius

```css
--radius-sm: 0.25rem;   /* 4px - Buttons, badges */
--radius-md: 0.5rem;    /* 8px - Cards, inputs */
--radius-lg: 0.75rem;   /* 12px - Modals */
--radius-xl: 1rem;      /* 16px - Large cards */
--radius-full: 9999px;  /* Full circle */
```

### Shadows

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

### Animations

```css
/* Timing Functions */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);

/* Durations */
--duration-fast: 150ms;
--duration-normal: 300ms;
--duration-slow: 500ms;
```

---

## Template Designs

### 1. Time-Restricted Blocking Page

**Use Case**: Website blocked due to time schedule

**Visual Elements**:
- Large clock icon (animated ticking)
- Current time display
- Next available time (countdown)
- Schedule visualization (timeline/calendar)

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  [Logo]                    Ubuntu Parental      │
├─────────────────────────────────────────────────┤
│                                                  │
│              ⏰ (Animated Clock Icon)            │
│                                                  │
│              Time Restriction Active             │
│                                                  │
│          🚫 youtube.com is not available         │
│                                                  │
│     Access is restricted during school hours     │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Next Available: Today at 4:00 PM          │ │
│  │  ⏱️ Unlocks in: 2 hours 15 minutes         │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌─── Your Schedule ───────────────────────┐   │
│  │ Mon-Fri:  4:00 PM - 8:00 PM             │   │
│  │ Sat-Sun:  10:00 AM - 9:00 PM            │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  [Request Access]           [View Schedule]     │
│                                                  │
│  💡 Suggested Activities:                       │
│  • Read a book                                  │
│  • Play outside                                 │
│  • Practice an instrument                       │
│                                                  │
├─────────────────────────────────────────────────┤
│  Protected by Ubuntu Parental Control           │
└─────────────────────────────────────────────────┘
```

**Color Scheme**:
- Primary: Info blue
- Icon: Animated gradient
- Background: Light gray with subtle pattern

**Interactions**:
- Real-time countdown timer
- Hover effects on buttons
- Animated clock icon
- Collapsible schedule view

---

### 2. Category-Based Blocking Page

**Use Case**: Website blocked due to content category (social media, gaming, adult, etc.)

**Visual Elements**:
- Category-specific icon
- Color-coded by category type
- Brief explanation
- Alternative suggestions

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  [Logo]                    Ubuntu Parental      │
├─────────────────────────────────────────────────┤
│                                                  │
│              🛡️ (Shield Icon)                   │
│                                                  │
│              Content Blocked                     │
│                                                  │
│       This website is in a blocked category      │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  🎮 Gaming & Entertainment                 │ │
│  │  facebook.com                              │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  This category is blocked to help you focus     │
│  on your studies and reduce distractions.       │
│                                                  │
│  [Request Access]           [Report Error]      │
│                                                  │
│  ✅ Try These Instead:                          │
│  • Khan Academy - Learn anything                │
│  • Duolingo - Learn languages                   │
│  • Scratch - Creative coding                    │
│                                                  │
│  📚 Why is this blocked?                        │
│  Your parents have chosen to limit access to    │
│  gaming and social media sites during study     │
│  hours to help you stay focused.                │
│                                                  │
├─────────────────────────────────────────────────┤
│  Protected by Ubuntu Parental Control           │
└─────────────────────────────────────────────────┘
```

**Category Colors**:
```css
.category-social-media { --accent: #FF6B9D; /* Pink */ }
.category-gaming { --accent: #A78BFA; /* Purple */ }
.category-video { --accent: #F59E0B; /* Amber */ }
.category-adult { --accent: #DC2626; /* Red */ }
.category-gambling { --accent: #F97316; /* Orange */ }
.category-malware { --accent: #EF4444; /* Bright Red */ }
```

**Interactions**:
- Expandable "Why is this blocked?" section
- Clickable alternative suggestions
- Feedback form for incorrect blocks

---

### 3. Manual Block Page

**Use Case**: Parent manually blocked specific site

**Visual Elements**:
- Lock icon
- Custom parent message (if provided)
- More personal tone
- Direct parent contact option

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  [Logo]                    Ubuntu Parental      │
├─────────────────────────────────────────────────┤
│                                                  │
│              🔒 (Lock Icon)                      │
│                                                  │
│              Access Not Allowed                  │
│                                                  │
│       This website has been blocked by your      │
│                   parent                         │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  📝 Message from Parent:                   │ │
│  │                                            │ │
│  │  "This website is not appropriate for our  │ │
│  │  family values. If you need access for     │ │
│  │  school, please ask me directly."          │ │
│  │                                            │ │
│  │  - Mom                                     │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  [Request Access]     [Talk to Parent]          │
│                                                  │
│  💬 Need to discuss this?                       │
│  Your parent is available to talk about why     │
│  this site is blocked and when access might     │
│  be appropriate.                                │
│                                                  │
├─────────────────────────────────────────────────┤
│  Protected by Ubuntu Parental Control           │
└─────────────────────────────────────────────────┘
```

**Features**:
- Custom message editor in admin panel
- Option to include parent's name/signature
- Warm, personal tone
- Emphasis on communication

---

### 4. Age-Restricted Content Page

**Use Case**: Content inappropriate for user's age

**Visual Elements**:
- Age-appropriate warning icon
- Educational messaging
- Online safety tips
- Report inappropriate content option

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  [Logo]                    Ubuntu Parental      │
├─────────────────────────────────────────────────┤
│                                                  │
│              ⚠️ (Warning Icon)                   │
│                                                  │
│         Content Not Age-Appropriate              │
│                                                  │
│     This website contains content that may       │
│         not be suitable for your age             │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  🔞 Age Restriction: 18+                   │ │
│  │  example-site.com                          │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  🛡️ Staying Safe Online:                        │
│  • Not all content online is appropriate        │
│  • Your parents help protect you                │
│  • Talk to an adult if you see something        │
│    that makes you uncomfortable                 │
│                                                  │
│  [Talk to Parent]      [Report Site]            │
│                                                  │
│  📚 Learn More:                                 │
│  • Common Sense Media - Internet Safety         │
│  • NetSmartz - Be Web Wise                      │
│                                                  │
├─────────────────────────────────────────────────┤
│  Protected by Ubuntu Parental Control           │
└─────────────────────────────────────────────────┘
```

**Age-Appropriate Messaging**:

**Ages 6-9**:
- Very simple language
- Friendly, reassuring tone
- Emphasis on "ask your parents"
- Colorful, cartoon-style icons

**Ages 10-13**:
- Clear, straightforward language
- Educational focus
- More context about why protection matters
- Modern, clean icons

**Ages 14-17**:
- Mature, respectful tone
- Detailed explanations
- Focus on digital citizenship
- Minimalist design

---

## Component Library

### 1. Header Component

**Purpose**: Consistent branding across all blocked pages

```html
<header class="blocked-header">
  <div class="header-content">
    <img src="/static/images/logo.svg" alt="Logo" class="logo">
    <span class="product-name">Ubuntu Parental Control</span>
  </div>
</header>
```

**CSS**:
```css
.blocked-header {
  padding: var(--space-4) var(--space-6);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--gray-200);
}

.logo {
  height: 32px;
  width: auto;
}

.product-name {
  font-size: var(--text-sm);
  color: var(--gray-600);
  font-weight: var(--font-medium);
}
```

---

### 2. Icon Container

**Purpose**: Consistent icon display with animation

```html
<div class="icon-container">
  <div class="icon-bg">
    <svg class="icon">
      <!-- Icon SVG content -->
    </svg>
  </div>
</div>
```

**CSS**:
```css
.icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-6);
}

.icon-bg {
  width: 120px;
  height: 120px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: pulse 2s ease-in-out infinite;
}

.icon {
  width: 64px;
  height: 64px;
  color: white;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}
```

---

### 3. Info Card Component

**Purpose**: Display key information in a card format

```html
<div class="info-card">
  <div class="info-card-icon">
    <svg><!-- Icon --></svg>
  </div>
  <div class="info-card-content">
    <h3 class="info-card-title">Card Title</h3>
    <p class="info-card-text">Card content goes here</p>
  </div>
</div>
```

**CSS**:
```css
.info-card {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.info-card-icon {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-card-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--gray-900);
  margin-bottom: var(--space-2);
}

.info-card-text {
  font-size: var(--text-sm);
  color: var(--gray-600);
  line-height: var(--leading-relaxed);
}
```

---

### 4. Button Component

**Purpose**: Consistent, accessible buttons

```html
<!-- Primary Button -->
<button class="btn btn-primary">
  <span>Request Access</span>
</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">
  <span>Go Back</span>
</button>

<!-- Ghost Button -->
<button class="btn btn-ghost">
  <span>Learn More</span>
</button>
```

**CSS**:
```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  border: none;
  position: relative;
  overflow: hidden;
}

/* Primary Button */
.btn-primary {
  background: var(--primary-blue);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-blue-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}

/* Secondary Button */
.btn-secondary {
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
}

.btn-secondary:hover {
  background: var(--gray-50);
  border-color: var(--gray-400);
}

/* Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--primary-blue);
}

.btn-ghost:hover {
  background: var(--gray-100);
}

/* Ripple Effect */
.btn::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  pointer-events: none;
  background-image: radial-gradient(circle, #fff 10%, transparent 10.01%);
  background-repeat: no-repeat;
  background-position: 50%;
  transform: scale(10, 10);
  opacity: 0;
  transition: transform 0.5s, opacity 1s;
}

.btn:active::after {
  transform: scale(0, 0);
  opacity: 0.3;
  transition: 0s;
}
```

---

### 5. Countdown Timer Component

**Purpose**: Display time until access is available

```html
<div class="countdown-timer">
  <div class="countdown-label">Unlocks in:</div>
  <div class="countdown-display">
    <div class="countdown-unit">
      <span class="countdown-value" data-hours>2</span>
      <span class="countdown-unit-label">hours</span>
    </div>
    <span class="countdown-separator">:</span>
    <div class="countdown-unit">
      <span class="countdown-value" data-minutes>15</span>
      <span class="countdown-unit-label">minutes</span>
    </div>
    <span class="countdown-separator">:</span>
    <div class="countdown-unit">
      <span class="countdown-value" data-seconds>30</span>
      <span class="countdown-unit-label">seconds</span>
    </div>
  </div>
</div>
```

**CSS**:
```css
.countdown-timer {
  text-align: center;
  padding: var(--space-6);
  background: var(--gradient-info);
  border-radius: var(--radius-lg);
  color: white;
}

.countdown-label {
  font-size: var(--text-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3);
  opacity: 0.9;
}

.countdown-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}

.countdown-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.countdown-value {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: 1;
  min-width: 2ch;
  font-variant-numeric: tabular-nums;
}

.countdown-unit-label {
  font-size: var(--text-xs);
  margin-top: var(--space-1);
  opacity: 0.8;
}

.countdown-separator {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  margin: 0 var(--space-1);
}
```

**JavaScript**:
```javascript
class CountdownTimer {
  constructor(element, targetTime) {
    this.element = element;
    this.targetTime = new Date(targetTime);
    this.hoursEl = element.querySelector('[data-hours]');
    this.minutesEl = element.querySelector('[data-minutes]');
    this.secondsEl = element.querySelector('[data-seconds]');
    this.start();
  }

  start() {
    this.update();
    this.interval = setInterval(() => this.update(), 1000);
  }

  update() {
    const now = new Date();
    const diff = this.targetTime - now;

    if (diff <= 0) {
      this.stop();
      location.reload(); // Reload to show access granted
      return;
    }

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    this.hoursEl.textContent = String(hours).padStart(2, '0');
    this.minutesEl.textContent = String(minutes).padStart(2, '0');
    this.secondsEl.textContent = String(seconds).padStart(2, '0');
  }

  stop() {
    clearInterval(this.interval);
  }
}
```

---

### 6. Access Request Form

**Purpose**: Allow users to request temporary access

```html
<form class="access-request-form" method="POST" action="/api/request-access">
  <h3>Request Temporary Access</h3>

  <div class="form-group">
    <label for="request-reason">Why do you need access?</label>
    <textarea
      id="request-reason"
      name="reason"
      required
      placeholder="Example: I need to research for my history project"
      maxlength="500"
    ></textarea>
    <span class="form-help">Be specific to help your parent make a decision</span>
  </div>

  <div class="form-group">
    <label for="request-duration">How long do you need? (minutes)</label>
    <select id="request-duration" name="duration" required>
      <option value="15">15 minutes</option>
      <option value="30" selected>30 minutes</option>
      <option value="60">1 hour</option>
      <option value="120">2 hours</option>
    </select>
  </div>

  <div class="form-actions">
    <button type="button" class="btn btn-secondary" onclick="closeForm()">
      Cancel
    </button>
    <button type="submit" class="btn btn-primary">
      Send Request
    </button>
  </div>

  <div class="form-notice">
    Your parent will be notified and can approve or deny your request.
  </div>
</form>
```

**CSS**:
```css
.access-request-form {
  background: white;
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: var(--space-5);
}

.form-group label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--gray-700);
  margin-bottom: var(--space-2);
}

.form-group textarea,
.form-group select {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-family: var(--font-family-base);
  transition: border-color var(--duration-fast);
}

.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.form-help {
  display: block;
  font-size: var(--text-xs);
  color: var(--gray-500);
  margin-top: var(--space-1);
}

.form-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.form-actions .btn {
  flex: 1;
}

.form-notice {
  margin-top: var(--space-4);
  padding: var(--space-3);
  background: var(--gray-50);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--gray-600);
  text-align: center;
}
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
/* Base styles: Mobile (< 640px) */

/* Tablet: 640px and up */
@media (min-width: 640px) {
  :root {
    --text-base: 1.0625rem; /* 17px */
  }
}

/* Desktop: 1024px and up */
@media (min-width: 1024px) {
  :root {
    --text-base: 1.125rem; /* 18px */
  }
}

/* Large Desktop: 1280px and up */
@media (min-width: 1280px) {
  .blocked-page-container {
    max-width: 1200px;
  }
}
```

### Mobile Optimizations

```css
/* Touch-friendly tap targets */
@media (max-width: 640px) {
  .btn {
    min-height: 44px; /* iOS recommended minimum */
    padding: var(--space-3) var(--space-4);
  }

  /* Stack buttons vertically on mobile */
  .form-actions {
    flex-direction: column;
  }

  /* Larger text for readability */
  .blocked-title {
    font-size: var(--text-3xl);
  }

  /* Reduce spacing on mobile */
  .blocked-page-container {
    padding: var(--space-4);
  }
}
```

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

#### 1. Color Contrast

All text must meet minimum contrast ratios:
- **Normal text (< 18px)**: 4.5:1 contrast ratio
- **Large text (≥ 18px)**: 3:1 contrast ratio
- **UI components**: 3:1 contrast ratio

```css
/* Example: Ensuring sufficient contrast */
.text-on-dark {
  color: #FFFFFF; /* White on dark background */
  /* Contrast ratio: 21:1 (Exceeds 4.5:1 requirement) */
}

.text-on-light {
  color: #1F2937; /* Dark gray on light background */
  /* Contrast ratio: 16:1 (Exceeds 4.5:1 requirement) */
}
```

#### 2. Keyboard Navigation

All interactive elements must be keyboard accessible:

```css
/* Visible focus indicators */
*:focus {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}

/* Skip to content link for keyboard users */
.skip-to-content {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--primary-blue);
  color: white;
  padding: var(--space-2) var(--space-4);
  text-decoration: none;
  z-index: 100;
}

.skip-to-content:focus {
  top: 0;
}
```

#### 3. Screen Reader Support

```html
<!-- Semantic HTML -->
<main role="main" aria-labelledby="page-title">
  <h1 id="page-title">Page Blocked</h1>

  <!-- Hidden text for screen readers -->
  <span class="sr-only">
    This page has been blocked by parental controls
  </span>

  <!-- ARIA labels for icons -->
  <svg aria-label="Clock icon indicating time restriction" role="img">
    <!-- Icon path -->
  </svg>

  <!-- Form accessibility -->
  <form aria-label="Request temporary access form">
    <label for="reason">
      Reason for request
      <span aria-required="true">*</span>
    </label>
    <textarea
      id="reason"
      aria-describedby="reason-help"
      required
    ></textarea>
    <span id="reason-help" class="form-help">
      Explain why you need access to this website
    </span>
  </form>
</main>
```

```css
/* Screen reader only text */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

#### 4. Reduced Motion

Respect user's motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }

  /* Disable pulsing animations */
  .icon-bg {
    animation: none;
  }
}
```

---

## Performance Guidelines

### Asset Optimization

1. **Images**:
   - Use SVG for icons and illustrations
   - Optimize SVGs with SVGO
   - Use WebP format with PNG fallback
   - Lazy load images below the fold

2. **CSS**:
   - Inline critical CSS (above-the-fold)
   - Defer non-critical CSS
   - Minify and compress
   - Remove unused styles

3. **JavaScript**:
   - Defer non-critical scripts
   - Use async for independent scripts
   - Minify and compress
   - Code split if bundle > 100KB

### Loading Strategy

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Blocked</title>

  <!-- Critical CSS inline -->
  <style>
    /* Critical above-the-fold styles */
  </style>

  <!-- Preload key assets -->
  <link rel="preload" href="/static/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>

  <!-- Defer non-critical CSS -->
  <link rel="preload" href="/static/css/blocked_pages.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/static/css/blocked_pages.css"></noscript>
</head>
<body>
  <!-- Content -->

  <!-- Defer JavaScript -->
  <script src="/static/js/blocked_interactions.js" defer></script>
</body>
</html>
```

### Target Metrics

- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.0s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Total Bundle Size**: < 150KB (compressed)

---

## Design Deliverables Checklist

- [ ] Complete design system documentation
- [ ] Color palette with accessibility verification
- [ ] Typography scale and font files
- [ ] Component library with code examples
- [ ] 4 main template designs (high-fidelity mockups)
- [ ] Responsive breakpoint designs
- [ ] Dark mode variations
- [ ] Age-specific theme variations
- [ ] Icon set (SVG format)
- [ ] Illustration set (SVG format)
- [ ] Animation specifications
- [ ] Accessibility audit report
- [ ] Performance optimization checklist
- [ ] Browser compatibility matrix

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Status**: Draft - Pending Design Review
