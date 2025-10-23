# Effect-TS Best Practices Guide

This guide documents best practices for writing Effect-TS code, following principles from:
- **"Grokking Simplicity"** by Eric Normand (functional programming fundamentals)
- **"Domain Modeling Made Functional"** by Scott Wlaschin (domain-driven design)
- **Effect-TS patterns** (modern TypeScript effect systems)

## Core Principles

### 1. Domain-Driven Design (Scott Wlaschin)

#### Make Illegal States Unrepresentable

Use the type system to prevent invalid domain states:

```typescript
// ❌ BAD: Primitives allow invalid states
interface VmConfig {
  cpus: number        // Could be 0, negative, or 1000
  memory: number      // Could be any number
  status: string      // Could be typo: "runing"
}

// ✅ GOOD: Types enforce domain rules
export const CpuCount = Schema.Number.pipe(
  Schema.int(),
  Schema.between(1, 64),  // Physical constraint
  Schema.brand("CpuCount")
)
export type CpuCount = Schema.Schema.Type<typeof CpuCount>

export const VmStatus = Schema.Literal("running", "stopped", "error")
export type VmStatus = Schema.Schema.Type<typeof VmStatus>

interface VmConfig {
  cpus: CpuCount      // Guaranteed valid
  memory: MemoryMB    // Guaranteed valid
  status: VmStatus    // Typos impossible
}
```

#### Model the Domain Precisely

Domain types should exactly match business concepts:

```typescript
// ❌ BAD: Generic, imprecise
type NetworkConfig = {
  vlan: number
  subnet: string
}

// ✅ GOOD: Precise domain model
export const VlanId = Schema.Number.pipe(
  Schema.int(),
  Schema.between(1, 4094),  // IEEE 802.1Q valid range
  Schema.brand("VlanId")
)

export const SubnetCidr = Schema.String.pipe(
  Schema.pattern(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/),
  Schema.brand("SubnetCidr")
)

export const NetworkSegment = Schema.Struct({
  name: Schema.String,
  vlanId: VlanId,
  subnet: SubnetCidr,
  gateway: IpAddress,
})
```

#### Use Ubiquitous Language

Domain types should use terminology from the problem domain:

```typescript
// ❌ BAD: Technical/generic terms
interface Config {
  val: number
  data: string
}

// ✅ GOOD: Domain language
export const TestSection = Schema.Struct({
  name: TestSectionName,
  estimatedDuration: EstimatedDuration,
  vmSpecs: Schema.Array(VmSpec),
  requiresNestedVirt: Schema.Boolean
})
```

#### Keep Domain Logic in Domain Types

Business rules belong with the data:

```typescript
// Domain model
export const VmSpec = Schema.Struct({
  name: VmName,
  cpus: CpuCount,
  memory: MemoryMB,
  disks: Schema.Array(DiskSpec),
})
export interface VmSpec extends Schema.Schema.Type<typeof VmSpec> {}

// Domain logic with the domain type
export namespace VmSpec {
  // Business rule: High-memory VMs need special hosts
  export const requiresHighMemoryHost = (spec: VmSpec): boolean =>
    spec.memory > 16384
  
  // Business calculation
  export const totalDiskGB = (spec: VmSpec): number =>
    spec.disks.reduce((sum, disk) => sum + disk.size, 0)
  
  // Domain validation
  export const canRunOn = (spec: VmSpec, host: Host): boolean =>
    host.availableCpus >= spec.cpus &&
    host.availableMemory >= spec.memory
}
```

#### Railway-Oriented Programming

Use Effect's error handling for domain workflows:

