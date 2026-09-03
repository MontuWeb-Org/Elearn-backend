/**
 * Jest runs against the TypeScript sources in native ESM mode (the package is
 * `"type": "module"`), so `NODE_OPTIONS=--experimental-vm-modules` is required —
 * see the `test` script in package.json.
 *
 * @type {import('jest').Config}
 */
export default {
  testEnvironment: 'node',
  rootDir: '.',
  roots: ['<rootDir>/tests'],
  extensionsToTreatAsEsm: ['.ts'],
  // NodeNext sources import siblings with a `.js` suffix; strip it so Jest
  // resolves the `.ts` file that actually exists on disk.
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  transform: {
    '^.+\\.ts$': ['ts-jest', { useESM: true, tsconfig: '<rootDir>/tests/tsconfig.json' }],
  },
  setupFiles: ['<rootDir>/tests/setup-env.ts'],
  // Call history is wiped between tests; suites re-stub behaviour in `beforeEach`.
  clearMocks: true,
  testMatch: ['<rootDir>/tests/**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts', '!src/server.ts'],
};
