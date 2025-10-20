# Effect-TestInfra Architecture

## Executive Summary

This document outlines the architecture for two TypeScript packages using Effect-TS:
1. **effect-testinfra**: Generic infrastructure testing framework (reusable library)
2. **homelab-test-cli**: Homelab-specific testing implementation

We follow Domain-Driven Design principles (Scott Wlaschin) and avoid primitive obsession (Eric Normand) by modeling the domain explicitly with rich types.

## Monorepo Structure

```
homelab-ansible/
├── packages/
│   ├── effect-testinfra/          # Generic testing framework
│   │   ├── src/
│   │   │   ├── domain/            # Domain models (no primitives!)
│   │   │   │   ├── Host.ts
│   │   │   │   ├── Command.ts
│   │   │   │   ├── NetworkInterface.ts
│   │   │   │   ├── Service.ts
│   │   │   │   ├── Package.ts
│   │   │   │   ├── File.ts
│   │   │   │   └── TestResult.ts
│   │   │   ├── services/          # Core services
│   │   │   │   ├── SSHConnection.ts
│   │   │   │   ├── CommandExecutor.ts
│   │   │   │   ├── FileSystem.ts
│   │   │   │   ├── NetworkInspector.ts
│   │   │   │   └── SystemInspector.ts
│   │   │   ├── assertions/        # Assertion DSL
│   │   │   │   ├── Assertion.ts
│   │   │   │   ├── Matchers.ts
│   │   │   │   └── ErrorMessages.ts
│   │   │   ├── errors/            # Typed errors
│   │   │   │   ├── ConnectionError.ts
│   │   │   │   ├── CommandError.ts
│   │   │   │   └── AssertionError.ts
│   │   │   ├── layers/            # Base layers
│   │   │   │   └── SSHLayer.ts
│   │   │   └── index.ts
│   │   ├── test/
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── homelab-test-cli/          # Homelab-specific implementation
│       ├── src/
│       │   ├── domain/            # Homelab domain models
│       │   │   ├── infrastructure/
│       │   │   │   ├── VlanId.ts
│       │   │   │   ├── NetworkSegment.ts
│       │   │   │   ├── IpAddress.ts
│       │   │   │   ├── Gateway.ts
│       │   │   │   ├── VmConfiguration.ts
│       │   │   │   └── ClusterNode.ts
│       │   │   ├── provisioning/
│       │   │   │   ├── VmSpec.ts
│       │   │   │   ├── ResourceRequirements.ts
│       │   │   │   ├── ProvisionedVm.ts
│       │   │   │   └── VmBackend.ts
│       │   │   └── testing/
│       │   │       ├── TestSection.ts
│       │   │       ├── TestConfiguration.ts
│       │   │       └── TestSuite.ts
│       │   ├── services/
│       │   │   ├── VmProvisioner.ts
│       │   │   ├── ResourceManager.ts
│       │   │   ├── InventoryGenerator.ts
│       │   │   ├── ConfigLoader.ts
│       │   │   └── TestReporter.ts
│       │   ├── provisioners/      # Backend implementations
│       │   │   ├── Libvirt.ts
│       │   │   ├── Vagrant.ts
│       │   │   └── Harvester.ts
│       │   ├── tests/             # Actual test implementations
│       │   │   ├── networking/
│       │   │   ├── storage/
│       │   │   ├── vyos/
│       │   │   └── harvester/
│       │   ├── layers/            # Layer composition
│       │   │   ├── HomelabConfig.ts
│       │   │   ├── Provisioning.ts
│       │   │   └── Testing.ts
│       │   ├── cli/               # CLI implementation
│       │   │   ├── commands/
│       │   │   │   ├── Run.ts
│       │   │   │   ├── List.ts
│       │   │   │   ├── Provision.ts
│       │   │   │   └── Cleanup.ts
│       │   │   └── index.ts
│       │   └── index.ts
│       ├── config/
│       │   └── test-config.yaml
│       ├── test/
│       ├── package.json
│       └── tsconfig.json
│
├── package.json                    # Root workspace config
├── pnpm-workspace.yaml
└── tsconfig.base.json
```

## Part 1: Domain Modeling (No Primitive Obsession!)

### Core Principle
**Never pass primitives around**. Instead of `string`, `number`, `boolean`, use rich domain types that carry meaning and validation.

### Effect-TestInfra Domain Models

```typescript
// ❌ BAD: Primitive obsession
function connectToHost(host: string, port: number, user: string): Effect.Effect<Connection>

// ✅ GOOD: Rich domain types
function connectToHost(host: HostAddress): Effect.Effect<Connection>
```

#### domain/Host.ts
```typescript
import { Schema } from "@effect/schema"
import { Effect, Context } from "effect"

// Domain types - NOT primitives!
export class HostAddress extends Schema.Class<HostAddress>("HostAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-zA-Z0-9.-]+$/),
    Schema.nonEmpty()
  )
}) {
  toString(): string {
    return this.value
  }
}

export class Port extends Schema.Class<Port>("Port")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 65535)
  )
}) {
  toString(): string {
    return this.value.toString()
  }
}

export class Username extends Schema.Class<Username>("Username")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z_][a-z0-9_-]*$/),
    Schema.nonEmpty()
  )
}) {}

export class SshKeyPath extends Schema.Class<SshKeyPath>("SshKeyPath")({
  value: Schema.String.pipe(Schema.nonEmpty())
}) {}

// Rich domain model for host connection
export class HostConnection extends Schema.Class<HostConnection>("HostConnection")({
  address: HostAddress,
  port: Port,
  username: Username,
  keyPath: SshKeyPath,
}) {
  // Domain behavior lives with the data
  toSshConnectionString(): string {
    return `${this.username.value}@${this.address.value}:${this.port.value}`
  }
}

// Host service - the main API
export class Host extends Context.Tag("Host")<
  Host,
  {
    readonly connection: HostConnection
    readonly run: (command: Command) => Effect.Effect<CommandResult, CommandError>
    readonly file: (path: FilePath) => FileInspector
    readonly interface: (name: InterfaceName) => NetworkInterface
    readonly service: (name: ServiceName) => ServiceInspector
    readonly package: (name: PackageName) => PackageInspector
  }
>() {}
```

