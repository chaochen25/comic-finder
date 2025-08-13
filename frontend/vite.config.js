import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // Vite default; keep visible so we remember it
    proxy: {
      '/api': 'http://127.0.0.1:8000', // forwards /api to FastAPI
    },
  },
})
