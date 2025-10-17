# Frontend - Vite + Vanilla JS + OpenSeadragon

## Purpose
Web-based viewer interface for histological slides.
Displays slide list and overview using OpenSeadragon.

## Contents
- `index.html` - Entry HTML
- `vite.config.js` - Vite configuration
- `package.json` - Dependencies
- `src/` - Source code
  - `main.js` - Application entry point
  - `style.css` - Global styles
  - `components/` - UI components
    - `SlideList.js` - Slide selection sidebar
    - `Viewer.js` - OpenSeadragon viewer wrapper
  - `utils/` - Utilities
    - `api.js` - Backend API client

## Dependencies
- **OpenSeadragon:** Gigapixel image viewer (Google Maps-like navigation)
- **Vite:** Modern build tool and dev server

Official documentation:
- OpenSeadragon: https://openseadragon.github.io/docs/
- Vite: https://vitejs.dev/

## Installation

```bash
cd frontend
npm install
```

## Usage

### Start development server
```bash
npm run dev
```

Opens browser automatically at http://localhost:5173

### Build for production
```bash
npm run build
```

Output in `dist/` directory.

### Preview production build
```bash
npm run preview
```

## Technical Notes

### Phase 1 Simplifications
- **No framework:** Vanilla JavaScript (no React/Vue/Svelte)
- **Simple image mode:** OpenSeadragon displays overview as single image (not DZI tiles)
- **No state management:** Direct DOM manipulation
- **No routing:** Single-page, no URL navigation

### Component Architecture
Components are simple functions that return DOM elements:
```javascript
export function createComponent(data, callback) {
    const element = document.createElement('div');
    // ... setup element ...
    return element;
}
```

No classes, no complex patterns. Keep it simple.

### OpenSeadragon Configuration
- **showNavigator:** true → Mini-map displays overview
- **navigatorPosition:** BOTTOM_RIGHT
- **Main area:** Black placeholder (Phase 2 will add DZI tiling)

### API Communication
- All calls to http://localhost:8000
- Fetch API (native, no axios)
- Error handling via try/catch

## Development Workflow

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Select slide → Overview appears in mini-map

## Last Updated
2025-10-17 - Phase 1 Hello World