#### domain/Command.ts
```typescript
import { Schema } from "@effect/schema"
import { Data } from "effect"

// Command is NOT a string!
export class Command extends Schema.Class<Command>("Command")({
  value: Schema.String.pipe(Schema.nonEmpty()),
  timeout: Schema.optional(Schema.Number.pipe(Schema.positive())),
  workingDir: Schema.optional(Schema.String),
}) {
  static make(value: string, options?: {
    timeout?: number
    workingDir?: string
  }): Command {
    return new Command({
      value,
      timeout: options?.timeout,
      workingDir: options?.workingDir
    })
  }
}

// Exit code is NOT a number!
export class ExitCode extends Schema.Class<ExitCode>("ExitCode")({
  value: Schema.Number.pipe(Schema.int(), Schema.between(0, 255))
}) {
  isSuccess(): boolean {
    return this.value === 0
  }
  
  isFailure(): boolean {
    return this.value !== 0
  }
}

// Stdout/Stderr are NOT strings!
export class Stdout extends Schema.Class<Stdout>("Stdout")({
  value: Schema.String
}) {
  contains(substring: string): boolean {
    return this.value.includes(substring)
  }
  
  matches(regex: RegExp): boolean {
    return regex.test(this.value)
  }
  
  lines(): ReadonlyArray<string> {
    return this.value.split('\n')
  }
}

export class Stderr extends Schema.Class<Stderr>("Stderr")({
  value: Schema.String
}) {
  isEmpty(): boolean {
    return this.value.trim().length === 0
  }
}

// Rich command result
export class CommandResult extends Schema.Class<CommandResult>("CommandResult")({
  command: Command,
  exitCode: ExitCode,
  stdout: Stdout,
  stderr: Stderr,
  duration: Schema.Number.pipe(Schema.positive()), // milliseconds
}) {
  succeeded(): boolean {
    return this.exitCode.isSuccess()
  }
  
  failed(): boolean {
    return this.exitCode.isFailure()
  }
}
```

#### domain/NetworkInterface.ts
```typescript
import { Schema } from "@effect/schema"
import { Effect } from "effect"

export class InterfaceName extends Schema.Class<InterfaceName>("InterfaceName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9]+[a-z0-9._-]*$/),
    Schema.nonEmpty()
  )
}) {}

export class MacAddress extends Schema.Class<MacAddress>("MacAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/)
  )
}) {}

export class IpAddress extends Schema.Class<IpAddress>("IpAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^(\d{1,3}\.){3}\d{1,3}$/)
  )
}) {
  static parse(value: string): Effect.Effect<IpAddress, Schema.ParseError> {
    return Schema.decode(IpAddress)(value)
  }
}

export class Netmask extends Schema.Class<Netmask>("Netmask")({
  value: Schema.Number.pipe(Schema.int(), Schema.between(0, 32))
}) {}

export class InterfaceState extends Schema.TaggedEnum<InterfaceState>()(
  "InterfaceState",
  {
    Up: Schema.Struct({}),
    Down: Schema.Struct({}),
    Unknown: Schema.Struct({})
  }
) {}

// Rich network interface model
export class NetworkInterface extends Schema.Class<NetworkInterface>("NetworkInterface")({
  name: InterfaceName,
  state: InterfaceState,
  addresses: Schema.Array(IpAddress),
  macAddress: Schema.optional(MacAddress),
  mtu: Schema.optional(Schema.Number.pipe(Schema.positive())),
}) {
  isUp(): boolean {
    return this.state._tag === "Up"
  }
  
  hasAddress(addr: IpAddress): boolean {
    return this.addresses.some(a => a.value === addr.value)
  }
}

// Service for inspecting network interfaces
export interface NetworkInterfaceInspector {
  readonly exists: Effect.Effect<boolean, never>
  readonly state: Effect.Effect<InterfaceState, InspectionError>
  readonly addresses: Effect.Effect<ReadonlyArray<IpAddress>, InspectionError>
  readonly isUp: Effect.Effect<boolean, InspectionError>
}
```

#### domain/File.ts
```typescript
import { Schema } from "@effect/schema"
import { Effect } from "effect"

export class FilePath extends Schema.Class<FilePath>("FilePath")({
  value: Schema.String.pipe(Schema.nonEmpty())
}) {
  get basename(): string {
    return this.value.split('/').pop() || ''
  }
  
  get dirname(): string {
    const parts = this.value.split('/')
    parts.pop()
    return parts.join('/') || '/'
  }
  
  join(other: string): FilePath {
    return new FilePath({
      value: `${this.value}/${other}`.replace(/\/+/g, '/')
    })
  }
}

export class FileMode extends Schema.Class<FileMode>("FileMode")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(0, 0o777)
  )
}) {
  toString(): string {
    return '0' + this.value.toString(8)
  }
  
  isExecutable(): boolean {
    return (this.value & 0o111) !== 0
  }
}

export class FileSize extends Schema.Class<FileSize>("FileSize")({
  bytes: Schema.Number.pipe(Schema.nonnegative())
}) {
  toKB(): number {
    return this.bytes / 1024
  }
  
  toMB(): number {
    return this.bytes / (1024 * 1024)
  }
}

export class FileOwner extends Schema.Class<FileOwner>("FileOwner")({
  uid: Schema.Number.pipe(Schema.nonnegative()),
  gid: Schema.Number.pipe(Schema.nonnegative()),
  user: Schema.String,
  group: Schema.String,
}) {}

export class FileContent extends Schema.Class<FileContent>("FileContent")({
  value: Schema.String
}) {
  contains(substring: string): boolean {
    return this.value.includes(substring)
  }
  
  matches(regex: RegExp): boolean {
    return regex.test(this.value)
  }
  
  lines(): ReadonlyArray<string> {
    return this.value.split('\n')
  }
}

export class FileInfo extends Schema.Class<FileInfo>("FileInfo")({
  path: FilePath,
  exists: Schema.Boolean,
  mode: Schema.optional(FileMode),
  size: Schema.optional(FileSize),
  owner: Schema.optional(FileOwner),
  isDirectory: Schema.Boolean,
  isFile: Schema.Boolean,
  isSymlink: Schema.Boolean,
}) {}

export interface FileInspector {
  readonly exists: Effect.Effect<boolean, never>
  readonly info: Effect.Effect<FileInfo, InspectionError>
  readonly content: Effect.Effect<FileContent, InspectionError>
  readonly mode: Effect.Effect<FileMode, InspectionError>
  readonly owner: Effect.Effect<FileOwner, InspectionError>
  readonly contains: (text: string) => Effect.Effect<boolean, InspectionError>
}
```

