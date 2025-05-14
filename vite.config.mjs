import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  base: '/static/',
  plugins: [react()],
  build: {
    outDir: './assets/',
    assetsDir: 'django-vite/',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        opr_review: resolve('./dataedit/static/peer_review/main.js'),
      },
    },
  }
})
