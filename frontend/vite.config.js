/**
 * Vite Configuration
 *
 * Documentation: https://vitejs.dev/config/
 */

import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    open: true  // Auto-open browser on start
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