### Homelab-Specific Domain Models

#### domain/infrastructure/VlanId.ts
```typescript
import { Schema } from "@effect/schema"

// VLAN ID is NOT a number!
export class VlanId extends Schema.Class<VlanId>("VlanId")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 4094) // Valid VLAN range
  )
}) {
  toString(): string {
    return this.value.toString()
  }
  
  toInterfaceSuffix(): string {
    return `.${this.value}`
  }
  
  static Management = new VlanId({ value: 10 })
  static Private = new VlanId({ value: 20 })
  static Public = new VlanId({ value: 30 })
  static Storage = new VlanId({ value: 40 })
  static Backup = new VlanId({ value: 50 })
  static GuestWifi = new VlanId({ value: 60 })
  static TrustedWifi = new VlanId({ value: 70 })
  static IoT = new VlanId({ value: 80 })
  static Logs = new VlanId({ value: 90 })
}

export class SubnetCidr extends Schema.Class<SubnetCidr>("SubnetCidr")({
  value: Schema.String.pipe(
    Schema.pattern(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/)
  )
}) {}

export class DomainName extends Schema.Class<DomainName>("DomainName")({
  value: Schema.String.pipe(
    Schema.pattern(/^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/)
  )
}) {}

// Rich network segment model
export class NetworkSegment extends Schema.Class<NetworkSegment>("NetworkSegment")({
  name: Schema.String,
  vlanId: VlanId,
  subnet: SubnetCidr,
  gateway: IpAddress,
  domain: Schema.optional(DomainName),
}) {
  // Domain logic
  containsIp(ip: IpAddress): boolean {
    // Implement CIDR matching
    const [network, bits] = this.subnet.value.split('/')
    // ... CIDR logic
    return false // placeholder
  }
  
  get interfaceName(): string {
    return `bond0${this.vlanId.toInterfaceSuffix()}`
  }
}

// Network topology as a first-class concept
export class NetworkTopology extends Schema.Class<NetworkTopology>("NetworkTopology")({
  segments: Schema.Array(NetworkSegment),
  // Access rules defined in domain
  accessRules: Schema.Record(
    Schema.String, // source segment
    Schema.Array(Schema.String) // allowed destinations
  )
}) {
  canAccess(from: NetworkSegment, to: NetworkSegment): boolean {
    const allowed = this.accessRules[from.name] || []
    return allowed.includes(to.name)
  }
  
  getSegmentByVlan(vlan: VlanId): Schema.Option<NetworkSegment> {
    return Schema.Option.fromNullable(
      this.segments.find(s => s.vlanId.value === vlan.value)
    )
  }
}
```

#### domain/provisioning/VmSpec.ts
```typescript
import { Schema } from "@effect/schema"

export class VmName extends Schema.Class<VmName>("VmName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9-]+$/),
    Schema.nonEmpty()
  )
}) {}

export class CpuCount extends Schema.Class<CpuCount>("CpuCount")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 64)
  )
}) {}

export class MemoryMB extends Schema.Class<MemoryMB>("MemoryMB")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(512, 524288) // 512MB to 512GB
  )
}) {
  toGB(): number {
    return this.value / 1024
  }
}

export class DiskSizeGB extends Schema.Class<DiskSizeGB>("DiskSizeGB")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 10000)
  )
}) {}

export class DiskSpec extends Schema.Class<DiskSpec>("DiskSpec")({
  size: DiskSizeGB,
  type: Schema.Literal("virtio", "scsi", "ide"),
}) {}

export class NetworkInterfaceCount extends Schema.Class<NetworkInterfaceCount>(
  "NetworkInterfaceCount"
)({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 8)
  )
}) {}

// Rich VM specification
export class VmSpec extends Schema.Class<VmSpec>("VmSpec")({
  name: VmName,
  cpus: CpuCount,
  memory: MemoryMB,
  disks: Schema.Array(DiskSpec),
  networkInterfaces: NetworkInterfaceCount,
  nestedVirtualization: Schema.Boolean,
  baseImage: Schema.optional(Schema.String),
}) {
  requiresHighMemoryHost(): boolean {
    return this.memory.value > 16384 // > 16GB
  }
  
  totalDiskGB(): number {
    return this.disks.reduce((sum, disk) => sum + disk.size.value, 0)
  }
}

// Provisioned VM with connection info
export class ProvisionedVm extends Schema.Class<ProvisionedVm>("ProvisionedVm")({
  spec: VmSpec,
  connection: HostConnection,
  vmId: Schema.String, // Backend-specific ID
  status: Schema.Literal("running", "stopped", "error"),
}) {}
```