```typescript
// Each step can succeed or fail
const provisionWorkflow = (spec: VmSpec) =>
  Effect.gen(function* () {
    // Validate
    yield* validateVmSpec(spec)  // Effect<void, ValidationError>
    
    // Allocate resources
    const allocation = yield* allocateResources(spec)  // Effect<Allocation, ResourceError>
    
    // Provision
    const vm = yield* provisionVm(spec, allocation)  // Effect<VM, ProvisionError>
    
    // Configure
    yield* configureVm(vm)  // Effect<void, ConfigError>
    
    return vm
  }).pipe(
    // Handle errors at appropriate level
    Effect.catchTag("ValidationError", (e) => /* handle */),
    Effect.catchTag("ResourceError", (e) => /* handle */),
  )
```

### 2. Separate Data, Calculations, and Actions (Eric Normand)

From "Grokking Simplicity":
- **Data**: Immutable values (Schema definitions)
- **Calculations**: Pure functions that transform data
- **Actions**: Effects that interact with the world

```typescript
// ❌ BAD: Mixing concerns
class Command {
  constructor(public value: string) {}
  execute() { /* action mixed with data */ }
}

// ✅ GOOD: Separated
// Data
export const Command = Schema.Struct({
  value: Schema.String.pipe(Schema.nonEmptyString()),
  timeout: Schema.optional(Schema.Number.pipe(Schema.positive())),
})
export interface Command extends Schema.Schema.Type<typeof Command> {}

// Calculation (pure function)
export const makeCommand = (value: string, timeout?: number): Command => ({
  value,
  timeout
})

// Action (Effect)
export const execute = (cmd: Command) =>
  Effect.gen(function* () {
    const ssh = yield* SSHConnection
    return yield* ssh.execute(cmd)
  })
```

### 2. Service Definition Pattern

Always use `Effect.Service()()` pattern with explicit dependencies:

```typescript
// ❌ BAD: Static methods, context.Tag
export class SSHConnection extends Context.Tag("SSHConnection")<...>() {
  static live = Layer.effect(...)
}

// ✅ GOOD: Service pattern with dependencies
export class SSHConnection extends Effect.Service<SSHConnection>()(
  "SSHConnection",
  {
    effect: Effect.gen(function* () {
      // Implementation
      return {
        execute: (cmd: Command) => // ...
      }
    }),
    dependencies: [] // Explicit dependencies
  }
) {
  static Test = Layer.succeed(SSHConnection, {
    execute: () => Effect.succeed(mockResult)
  })
}
```

### 3. Schema: Use Schema.Struct, Not Schema.Class

```typescript
// ❌ BAD: Schema.Class with methods using `this`
export class Port extends Schema.Class<Port>("Port")({
  value: Schema.Number
}) {
  toString(): string {
    return this.value.toString() // Using `this`!
  }
}

// ✅ GOOD: Schema.Struct + pure functions
export const Port = Schema.Struct({
  value: Schema.Number.pipe(Schema.int(), Schema.between(1, 65535))
})
export interface Port extends Schema.Schema.Type<typeof Port> {}

// Pure function instead of method
export const portToString = (port: Port): string => 
  port.value.toString()

// Or namespace for organization
export namespace Port {
  export const toString = (port: Port): string => 
    port.value.toString()
  
  export const SSH = { value: 22 } as Port
}
```

### 4. Never Use `this` - Use Functional Style

```typescript
// ❌ BAD: Using `this`
class CommandResult {
  succeeded(): boolean {
    return this.exitCode.value === 0
  }
}

// ✅ GOOD: Pure function
export const isSuccess = (result: CommandResult): boolean =>
  result.exitCode.value === 0

// Or namespace pattern
export namespace CommandResult {
  export const isSuccess = (result: CommandResult): boolean =>
    result.exitCode.value === 0
  
  export const isFailed = (result: CommandResult): boolean =>
    !isSuccess(result)
}
```

### 5. One Concept Per File

```typescript
// ❌ BAD: Multiple concepts in one file
// Command.ts
export class Command { }
export class CommandResult { }
export class ExitCode { }
export class Stdout { }
export class Stderr { }

// ✅ GOOD: One concept per file
// Command.ts
export const Command = Schema.Struct({ ... })

// CommandResult.ts
export const CommandResult = Schema.Struct({ ... })

// ExitCode.ts
export const ExitCode = Schema.Struct({ ... })

// Stdout.ts
export const Stdout = Schema.Struct({ ... })

// Stderr.ts
export const Stderr = Schema.Struct({ ... })
```

