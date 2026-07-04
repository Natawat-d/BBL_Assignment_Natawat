import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During local dev, Vite proxies /api to the backend so the browser talks to a
// single origin (matching the nginx setup used in Docker).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