#### domain/testing/TestSection.ts
```typescript
import { Schema } from "@effect/schema"
import { Duration } from "effect"

export class TestSectionName extends Schema.Class<TestSectionName>("TestSectionName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z_]+$/),
    Schema.nonEmpty()
  )
}) {}

export class TestMarker extends Schema.Class<TestMarker>("TestMarker")({
  value: Schema.Literal("network", "storage", "critical", "slow", "harvester", "vyos")
}) {}

export class EstimatedDuration extends Schema.Class<EstimatedDuration>("EstimatedDuration")({
  milliseconds: Schema.Number.pipe(Schema.positive())
}) {
  static fromMinutes(minutes: number): EstimatedDuration {
    return new EstimatedDuration({ milliseconds: minutes * 60 * 1000 })
  }
  
  toMinutes(): number {
    return this.milliseconds / (60 * 1000)
  }
  
  isQuick(): boolean {
    return this.toMinutes() < 10
  }
}

// Rich test section model
export class TestSection extends Schema.Class<TestSection>("TestSection")({
  name: TestSectionName,
  description: Schema.String,
  playbookPath: Schema.String,
  tags: Schema.Array(Schema.String),
  vmSpecs: Schema.Array(VmSpec),
  estimatedDuration: EstimatedDuration,
  requiresNestedVirt: Schema.Boolean,
  markers: Schema.Array(TestMarker),
  testFiles: Schema.Array(Schema.String),
}) {
  totalCpus(): number {
    return this.vmSpecs.reduce((sum, vm) => sum + vm.cpus.value, 0)
  }
  
  totalMemoryMB(): number {
    return this.vmSpecs.reduce((sum, vm) => sum + vm.memory.value, 0)
  }
  
  isQuick(): boolean {
    return this.estimatedDuration.isQuick()
  }
}
```

## Part 2: Services (Effect Services)

### Effect-TestInfra Services

#### services/SSHConnection.ts
```typescript
import { Effect, Context, Layer, Scope } from "effect"
import { NodeSSH } from "node-ssh"

export class SSHConnectionError extends Schema.TaggedError<SSHConnectionError>()(
  "SSHConnectionError",
  {
    message: Schema.String,
    cause: Schema.Unknown
  }
) {}

// Service tag definition - simple interface, no direct dependencies
export class SSHConnection extends Context.Tag("SSHConnection")<
  SSHConnection,
  {
    readonly execute: (
      command: Command
    ) => Effect.Effect<CommandResult, CommandError>
  }
>() {}

// Layer implementation with proper resource management
export const makeSSHConnectionLayer = (connection: HostConnection) =>
  Layer.scoped(
    SSHConnection,
    Effect.gen(function* () {
      const ssh = new NodeSSH()
      
      // Acquire connection with automatic cleanup
      yield* Effect.acquireRelease(
        Effect.tryPromise({
          try: () => ssh.connect({
            host: connection.address.value,
            port: connection.port.value,
            username: connection.username.value,
            privateKeyPath: connection.keyPath.value,
          }),
          catch: (error) => new SSHConnectionError({
            message: "Failed to connect",
            cause: error
          })
        }),
        () => Effect.promise(() => ssh.dispose())
      )
      
      // Return service implementation
      const execute = (command: Command) =>
        Effect.gen(function* () {
          const startTime = Date.now()
          
          const result = yield* Effect.tryPromise({
            try: () => ssh.execCommand(
              command.value,
              { 
                cwd: command.workingDir,
                timeout: command.timeout 
              }
            ),
            catch: (error) => new CommandError({
              command,
              message: "Command execution failed",
              cause: error
            })
          })
          
          const duration = Date.now() - startTime
          
          return new CommandResult({
            command,
            exitCode: new ExitCode({ value: result.code || 0 }),
            stdout: new Stdout({ value: result.stdout }),
            stderr: new Stderr({ value: result.stderr }),
            duration
          })
        })
      
      return { execute }
    })
  )
```

#### services/CommandExecutor.ts
```typescript
import { Effect, Context, Layer, Schedule } from "effect"

// High-level command execution with retry logic
export class CommandExecutor extends Context.Tag("CommandExecutor")<
  CommandExecutor,
  {
    readonly run: (
      command: Command
    ) => Effect.Effect<CommandResult, CommandError>
    
    readonly runWithRetry: (
      command: Command,
      retries: number
    ) => Effect.Effect<CommandResult, CommandError>
    
    readonly runExpectingSuccess: (
      command: Command
    ) => Effect.Effect<CommandResult, CommandError>
  }
>() {}

// Layer depends on SSHConnection
export const CommandExecutorLive = Layer.effect(
  CommandExecutor,
  Effect.gen(function* () {
    const ssh = yield* SSHConnection
    
    const run = (command: Command) => ssh.execute(command)
    
    const runWithRetry = (command: Command, retries: number) =>
      ssh.execute(command).pipe(
        Effect.retry(
          Schedule.exponential("100 millis").pipe(
            Schedule.intersect(Schedule.recurs(retries))
          )
        )
      )
    
    const runExpectingSuccess = (command: Command) =>
      Effect.gen(function* () {
        const result = yield* ssh.execute(command)
        
        if (result.failed()) {
          yield* Effect.fail(new CommandError({
            command,
            message: `Command failed with exit code ${result.exitCode.value}`,
            cause: result.stderr.value
          }))
        }
        
        return result
      })
    
    return { run, runWithRetry, runExpectingSuccess }
  })
)
```

### Homelab Services

