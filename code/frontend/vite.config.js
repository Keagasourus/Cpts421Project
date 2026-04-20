import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    // Tailwind's vite plugin causes ETIMEDOUT during vitest; skip it in test mode
    ...(mode === 'test' ? [] : [tailwindcss()]),
  ],
  server: {
    port: 3000
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './src/test/setup.js',
    css: false,
    pool: 'forks',
  }
}))
