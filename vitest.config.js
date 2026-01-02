import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['static/js/__tests__/**/*.test.js'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html'],
      include: ['static/js/**/*.js'],
      exclude: ['static/js/__tests__/**'],
      all: true
    },
    setupFiles: ['./static/js/__tests__/setup.js']
  }
});