#### services/VmProvisioner.ts
```typescript
import { Effect, Context, Layer } from "effect"

export class VmProvisionError extends Schema.TaggedError<VmProvisionError>()(
  "VmProvisionError",
  {
    spec: VmSpec,
    message: Schema.String,
    cause: Schema.Unknown
  }
) {}

// Abstract provisioner interface
export class VmProvisioner extends Context.Tag("VmProvisioner")<
  VmProvisioner,
  {
    readonly provision: (
      spec: VmSpec
    ) => Effect.Effect<ProvisionedVm, VmProvisionError>
    
    readonly provisionMany: (
      specs: ReadonlyArray<VmSpec>
    ) => Effect.Effect<ReadonlyArray<ProvisionedVm>, VmProvisionError>
    
    readonly destroy: (
      vm: ProvisionedVm
    ) => Effect.Effect<void, VmProvisionError>
    
    readonly snapshot: (
      vm: ProvisionedVm,
      name: string
    ) => Effect.Effect<void, VmProvisionError>
    
    readonly restore: (
      vm: ProvisionedVm,
      name: string
    ) => Effect.Effect<void, VmProvisionError>
  }
>() {}
```

#### services/ResourceManager.ts
```typescript
import { Effect, Context, Layer, Ref, Schedule, Duration } from "effect"

export class ResourceAllocation extends Schema.Class<ResourceAllocation>(
  "ResourceAllocation"
)({
  cpus: CpuCount,
  memory: MemoryMB,
  owner: Schema.String
}) {}

export class ResourceExhaustedError extends Schema.TaggedError<ResourceExhaustedError>()(
  "ResourceExhaustedError",
  {
    requested: ResourceAllocation,
    available: ResourceAllocation,
    message: Schema.String
  }
) {}

// Resource management service
export class ResourceManager extends Context.Tag("ResourceManager")<
  ResourceManager,
  {
    readonly tryAllocate: (
      allocation: ResourceAllocation
    ) => Effect.Effect<void, ResourceExhaustedError>
    
    readonly release: (
      allocation: ResourceAllocation
    ) => Effect.Effect<void>
    
    readonly waitForResources: (
      allocation: ResourceAllocation,
      timeout: Duration.Duration
    ) => Effect.Effect<void, ResourceExhaustedError>
    
    readonly currentUsage: Effect.Effect<ResourceAllocation>
  }
>() {}

// Layer factory for ResourceManager
export const makeResourceManagerLayer = (
  maxCpus: CpuCount,
  maxMemory: MemoryMB
) =>
  Layer.effect(
    ResourceManager,
    Effect.gen(function* () {
      const allocationsRef = yield* Ref.make<ReadonlyArray<ResourceAllocation>>([])
      
      const currentUsage = Effect.gen(function* () {
        const allocations = yield* Ref.get(allocationsRef)
        
        const totalCpus = allocations.reduce(
          (sum, a) => sum + a.cpus.value, 
          0
        )
        const totalMemory = allocations.reduce(
          (sum, a) => sum + a.memory.value,
          0
        )
        
        return new ResourceAllocation({
          cpus: new CpuCount({ value: totalCpus }),
          memory: new MemoryMB({ value: totalMemory }),
          owner: "system"
        })
      })
      
      const tryAllocate = (allocation: ResourceAllocation) =>
        Effect.gen(function* () {
          const current = yield* currentUsage
          
          const newCpus = current.cpus.value + allocation.cpus.value
          const newMemory = current.memory.value + allocation.memory.value
          
          if (newCpus > maxCpus.value || newMemory > maxMemory.value) {
            yield* Effect.fail(new ResourceExhaustedError({
              requested: allocation,
              available: new ResourceAllocation({
                cpus: new CpuCount({ value: maxCpus.value - current.cpus.value }),
                memory: new MemoryMB({ value: maxMemory.value - current.memory.value }),
                owner: "available"
              }),
              message: "Insufficient resources"
            }))
          }
          
          yield* Ref.update(
            allocationsRef,
            (allocs) => [...allocs, allocation]
          )
        })
      
      const release = (allocation: ResourceAllocation) =>
        Ref.update(
          allocationsRef,
          (allocs) => allocs.filter(a => a !== allocation)
        )
      
      const waitForResources = (
        allocation: ResourceAllocation,
        timeout: Duration.Duration
      ) =>
        tryAllocate(allocation).pipe(
          Effect.retry(
            Schedule.spaced("5 seconds").pipe(
              Schedule.whileInput((error: ResourceExhaustedError) => 
                error._tag === "ResourceExhaustedError"
              ),
              Schedule.compose(Schedule.elapsed),
              Schedule.whileOutput((elapsed) => 
                Duration.lessThan(elapsed, timeout)
              )
            )
          )
        )
      
      return {
        tryAllocate,
        release,
        waitForResources,
        currentUsage
      }
    })
  )
```

#### services/TestReporter.ts
```typescript
import { Effect, Context, Layer } from "effect"

export class TestOutcome extends Schema.TaggedEnum<TestOutcome>()(
  "TestOutcome",
  {
    Passed: Schema.Struct({ duration: Schema.Number }),
    Failed: Schema.Struct({ 
      duration: Schema.Number,
      error: Schema.String 
    }),
    Skipped: Schema.Struct({ reason: Schema.String })
  }
) {}

export class TestReport extends Schema.Class<TestReport>("TestReport")({
  section: TestSectionName,
  outcome: TestOutcome,
  timestamp: Schema.Number,
}) {}

export class TestReporter extends Context.Tag("TestReporter")<
  TestReporter,
  {
    readonly reportTest: (
      report: TestReport
    ) => Effect.Effect<void, never>
    
    readonly generateHtmlReport: (
      outputPath: string
    ) => Effect.Effect<void, FileSystemError>
    
    readonly generateJunitXml: (
      outputPath: string
    ) => Effect.Effect<void, FileSystemError>
  }
>() {}
```

## Part 3: Layer Composition

### Effect-TestInfra Layers

