import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    globals: false,
    environment: "node",
    include: ["tests/**/*.test.ts"],
    testTimeout: 300000, // 5 minutes for infrastructure tests
    hookTimeout: 60000,  // 1 minute for setup/teardown
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      exclude: ["**/*.test.ts", "**/index.ts"]
    }
  }
})
