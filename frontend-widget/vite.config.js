import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

/**
 * Vite Configuration for PDBOT Widget
 * 
 * Builds a standalone widget bundle that can be embedded in any website.
 * Output: dist/pdbot-widget.js (single file bundle)
 */
export default defineConfig({
  plugins: [react()],
  
  // Build configuration for widget bundle
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.jsx'),
      name: 'PDBOTWidget',
      fileName: 'pdbot-widget',
      formats: ['iife'] // Immediately Invoked Function Expression for browser
    },
    rollupOptions: {
      // Bundle React into the widget (no external dependencies)
      external: [],
      output: {
        // Single file output
        inlineDynamicImports: true,
        // Global variable name
        name: 'PDBOTWidget',
        // CSS injected into JS
        assetFileNames: 'pdbot-widget.[ext]'
      }
    },
    // Output directory
    outDir: 'dist',
    // Generate sourcemaps for debugging
    sourcemap: true,
    // Minify for production
    minify: 'terser'
  },
  
  // Development server configuration
  server: {
    port: 3000,
    host: true, // Expose to network
    open: true,
    // Allow tunnel hosts (Cloudflare, localtunnel, etc.)
    allowedHosts: 'all',
    // Proxy API requests to backend during development
    proxy: {
      '/chat': {
        target: 'http://localhost:8501',
        changeOrigin: true
      },
      '/feedback': {
        target: 'http://localhost:8501',
        changeOrigin: true
      }
    }
  },
  
  // CSS configuration
  css: {
    modules: false // Use regular CSS, not CSS modules
  }
});