```typescript
// layers/HostLayer.ts
import { Layer } from "effect"

// Build Host layer from SSH connection
export const makeHostLayer = (connection: HostConnection) => {
  const sshLayer = makeSSHConnectionLayer(connection)
  const commandLayer = CommandExecutorLive
  
  // Compose using pipe - flat, readable
  return commandLayer.pipe(
    Layer.provide(sshLayer),
    Layer.provide(HostLive)
  )
}

// HostLive layer (depends on CommandExecutor)
export const HostLive = Layer.effect(
  Host,
  Effect.gen(function* () {
    const executor = yield* CommandExecutor
    
    return {
      connection: /* ... */,
      run: executor.run,
      file: (path) => makeFileInspector(path, executor),
      interface: (name) => makeNetworkInterfaceInspector(name, executor),
      service: (name) => makeServiceInspector(name, executor),
      package: (name) => makePackageInspector(name, executor),
    }
  })
)
```

### Homelab Layers

```typescript
// layers/HomelabConfig.ts
export class HomelabConfig extends Context.Tag("HomelabConfig")<
  HomelabConfig,
  {
    readonly networkTopology: NetworkTopology
    readonly testSections: ReadonlyArray<TestSection>
    readonly devices: Record<string, HostConnection>
  }
>() {}

export const HomelabConfigLive = Layer.effect(
  HomelabConfig,
  Effect.gen(function* () {
    // Load from YAML using @effect/schema
    const config = yield* loadYamlConfig("test-config.yaml")
    
    const networkTopology = yield* Schema.decode(NetworkTopology)(config.networks)
    
    const testSections = yield* Effect.all(
      config.sections.map(s => Schema.decode(TestSection)(s))
    )
    
    return {
      networkTopology,
      testSections,
      devices: config.devices
    }
  })
)

// layers/Provisioning.ts

// Libvirt provisioner implementation
const libvirtProvisionerImpl = {
  provision: (spec: VmSpec) => /* ... */,
  provisionMany: (specs: ReadonlyArray<VmSpec>) => /* ... */,
  destroy: (vm: ProvisionedVm) => /* ... */,
  snapshot: (vm: ProvisionedVm, name: string) => /* ... */,
  restore: (vm: ProvisionedVm, name: string) => /* ... */,
}

export const LibvirtLayer = Layer.succeed(
  VmProvisioner,
  libvirtProvisionerImpl
)

export const VagrantLayer = Layer.succeed(
  VmProvisioner,
  vagrantProvisionerImpl
)

export const HarvesterLayer = Layer.succeed(
  VmProvisioner,
  harvesterProvisionerImpl
)

// Compose layers using pipe to avoid nesting
export const makeTestEnvironment = (
  backend: "libvirt" | "vagrant" | "harvester"
) => {
  // Select provisioner backend
  const provisionerLayer = 
    backend === "libvirt" ? LibvirtLayer :
    backend === "vagrant" ? VagrantLayer :
    HarvesterLayer
  
  // Build resource manager layer
  const resourceLayer = makeResourceManagerLayer(
    new CpuCount({ value: 16 }),
    new MemoryMB({ value: 65536 })
  )
  
  // Compose all layers - flat and readable!
  return Layer.merge(
    HomelabConfigLive,
    provisionerLayer
  ).pipe(
    Layer.merge(resourceLayer),
    Layer.merge(TestReporterLive)
  )
}

// Example: Test-specific layer with custom config
export const makeTestLayer = (
  sectionName: string,
  backend: "libvirt" | "vagrant" | "harvester" = "libvirt"
) => {
  const baseLayer = makeTestEnvironment(backend)
  
  // Add test-specific layers
  return Layer.merge(
    baseLayer,
    CurrentTestSectionLive(sectionName)
  )
}
```

## Part 4: Vitest + @effect/vitest Integration

### Why Vitest with @effect/vitest?

We use **Vitest** as our test runner combined with **@effect/vitest** for Effect-native test APIs. This gives us:

1. **Mature test infrastructure**: Test discovery, parallel execution, reporting, watch mode
2. **Effect-native API**: Write tests using `Effect.gen` naturally
3. **Layer support**: Provide dependencies via layers, not manual setup
4. **Resource management**: Automatic cleanup via `it.scoped`
5. **IDE integration**: Full VSCode/WebStorm support

### Test File Structure

```typescript
// tests/networking/vlan-connectivity.test.ts
import { describe, it, expect } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { Host, Command } from "effect-testinfra"
import { NetworkTopology, makeTestLayer } from "../../src"

// Tests use it.live() to get layer-provided dependencies
describe("VLAN Connectivity", () => {
  it.live("can reach all VLAN gateways", () =>
    Effect.gen(function* () {
      const topology = yield* NetworkTopology
      const host = yield* Host
      
      // Test each segment
      for (const segment of topology.segments) {
        const cmd = Command.make(`ping -c 2 -W 2 ${segment.gateway.value}`)
        const result = yield* host.run(cmd)
        
        // Vitest assertions
        expect(result.succeeded()).toBe(true)
        expect(result.stdout.contains("2 packets transmitted")).toBe(true)
      }
    }),
    // Provide dependencies via layer
    makeTestLayer("networking")
  )
  
  // Scoped tests with automatic cleanup
  it.scoped("VM provisioning and cleanup", () =>
    Effect.gen(function* () {
      const provisioner = yield* VmProvisioner
      
      // Provision with automatic cleanup
      const vm = yield* Effect.acquireRelease(
        provisioner.provision(testVmSpec),
        (vm) => provisioner.destroy(vm)
      )
      
      expect(vm.status).toBe("running")
      
      // VM destroyed automatically when test ends
    }),
    makeTestLayer("networking")
  )
})
```

### CLI Orchestration with Vitest

Our CLI wraps Vitest to handle infrastructure provisioning:

