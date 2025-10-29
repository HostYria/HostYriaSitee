# Python Hostfly Design Guidelines

## Design Approach

**Selected Approach**: Design System with Developer Tool Aesthetics

Drawing inspiration from modern developer platforms (GitHub, Vercel, Railway, Linear) combined with Material Design principles for structure. This platform prioritizes clarity, efficiency, and technical precision over visual flair.

**Core Principles**:
- Information density without clutter
- Terminal-inspired aesthetics for technical credibility
- Efficient workflows with minimal friction
- Clear visual hierarchy for complex data

---

## Typography System

**Font Families**:
- **UI Text**: Inter (Google Fonts) - all interface elements, buttons, labels
- **Code/Technical**: JetBrains Mono (Google Fonts) - file names, logs, code snippets, technical values
- **Headings**: Inter - maintaining consistency

**Type Scale**:
- Page Titles: text-4xl font-bold
- Section Headers: text-2xl font-semibold
- Card Titles: text-lg font-medium
- Body Text: text-base
- Captions/Meta: text-sm
- Code/Logs: text-sm font-mono

---

## Layout System

**Spacing Primitives**: Tailwind units of 2, 4, 6, 8, and 12
- Component padding: p-4 to p-6
- Section spacing: py-12 to py-20
- Card gaps: gap-4 to gap-6
- Icon-text gaps: gap-2

**Container Strategy**:
- Marketing pages: max-w-7xl
- Dashboard content: max-w-screen-2xl (wider for data)
- Settings forms: max-w-3xl
- Code blocks: w-full with horizontal scroll

---

## Component Library

### Navigation
**Header** (all pages):
- Logo "Python Hostfly" with simple Python icon (Font Awesome)
- Primary nav: Home, Docs, Pricing, GitHub
- Right-aligned: User avatar dropdown OR Sign In/Sign Up buttons
- Sticky position with subtle bottom border
- Height: h-16

**Dashboard Sidebar** (logged-in views):
- Fixed left sidebar, width: w-64
- Navigation items with icons (Heroicons):
  - Repositories (folder icon)
  - Settings (cog icon)
  - Billing (credit card icon)
  - Documentation (book icon)
- Active state: subtle background fill
- Collapse button for mobile

### Landing Page Structure

**Hero Section** (py-20 to py-32):
- Left-aligned content (60% width on desktop)
- Headline: "Host & Run Python Projects in the Cloud"
- Subheadline: "Deploy bots, scripts, and applications with real-time logs and environment management"
- CTA buttons: "Start Free" (primary) + "View Docs" (secondary) with gap-4
- Right side: Terminal window mockup showing code execution with live logs effect
- No background image - clean gradient or solid treatment

**Features Grid** (py-20):
- 3-column grid (lg:grid-cols-3, md:grid-cols-2, grid-cols-1)
- Each feature card:
  - Icon at top (Heroicons: server, code, chart-bar, shield-check, etc.)
  - Feature title (text-xl font-semibold)
  - 2-3 sentence description
  - Subtle border and padding (p-6)
- Features: Real-time Execution, Live Logs, Environment Variables, Multiple Python Versions, Database Integration, 24/7 Uptime

**How It Works** (py-20):
- Numbered steps in 3-column layout
- Large step numbers (text-6xl, semi-transparent)
- Step titles and descriptions
- Steps: 1. Create Repository → 2. Upload Files → 3. Configure & Deploy

**Pricing Section** (py-20):
- 3-column pricing cards (Free, Pro, Enterprise)
- Card structure: Plan name, price (text-4xl), feature list with checkmarks (Heroicons check icon), CTA button
- Recommended plan: subtle highlight treatment

**CTA Section** (py-16):
- Centered content
- Bold headline: "Ready to Deploy Your Python Projects?"
- Primary CTA button
- Supporting text: "No credit card required"

**Footer**:
- 4-column layout: Product (Features, Pricing, Docs), Company (About, Blog, Contact), Resources (API, Status, Support), Legal (Privacy, Terms)
- Bottom bar: Copyright, social icons (GitHub, Twitter, Discord)

### Dashboard Views

