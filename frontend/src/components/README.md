# Components

## Purpose
Reusable UI components using Vanilla JavaScript.

## Contents
- `SlideList.js` - Sidebar component displaying available slides
- `Viewer.js` - OpenSeadragon viewer wrapper

## Design Pattern
Simple function-based components:
- Accept data and callbacks as parameters
- Return DOM elements ready to insert
- No state management (parent handles state)
- No classes or complex OOP

## Technical Notes

### SlideList.js
- Generates `<ul>` with slides
- Manages .active state for selection
- Calls callback on click

### Viewer.js
- Wraps OpenSeadragon initialization
- Provides `loadOverview()` helper
- Phase 1: Simple image mode
- Phase 2: Will add DZI tiling support
