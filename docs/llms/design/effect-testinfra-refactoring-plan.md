# Effect-TestInfra Refactoring Plan

## Issues Identified and Solutions

### 1. Service Pattern
**Issue**: Using `Context.Tag` with static methods instead of `Effect.Service()()`

**Fix**:
```typescript
// Before
export class SSHConnection extends Context.Tag("SSHConnection")<...>() {
  static live = Layer.effect(...)
}

// After
export class SSHConnection extends Effect.Service<SSHConnection>()(
  "SSHConnection",
  {
    effect: Effect.gen(function* () { /* ... */ }),
    dependencies: []
  }
) {
  static Test = Layer.succeed(SSHConnection, { /* mock */ })
}
```

### 2. Schema Definition
**Issue**: Using `Schema.Class` with methods containing `this`

**Fix**:
```typescript
// Before
export class Port extends Schema.Class<Port>("Port")({
  value: Schema.Number
}) {
  toString(): string { return this.value.toString() }
}

// After
export const Port = Schema.Struct({
  value: Schema.Number.pipe(Schema.int(), Schema.between(1, 65535))
}).pipe(Schema.brand("Port"))
export interface Port extends Schema.Schema.Type<typeof Port> {}

export namespace Port {
  export const toString = (port: Port): string => port.value.toString()
  export const SSH: Port = { value: 22 }
}
```

### 3. File Organization
**Issue**: Multiple concepts in single file (Command.ts has Command, CommandResult, ExitCode, Stdout, Stderr)

**Fix**: Split into separate files:
- `domain/Command.ts` - Just Command
- `domain/CommandResult.ts` - CommandResult
- `domain/ExitCode.ts` - ExitCode
- `domain/Stdout.ts` - Stdout
- `domain/Stderr.ts` - Stderr

### 4. Context-Specific Functions
**Issue**: `isExecutable()` doesn't specify user context

**Fix**:
```typescript
// Before
isExecutable(): boolean {
  return (this.value & 0o111) !== 0
}

// After
export namespace FileMode {
  export const isExecutableByOwner = (mode: FileMode): boolean =>
    (mode.value & 0o100) !== 0
  
  export const isExecutableByGroup = (mode: FileMode): boolean =>
    (mode.value & 0o010) !== 0
  
  export const isExecutableByAnyone = (mode: FileMode): boolean =>
    (mode.value & 0o111) !== 0
}
```

### 5. No `this` Keyword
**Issue**: Methods using `this` throughout codebase

**Fix**: Convert to pure functions or namespace methods

### 6. Use Schema.Struct
**Issue**: Overusing Schema.Class

**Fix**: Use Schema.Struct with Schema.brand for most domain types

### 7. For Loops
**Issue**: Using `for` loops in test examples

**Fix**:
```typescript
// Before
for (const segment of topology.segments) {
  const result = yield* test(segment)
}

// After
yield* Effect.forEach(
  topology.segments,
  (segment) => testSegment(segment),
  { concurrency: "unbounded" }
)
```

## Refactoring Checklist

### Phase 1: Domain Models (Partially Complete)
- [x] Refactor Command domain models
  - [x] Already split into separate files
  - [x] Convert to Schema.Struct pattern  
  - [x] Remove `this` usage
  - [x] Add namespace functions
  - [x] Fix type exports (CommandSchema + Command type)
- [x] Refactor CommandResult, ExitCode, Stdout, Stderr
  - [x] Proper Schema.Type extraction
  - [x] Remove ReadonlyArray imports (use `readonly T[]`)
  - [x] Namespace functions for business logic
- [x] Fix File models
  - [x] Fix nonNegative typo
- [ ] Refactor Host domain models (8 errors remaining)
  - [ ] Convert to Schema.Struct
  - [ ] Remove methods with `this`
  - [ ] Fix Effect namespace import
- [ ] Refactor NetworkInterface models
  - [ ] Fix deprecated Schema.ParseError
  - [ ] Replace Schema.TaggedEnum (deprecated API)
- [ ] Refactor Service/Package models
  - [ ] Replace Schema.TaggedEnum (deprecated API)

**Status:** Core domain models (Command, CommandResult, etc.) refactored. Remaining: Host, NetworkInterface, Service use old Schema.Class pattern.

### Phase 2: Services ✅ COMPLETED
- [x] Refactor SSHConnection
  - [x] Use Effect.Service()() pattern
  - [x] Add Test layer
  - [x] Explicit dependencies
  - [x] Add service interface
  - [x] Fix domain type construction (no `new`)
- [x] Refactor CommandExecutor
  - [x] Use Effect.Service()() pattern
  - [x] Add Test layer
  - [x] Add service interface
  - [x] Use CommandResult.failed() namespace function
- [x] Update layers to use Service.Default instead of ServiceLive

**Note:** Some compilation errors remain due to incomplete Phase 1 (domain models still need refactoring)

### Phase 3: Layers
- [ ] Update layer composition to use proper patterns
- [ ] Ensure all use pipe for composition

### Phase 4: Tests
- [ ] Remove for loops from tests
- [ ] Use Effect.forEach
- [ ] Ensure proper Layer usage

### Phase 5: Documentation
- [x] Create Effect best practices guide
- [ ] Update examples in README
- [ ] Add code comments referencing patterns

## Priority Order

1. **Critical** - Service pattern (Phase 2)
2. **High** - Domain model refactoring (Phase 1)
3. **Medium** - Test refactoring (Phase 4)
4. **Low** - Documentation updates (Phase 5)

## Example: Refactored Command.ts

See `packages/effect-testinfra/src/domain/Command.ts` for the refactored version following all these patterns.