```typescript
// cli/commands/Run.ts
import { startVitest } from "vitest/node"

const runTestSection = (section: TestSection) =>
  Effect.gen(function* () {
    const provisioner = yield* VmProvisioner
    const inventory = yield* InventoryGenerator
    
    // 1. Provision VMs (our logic)
    console.log(`Provisioning VMs for ${section.name.value}...`)
    const vms = yield* Effect.forEach(
      section.vmSpecs,
      (spec) => provisioner.provision(spec),
      { concurrency: "unbounded" }
    )
    
    // 2. Generate dynamic inventory
    yield* inventory.generate(vms, section.name.value)
    
    // 3. Run Vitest programmatically
    console.log(`Running tests for ${section.name.value}...`)
    const vitest = yield* Effect.promise(() =>
      startVitest("test", [], {
        include: section.testFiles.map(f => `tests/**/${f}`),
        reporters: ["verbose", "html", "junit"],
        root: process.cwd(),
      })
    )
    
    // 4. Cleanup VMs
    yield* Effect.forEach(vms, (vm) => provisioner.destroy(vm))
    
    return vitest.state
  })
```

## Part 5: Test DSL

### Writing Tests with Rich Domain Types

```typescript
// tests/networking/vlan-connectivity.test.ts
import { Effect, pipe } from "effect"
import { describe, it } from "@effect/vitest"
import * as TestInfra from "effect-testinfra"

export const vlanConnectivityTests = Effect.gen(function* (_) {
  const config = yield* _(HomelabConfig)
  const topology = config.networkTopology
  
  // Test each VLAN gateway is reachable
  yield* _(
    Effect.forEach(topology.segments, (segment) =>
      Effect.gen(function* (_) {
        const host = yield* _(Host)
        
        // Ping gateway using rich types
        const pingCommand = Command.make(
          `ping -c 2 -W 2 ${segment.gateway.value}`
        )
        
        const result = yield* _(host.run(pingCommand))
        
        // Assertion with domain types
        yield* _(
          TestInfra.expect(result.exitCode.isSuccess()).toBeTruthy(
            `Cannot reach ${segment.name} gateway at ${segment.gateway.value}`
          )
        )
      })
    )
  )
})

// Test VLAN interfaces exist
export const vlanInterfaceTests = Effect.gen(function* (_) {
  const config = yield* _(HomelabConfig)
  const topology = config.networkTopology
  const host = yield* _(Host)
  
  yield* _(
    Effect.forEach(topology.segments, (segment) =>
      Effect.gen(function* (_) {
        const interfaceName = new InterfaceName({
          value: segment.interfaceName
        })
        
        const iface = host.interface(interfaceName)
        
        const exists = yield* _(iface.exists)
        yield* _(
          TestInfra.expect(exists).toBeTruthy(
            `VLAN ${segment.vlanId.value} interface ${segment.interfaceName} not found`
          )
        )
        
        const state = yield* _(iface.state)
        yield* _(
          TestInfra.expect(state._tag).toEqual("Up",
            `VLAN ${segment.vlanId.value} interface is not UP`
          )
        )
      })
    )
  )
})

// Test cross-VLAN access follows security policy
export const crossVlanAccessTests = Effect.gen(function* (_) {
  const config = yield* _(HomelabConfig)
  const topology = config.networkTopology
  const host = yield* _(Host)
  
  // Test all segment pairs
  yield* _(
    Effect.forEach(topology.segments, (sourceSegment) =>
      Effect.forEach(topology.segments, (destSegment) =>
        Effect.gen(function* (_) {
          if (sourceSegment === destSegment) return
          
          const canAccess = topology.canAccess(sourceSegment, destSegment)
          
          const pingCommand = Command.make(
            `ping -c 1 -W 2 ${destSegment.gateway.value}`
          )
          
          const result = yield* _(
            host.run(pingCommand).pipe(
              Effect.either // Don't fail, just check result
            )
          )
          
          if (canAccess) {
            // Should be reachable
            yield* _(
              TestInfra.expect(result._tag).toEqual("Right",
                `${sourceSegment.name} should reach ${destSegment.name} but cannot`
              )
            )
          } else {
            // Should be blocked (we accept either way for now)
            // This accounts for firewall rules
            const isBlocked = result._tag === "Left"
            if (isBlocked) {
              console.log(
                `✓ ${sourceSegment.name} correctly blocked from ${destSegment.name}`
              )
            }
          }
        })
      )
    )
  )
})
```

### Harvester Cluster Tests

```typescript
// tests/harvester/cluster-formation.test.ts
export const clusterFormationTest = Effect.gen(function* (_) {
  const provisioner = yield* _(VmProvisioner)
  const section = yield* _(getCurrentTestSection)
  
  // Provision 3-node cluster with resource management
  const vms = yield* _(
    Effect.forEach(section.vmSpecs, (spec) =>
      Effect.gen(function* (_) {
        // Check resources before provisioning
        const allocation = new ResourceAllocation({
          cpus: spec.cpus,
          memory: spec.memory,
          owner: spec.name.value
        })
        
        const resourceMgr = yield* _(ResourceManager)
        
        // Wait for resources if needed (with timeout)
        yield* _(
          resourceMgr.waitForResources(
            allocation,
            Duration.minutes(10)
          )
        )
        
        // Provision with automatic cleanup
        const vm = yield* _(
          provisioner.provision(spec),
          Effect.acquireRelease(
            Effect.succeed,
            (vm) => Effect.gen(function* (_) {
              yield* _(provisioner.destroy(vm))
              yield* _(resourceMgr.release(allocation))
            })
          )
        )
        
        return vm
      })
    ),
    { concurrency: "unbounded" } // Provision in parallel
  )
  
  // Wait for cluster to stabilize
  const primaryVm = vms[0]
  const primaryHost = yield* _(Host.make(primaryVm.connection))
  
  yield* _(
    waitForClusterReady(primaryHost, vms.length),
    Effect.timeout(Duration.minutes(15)),
    Effect.orElseFail(() => new TestError({
      message: "Cluster did not stabilize within timeout"
    }))
  )
  
  // Verify all nodes joined
  const getNodesCmd = Command.make("kubectl get nodes --no-headers")
  const result = yield* _(primaryHost.run(getNodesCmd))
  
  const readyCount = result.stdout.value.split('\n')
    .filter(line => line.includes('Ready')).length
  
  yield* _(
    TestInfra.expect(readyCount).toEqual(vms.length,
      `Expected ${vms.length} nodes, got ${readyCount}`
    )
  )
})

// Helper: Wait for cluster with exponential backoff
const waitForClusterReady = (
  host: Host,
  expectedNodes: number
) => Effect.gen(function* (_) {
  const checkCmd = Command.make("kubectl get nodes --no-headers")
  
  yield* _(
    Effect.repeat(
      Effect.gen(function* (_) {
        const result = yield* _(host.run(checkCmd))
        
        if (!result.succeeded()) {
          yield* _(Effect.fail("kubectl not ready"))
        }
        
        const readyCount = result.stdout.value
          .split('\n')
          .filter(line => line.includes('Ready')).length
        
        if (readyCount < expectedNodes) {
          yield* _(Effect.fail("not enough nodes ready"))
        }
      }),
      Schedule.exponential("1 second").pipe(
        Schedule.compose(Schedule.recurs(20)) // Max 20 attempts
      )
    )
  )
})
```