### 6. No For Loops - Use Functional Iteration

```typescript
// ❌ BAD: Imperative for loop
for (const segment of topology.segments) {
  const result = await test(segment)
  results.push(result)
}

// ✅ GOOD: Effect.forEach
yield* Effect.forEach(
  topology.segments,
  (segment) => testSegment(segment),
  { concurrency: "unbounded" }
)

// ✅ GOOD: Array methods for calculations
const totalCpus = vmSpecs.map(spec => spec.cpus.value)
  .reduce((sum, cpu) => sum + cpu, 0)

// ✅ GOOD: ReadonlyArray.map for immutability
import { ReadonlyArray } from "effect"

const mapped = ReadonlyArray.map(
  segments,
  (segment) => segment.name
)
```

### 7. Avoid Primitive Obsession

```typescript
// ❌ BAD: Primitives everywhere
function provision(name: string, cpus: number, memory: number)

// ✅ GOOD: Rich domain types
export const VmName = Schema.String.pipe(
  Schema.pattern(/^[a-z0-9-]+$/),
  Schema.brand("VmName")
)
export type VmName = Schema.Schema.Type<typeof VmName>

export const CpuCount = Schema.Number.pipe(
  Schema.int(),
  Schema.between(1, 64),
  Schema.brand("CpuCount")
)
export type CpuCount = Schema.Schema.Type<typeof CpuCount>

function provision(spec: VmSpec)
```

### 8. Context-Aware Domain Models

```typescript
// ❌ BAD: Ambiguous
export const isExecutable = (mode: FileMode): boolean =>
  (mode.value & 0o111) !== 0

// ✅ GOOD: Explicit context
export namespace FileMode {
  export const isExecutableByOwner = (mode: FileMode): boolean =>
    (mode.value & 0o100) !== 0
  
  export const isExecutableByGroup = (mode: FileMode): boolean =>
    (mode.value & 0o010) !== 0
  
  export const isExecutableByOther = (mode: FileMode): boolean =>
    (mode.value & 0o001) !== 0
  
  export const isExecutableByAnyone = (mode: FileMode): boolean =>
    (mode.value & 0o111) !== 0
}
```

### 9. Layer Composition Patterns

```typescript
// Use pipe for clean composition
export const AppLayer = Layer.merge(
  ConfigLayer,
  LoggerLayer
).pipe(
  Layer.provide(DatabaseLayer),
  Layer.provide(ResourceLayer)
)

// Factory functions for parameterized layers
export const makeSSHLayer = (connection: HostConnection) =>
  Layer.effect(
    SSHConnection,
    Effect.gen(function* () {
      // Implementation
    })
  )
```

### 10. Effect.gen Instead of Async/Await

```typescript
// ❌ BAD: Mixing async/await with Effect
async function test() {
  const result = await Effect.runPromise(something)
  return result
}

// ✅ GOOD: Pure Effect
const test = Effect.gen(function* () {
  const result = yield* something
  return result
})
```

### 11. Branded Types for Type Safety

```typescript
// Use Schema.brand for nominal typing
export const VlanId = Schema.Number.pipe(
  Schema.int(),
  Schema.between(1, 4094),
  Schema.brand("VlanId")
)
export type VlanId = Schema.Schema.Type<typeof VlanId>

// Now VlanId and Port cannot be confused
const vlan: VlanId = 10 // Type error!
const vlan = Schema.decode(VlanId)(10) // Correct
```

### 12. Test Layer Pattern

