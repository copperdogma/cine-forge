import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const uiPort = Number(process.env.CINE_FORGE_UI_PORT ?? process.env.FRONTEND_PORT ?? 5174)
const apiTarget = process.env.CINE_FORGE_API_URL ?? process.env.BACKEND_URL ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: uiPort,
    strictPort: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          codemirror: [
            'codemirror',
            '@codemirror/view',
            '@codemirror/state',
            '@codemirror/language',
            '@codemirror/search',
            '@codemirror/commands',
            '@lezer/highlight',
          ],
        },
      },
    },
  },
})
