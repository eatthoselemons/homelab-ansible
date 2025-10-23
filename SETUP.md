# Effect-TestInfra Setup Guide

This guide shows how to set up and use the Effect-based infrastructure testing framework.

## Prerequisites

- Node.js >= 20.0.0
- pnpm >= 9.0.0

## Installation

```bash
# Install pnpm if not already installed
npm install -g pnpm

# Install all dependencies
pnpm install

# Build both packages
pnpm build
```

## Project Structure

```
homelab-ansible/
├── packages/
│   ├── effect-testinfra/       # Generic infrastructure testing library
│   │   ├── src/
│   │   │   ├── domain/         # Rich domain types (no primitives!)
│   │   │   ├── services/       # SSH, command execution
│   │   │   ├── layers/         # Layer composition
│   │   │   └── errors/         # Typed errors
│   │   └── package.json
│   │
│   └── homelab-test-cli/       # Homelab-specific implementation
│       ├── src/
│       │   ├── domain/         # VLANs, VMs, TestSections
│       │   ├── services/       # VM provisioning
│       │   ├── layers/         # Layer composition
│       │   └── cli/            # CLI commands
│       ├── tests/              # Actual infrastructure tests
│       └── package.json
│
├── pnpm-workspace.yaml         # Monorepo configuration
└── package.json                # Root workspace
```

## Key Concepts

### 1. No Primitive Obsession

We use rich domain types instead of primitives:

```typescript
// ❌ BAD
function connect(host: string, port: number, user: string)

// ✅ GOOD
function connect(connection: HostConnection)
```

### 2. Layer-Based Dependency Injection

Services are provided via Effect layers:

```typescript
const testProgram = Effect.gen(function* () {
  const executor = yield* CommandExecutor
  const result = yield* executor.run(Command.make("hostname"))
})

// Provide dependencies
Effect.provide(testProgram, makeTestLayer("networking"))
```

### 3. Vitest for Test Execution

We use Vitest with `@effect/vitest` for Effect-native tests:

```typescript
import { describe, it, expect } from "@effect/vitest"

it.live("infrastructure test", () =>
  Effect.gen(function* () {
    // Test logic here
  }),
  testLayer // Provide dependencies
)
```

## Development Workflow

### Running Tests

```bash
# Run tests in effect-testinfra
cd packages/effect-testinfra
pnpm test

# Run tests in homelab-test-cli
cd packages/homelab-test-cli
pnpm test

# Watch mode
pnpm test:watch
```

### Type Checking

```bash
# Check all packages
pnpm typecheck

# Check specific package
cd packages/effect-testinfra
pnpm typecheck
```

### Building

```bash
# Build all packages
pnpm build

# Build specific package
cd packages/effect-testinfra
pnpm build
```

## Writing Your First Test

1. **Define domain types** (if needed):

```typescript
// packages/homelab-test-cli/src/domain/MyDomain.ts
export class MyType extends Schema.Class<MyType>("MyType")({
  value: Schema.String
}) {}
```

2. **Write test using Vitest**:

```typescript
// packages/homelab-test-cli/tests/my-test.test.ts
import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"

describe("My Infrastructure Test", () => {
  it.live("does something", () =>
    Effect.gen(function* () {
      const executor = yield* CommandExecutor
      const result = yield* executor.run(Command.make("echo test"))
      
      expect(result.succeeded()).toBe(true)
    }),
    makeTestLayer("my-section")
  )
})
```

3. **Run the test**:

```bash
cd packages/homelab-test-cli
pnpm test
```

## Next Steps

1. ✅ Implement libvirt provisioner
2. ✅ Add resource manager service
3. ✅ Create CLI commands using @effect/cli
4. ✅ Port existing shell tests to Vitest
5. ✅ Add HTML/JUnit reporting

## Benefits

- **Type Safety**: Compiler catches errors at build time
- **Composability**: Layers make testing easy
- **No Primitive Obsession**: Self-documenting code
- **Resource Management**: Automatic cleanup
- **Retry Logic**: Built-in retry support

## Troubleshooting

### Build Errors

```bash
# Clean and rebuild
pnpm clean
pnpm install
pnpm build
```

### Test Failures

```bash
# Run with verbose output
pnpm test -- --reporter=verbose

# Run specific test file
pnpm test tests/networking/vlan-connectivity.test.ts
```