```typescript
export class MyService extends Effect.Service<MyService>()(
  "MyService",
  {
    effect: Effect.gen(function* () {
      const dep = yield* Dependency
      return {
        doThing: (input: string) => 
          Effect.succeed(`Result: ${input}`)
      }
    }),
    dependencies: [DependencyLayer]
  }
) {
  // Provide test implementation
  static Test = Layer.succeed(MyService, {
    doThing: (input: string) => 
      Effect.succeed(`Mock: ${input}`)
  })
}

// In tests
describe("MyService", () => {
  it.live("does thing", () =>
    Effect.gen(function* () {
      const service = yield* MyService
      const result = yield* service.doThing("test")
      expect(result).toBe("Mock: test")
    }),
    MyService.Test // Use test layer
  )
})
```

### 13. Error Handling with Tagged Errors

```typescript
// Define typed errors
export class CommandError extends Data.TaggedError("CommandError")<{
  readonly command: Command
  readonly message: string
  readonly cause?: unknown
}> {}

// Handle specific errors
const program = Effect.gen(function* () {
  const result = yield* runCommand(cmd)
  return result
}).pipe(
  Effect.catchTag("CommandError", (error) =>
    Effect.succeed(defaultResult)
  )
)
```

### 14. Opaque Types for Validation

```typescript
// Schema validates and creates opaque type
export const Email = Schema.String.pipe(
  Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/),
  Schema.brand("Email")
)
export type Email = Schema.Schema.Type<typeof Email>

// Can only create via validation
const email = yield* Schema.decode(Email)("user@example.com")
// Type is Email, not string!
```

## Common Patterns

### Repository Pattern

```typescript
export class UsersRepo extends Effect.Service<UsersRepo>()(
  "UsersRepo",
  {
    effect: Effect.gen(function* () {
      const sql = yield* Sql
      
      return {
        findById: (id: string) =>
          sql.query(/* ... */).pipe(
            Effect.map(rows => rows[0])
          ),
        
        create: (user: User) =>
          sql.query(/* ... */)
      }
    }),
    dependencies: [SqlLayer]
  }
) {
  static Test = Layer.succeed(UsersRepo, {
    findById: (id: string) => Effect.succeed(mockUser),
    create: (user: User) => Effect.succeed(user)
  })
}
```

### Configuration Pattern

```typescript
export const AppConfig = Schema.Struct({
  port: Port,
  database: Schema.Struct({
    host: HostAddress,
    port: Port,
    name: DatabaseName
  })
})
export interface AppConfig extends Schema.Schema.Type<typeof AppConfig> {}

export class Config extends Effect.Service<Config>()(
  "Config",
  {
    effect: Effect.gen(function* () {
      const raw = yield* loadConfigFile("config.yaml")
      const config = yield* Schema.decode(AppConfig)(raw)
      return config
    }),
    dependencies: []
  }
) {}
```

### Resource Management Pattern

```typescript
// Use Layer.scoped for resources
export const DatabaseLayer = Layer.scoped(
  Database,
  Effect.gen(function* () {
    const connection = yield* Effect.acquireRelease(
      acquireConnection(),
      (conn) => closeConnection(conn)
    )
    
    return {
      query: (sql: string) => runQuery(connection, sql)
    }
  })
)
```

## Testing Patterns

### Unit Tests

```typescript
import { describe, it, expect } from "@effect/vitest"

describe("Pure Calculations", () => {
  it.effect("transforms data", () =>
    Effect.gen(function* () {
      const result = transform(input)
      expect(result).toEqual(expected)
    })
  )
})
```

### Integration Tests with Layers

```typescript
describe("Service Integration", () => {
  it.live("calls database", () =>
    Effect.gen(function* () {
      const repo = yield* UsersRepo
      const user = yield* repo.findById("123")
      expect(user.name).toBe("Test User")
    }),
    Layer.merge(UsersRepo.Test, Database.Test)
  )
})
```

### Scoped Tests with Cleanup

