// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  base: '/static/',
  plugins: [
    react({
      // Emotion JSX factory & css prop
      jsxImportSource: '@emotion/react',
      babel: {
        plugins: ['@emotion/babel-plugin'],
      },
    }),
  ],
  optimizeDeps: {
    include: [
      '@emotion/react',
      '@emotion/styled',
      '@mui/material',
      '@mui/material/styles',
      '@mui/system',
      '@mui/utils',
      // add any other @mui/* packages you import directly
    ],
  },
  build: {
    outDir: './assets/',
    assetsDir: 'django-vite/',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        factsheet: resolve('./factsheet/frontend/src/index.jsx'),
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: { host: 'localhost' },
  },
  watch: {
    // don’t poll at all, lean on inotify if possible
    usePolling: false,
    // ignore everything except your source folders
    ignored: [
      '**/node_modules/**',
      '**/.git/**',
      '**/.venv/**',
      '**/venv/**',
      '**/env/**',
      '**/.env*/**',
    ],
  }
})