**Repositories List** (main dashboard):
- Header with "Your Repositories" + "New Repository" button (right-aligned)
- Search/filter bar (mb-6)
- Repository cards grid (grid-cols-1 lg:grid-cols-2, gap-4):
  - Repository name (text-lg font-semibold with folder icon)
  - Status indicator: Running (green dot) / Stopped (gray dot) / Error (red dot)
  - Meta row: Python version badge, last updated timestamp, file count
  - Action buttons: View Logs, Settings, Stop/Start (icon buttons, gap-2)
  - Card padding: p-6, subtle border

**Repository Detail Page**:
Left content area (flex-1):
- Breadcrumb: Repositories > {repo_name}
- Status banner: prominent status with start/stop button
- Tabbed interface (border-b with active indicator):
  - Files tab
  - Logs tab
  - Settings tab

**Files Tab**:
- File browser list with file icons (code, json, text)
- Each row: icon, filename (font-mono), file size, last modified
- Upload button (top-right)
- Rows: hover state, clickable

**Logs Tab**:
- Terminal-style container:
  - Background: dark treatment with monospace text
  - Auto-scrolling log entries
  - Timestamp prefix for each log line
  - Controls: Clear Logs, Download Logs, Auto-scroll toggle (top-right)
  - Height: min-h-96 with scroll
  - Live update indicator (pulsing dot when active)

**Settings Tab**:
Form layout with sections:
- **Execution Settings** (mb-8):
  - Main File dropdown (select from uploaded .py files)
  - Python Version selector (dropdown with versions: 3.8, 3.9, 3.10, 3.11, 3.12)
  
- **Environment Variables** (mb-8):
  - Table layout: Key | Value | Actions
  - Add Variable button
  - Each row: text inputs with delete icon button
  - Database URL helper text: "Add DATABASE_URL for database connections"

- **Danger Zone**:
  - Delete Repository button (destructive styling)
  - Confirmation required

Save Changes button (sticky bottom or top-right)

### Forms & Inputs

**Text Inputs**:
- Height: h-10 to h-12
- Padding: px-4
- Border radius: rounded-md
- Labels above inputs (text-sm font-medium, mb-2)
- Helper text below (text-sm, subtle)

**Buttons**:
- Primary: px-6 py-2.5, rounded-md, font-medium
- Secondary: Same sizing, border variant
- Icon buttons: p-2, rounded
- Destructive: Use for delete actions

**Dropdowns/Selects**:
- Match text input styling
- Chevron icon indicator

**Toggle Switches**:
- For on/off settings (auto-scroll, etc.)
- Clear visual states

### Status Indicators

**Badges**:
- Running: pill shape with dot
- Stopped: pill shape with dot
- Error: pill shape with dot
- Python version: outlined badge (e.g., "Python 3.11")

**Progress & Loading**:
- Spinner for async operations
- Progress bars for uploads
- Skeleton loaders for data fetching

---

## Images

**Hero Section**: Terminal window mockup showing:
- Code editor interface with Python code visible
- Terminal panel below showing live logs scrolling
- File structure sidebar
- Use screenshot or designed mockup of actual IDE-like interface
- Placement: Right side of hero, 40% width, slight tilt or elevation for depth

**Optional Feature Icons**: Use actual screenshot snippets of terminal logs, code editor, or dashboard UI to showcase real interface in feature cards

---

## Accessibility

- All interactive elements keyboard navigable
- Form inputs with associated labels
- Icon buttons with aria-labels
- Status indicators with text alternatives
- Sufficient contrast ratios for readability
- Focus indicators on all interactive elements

---

## Key UX Patterns

**Empty States**: 
- No repositories: Centered illustration with "Create Your First Repository" CTA
- No logs yet: "Waiting for application output..." with loading indicator

**Confirmation Modals**:
- Destructive actions (delete repository, stop running process)
- Modal overlay with clear action buttons

**Real-time Updates**:
- WebSocket connection indicator
- Live log streaming with auto-scroll
- Status changes reflect immediately

**File Upload**:
- Drag-and-drop zone in files tab
- File type validation (show supported: .py, .txt, .json)
- Upload progress indication

---

This design creates a professional, developer-focused platform that balances technical functionality with modern aesthetics, ensuring efficient workflows for managing Python projects in the cloud.