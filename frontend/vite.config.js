import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  // La demo se publica en GitHub Pages bajo /expertak-erp/
  base: process.env.VITE_BASE || '/',
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost/expertak',
        changeOrigin: true
      }
    }
  }
});
