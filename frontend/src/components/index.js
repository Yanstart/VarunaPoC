/**
 * Components Module Exports
 *
 * Centralized exports for UI components.
 *
 * @module components
 *
 * @example
 * import { CompareLayout, ViewerPanel, SyncControls } from './components';
 */

export { CompareLayout } from './CompareLayout.js';
export { ViewerPanel } from './ViewerPanel.js';
export { SyncControls } from './SyncControls.js';
export { createFolderBrowser } from './FolderBrowser.js';

// Legacy exports for backward compatibility
export {
    initViewer,
    loadSlideWithTiles,
    loadOverview,
    getLegacyViewer,
    destroyLegacyViewer
} from './Viewer.js';
