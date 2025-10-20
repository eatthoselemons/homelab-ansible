# effect-testinfra

A type-safe, composable infrastructure testing library built with Effect-TS.

## Features

- **No Primitive Obsession**: Rich domain types instead of strings/numbers
- **Composable via Layers**: Easy dependency injection and testing
- **Type-Safe**: Full TypeScript types with validation
- **Resource Management**: Automatic cleanup via Effect's Scope
- **Retry Logic**: Built-in retry support for flaky operations

## Quick Start

```typescript
import { Effect } from "effect"
import {
  HostConnection,
  HostAddress,
  Port,
  Username,
  SshKeyPath,
  Command,
  makeHostTestLayer
} from "effect-testinfra"

// Create connection (rich types, not primitives!)
const connection = new HostConnection({
  address: new HostAddress({ value: "192.168.1.100" }),
  port: Port.SSH,
  username: Username.vagrant,
  keyPath: new SshKeyPath({ value: "/path/to/key" })
})

// Create test program
const testProgram = Effect.gen(function* () {
  const executor = yield* CommandExecutor
  
  // Run command
  const result = yield* executor.run(
    Command.make("ip addr show")
  )
  
  // Type-safe assertions
  if (result.succeeded()) {
    console.log("Command output:", result.stdout.value)
  }
})

// Provide dependencies and run
const layer = makeHostTestLayer(connection)
Effect.provide(testProgram, layer).pipe(Effect.runPromise)
```

## Domain Types

### Host Connection
- `HostAddress` - Not a string!
- `Port` - Not a number!
- `Username` - Validated Unix username
- `SshKeyPath` - Path to SSH key

### Commands
- `Command` - Shell command with options
- `CommandResult` - Rich result with typed stdout/stderr
- `ExitCode` - Typed exit codes

### Network
- `InterfaceName` - Network interface name
- `IpAddress` - Validated IP address
- `MacAddress` - Validated MAC address

## Testing with Vitest

```typescript
import { describe, it, expect } from "@effect/vitest"

describe("Infrastructure Tests", () => {
  it.live("can connect to host", () =>
    Effect.gen(function* () {
      const executor = yield* CommandExecutor
      const result = yield* executor.run(Command.make("hostname"))
      
      expect(result.succeeded()).toBe(true)
    }),
    makeHostTestLayer(connection)
  )
})
```
