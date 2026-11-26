import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Send /api requests to the FastAPI backend during development,
    // so the app and the API share one origin (no CORS setup needed).
    proxy: {
      '/api': process.env.VITE_API_TARGET ?? 'http://localhost:8000',
    },
  },
})