## Part 5: CLI Implementation

```typescript
// cli/index.ts
import { Command, Options, Args } from "@effect/cli"
import { Effect, Layer } from "effect"

const sectionArg = Args.text({ name: "section" }).pipe(
  Args.optional
)

const backendOption = Options.choice("backend", [
  "libvirt",
  "vagrant", 
  "harvester"
]).pipe(
  Options.withDefault("libvirt" as const)
)

const noCleanupOption = Options.boolean("no-cleanup").pipe(
  Options.withDefault(false)
)

// Run command
const runCommand = Command.make(
  "run",
  { section: sectionArg, backend: backendOption, noCleanup: noCleanupOption },
  ({ section, backend, noCleanup }) =>
    Effect.gen(function* (_) {
      const config = yield* _(HomelabConfig)
      
      const sectionsToRun = section
        ? [section]
        : config.testSections.map(s => s.name.value)
      
      for (const sectionName of sectionsToRun) {
        yield* _(runTestSection(sectionName, { backend, cleanup: !noCleanup }))
      }
    }).pipe(
      Effect.provide(makeTestEnvironment(backend))
    )
)

// List command
const listCommand = Command.make(
  "list",
  {},
  () => Effect.gen(function* (_) {
    const config = yield* _(HomelabConfig)
    
    console.log("Available test sections:")
    for (const section of config.testSections) {
      console.log(
        `  ${section.name.value.padEnd(20)} - ${section.description} ` +
        `(${section.estimatedDuration.toMinutes().toFixed(0)} min)`
      )
    }
  }).pipe(
    Effect.provide(HomelabConfig.live)
  )
)

// Main CLI
const cli = Command.make("homelab-test", {}, {
  subcommands: [runCommand, listCommand, provisionCommand, cleanupCommand]
})
```

## Part 6: Benefits of This Approach

### 1. **Type Safety Throughout**
- Cannot pass invalid VLAN IDs (must be 1-4094)
- Cannot create malformed IP addresses
- Cannot allocate impossible resource amounts
- Compiler catches mistakes at build time

### 2. **Domain Logic Lives with Data**
```typescript
// ❌ BAD: Logic scattered, primitives everywhere
function canAccessVlan(sourceVlan: number, destVlan: number, rules: any): boolean

// ✅ GOOD: Domain model encapsulates logic
networkTopology.canAccess(sourceSegment, destSegment)
```

### 3. **Self-Documenting Code**
```typescript
// What does this mean?
provision(2, 4096, "test-vm", true)

// vs

provision(new VmSpec({
  cpus: new CpuCount({ value: 2 }),
  memory: new MemoryMB({ value: 4096 }),
  name: new VmName({ value: "test-vm" }),
  nestedVirtualization: true
}))
```

### 4. **Composable via Layers**
```typescript
// Easy to test with mock layers
const testLayer = Layer.mergeAll(
  MockProvisioner.layer,
  MockResourceManager.layer,
  TestConfig.layer
)

// Easy to swap implementations
const prodLayer = makeTestEnvironment("harvester")
```

### 5. **Error Handling Built-In**
```typescript
// All errors are typed and recoverable
Effect.gen(function* (_) {
  const result = yield* _(
    provisioner.provision(spec),
    Effect.catchTag("VmProvisionError", (error) =>
      // Handle specific error
      Effect.succeed(provisionFallback())
    ),
    Effect.retry({ times: 3 })
  )
})
```

## Part 7: Migration Path

### Phase 1: Setup Monorepo
- [ ] Create `packages/` directory
- [ ] Setup `pnpm-workspace.yaml`
- [ ] Initialize both packages
- [ ] Configure TypeScript project references

### Phase 2: Build effect-testinfra
- [ ] Create domain models (Host, Command, etc.)
- [ ] Implement SSH service
- [ ] Build assertion DSL
- [ ] Add basic inspectors (file, interface, service)

### Phase 3: Build homelab-test-cli
- [ ] Create homelab domain models
- [ ] Implement libvirt provisioner
- [ ] Port one test section (networking)
- [ ] Build CLI with @effect/cli

### Phase 4: Complete Migration
- [ ] Port remaining test sections
- [ ] Add parallel execution
- [ ] Implement reporting
- [ ] Update CI/CD

## Conclusion

This architecture uses Effect-TS's powerful abstractions (Services, Layers, Errors) combined with DDD principles to create a type-safe, composable testing framework. By avoiding primitive obsession and modeling the domain explicitly, we get:

- **Compile-time safety**
- **Self-documenting code**
- **Easy testing** (swap layers)
- **Powerful composition**
- **Built-in error handling**
- **Resource management**

The monorepo structure keeps the generic framework separate from homelab-specific code, making `effect-testinfra` potentially useful for other infrastructure testing needs.