```typescript
it.scoped("provisions and cleans up VM", () =>
  Effect.gen(function* () {
    const provisioner = yield* VmProvisioner
    
    const vm = yield* Effect.acquireRelease(
      provisioner.provision(spec),
      (vm) => provisioner.destroy(vm)
    )
    
    expect(vm.status).toBe("running")
    
    // VM automatically destroyed after test
  }),
  testLayer
)
```

## File Organization

```
src/
├── domain/               # Data structures
│   ├── Command.ts       # One type per file
│   ├── ExitCode.ts
│   └── index.ts         # Re-exports
├── services/            # Business logic
│   ├── SSHConnection.ts
│   └── index.ts
├── layers/              # DI composition
│   ├── AppLayer.ts
│   └── index.ts
├── errors/              # Typed errors
│   ├── CommandError.ts
│   └── index.ts
└── utils/               # Pure helper functions
    ├── parsing.ts
    └── index.ts
```

## Checklist for Code Review

- [ ] No `this` keyword anywhere
- [ ] No `for`/`while` loops - use functional iteration
- [ ] Schema.Struct, not Schema.Class (unless absolutely needed)
- [ ] One concept per file
- [ ] Services use `Effect.Service()()` pattern
- [ ] Pure functions separated from Effects
- [ ] Test layers provided via `static Test`
- [ ] Branded types for domain concepts
- [ ] No primitive obsession
- [ ] Explicit user context where needed (file permissions, etc.)
- [ ] Effect.gen instead of async/await
- [ ] Layer composition uses pipe
- [ ] Tagged errors for error handling
- [ ] Resources use Layer.scoped + Effect.acquireRelease

## Domain-Driven Design Workflow

Following Scott Wlaschin's approach:

### 1. Understand the Domain
- Talk to domain experts
- Learn ubiquitous language
- Identify bounded contexts

### 2. Model the Domain
```typescript
// Start with types that match domain language
export const NetworkSegment = Schema.Struct({
  name: Schema.String,           // "Management", "DMZ"
  vlanId: VlanId,                // 10, 20, 30...
  subnet: SubnetCidr,            // "10.10.0.0/16"
  gateway: IpAddress,            // "10.10.0.1"
  accessRules: Schema.Array(Schema.String)
})
```

### 3. Make Rules Explicit
```typescript
// Business rule: DMZ cannot access internal networks
export namespace NetworkTopology {
  export const canAccess = (
    from: NetworkSegment,
    to: NetworkSegment,
    topology: NetworkTopology
  ): boolean => {
    // Rules are explicit in code
    if (from.name === "DMZ") return false
    
    const allowed = topology.accessRules[from.name] || []
    return allowed.includes(to.name)
  }
}
```

### 4. Validate at Boundaries
```typescript
// Parse untyped data at system boundaries
export const parseTestConfig = (rawYaml: unknown) =>
  Schema.decodeUnknown(TestConfig)(rawYaml)
  // Result: Effect<TestConfig, ParseError>

// Inside the system, types are guaranteed valid
const runTests = (config: TestConfig) => {
  // config is already validated, no defensive checks needed
  return Effect.forEach(config.sections, runSection)
}
```

## Summary

**Key Takeaways:**

**From Scott Wlaschin (DDD):**
1. Make illegal states unrepresentable
2. Model domain precisely with types
3. Use ubiquitous language
4. Keep domain logic with domain types
5. Railway-oriented error handling

**From Eric Normand (Functional):**
1. Separate data (Schema), calculations (pure functions), actions (Effects)
2. Avoid primitive obsession
3. Keep calculations pure
4. Push effects to boundaries

**From Effect-TS Patterns:**
1. Use Schema.Struct + namespaces, not Schema.Class with methods
2. Never use `this` - functional style only
3. One concept per file
4. Effect.Service()() pattern for all services
5. Functional iteration (map/filter/fold), never for loops
6. Explicit context (e.g., file permissions by user type)
7. Branded types for domain safety
8. Layer composition for dependency injection

Follow these patterns and your Effect-TS code will be maintainable, testable, and type-safe.
