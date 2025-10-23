import { Schema } from "@effect/schema"
import { Context } from "effect"
import type { Command } from "./Command.js"
import type { CommandResult } from "./CommandResult.js"
import type { CommandError } from "../errors/CommandError.js"

/**
 * HostAddress - NOT a string!
 * Represents a validated hostname or IP address
 */
export class HostAddress extends Schema.Class<HostAddress>("HostAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-zA-Z0-9.-]+$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * Port - NOT a number!
 * Represents a valid network port
 */
export class Port extends Schema.Class<Port>("Port")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 65535)
  )
}) {
  toString(): string {
    return this.value.toString()
  }
  
  static readonly SSH = new Port({ value: 22 })
  static readonly HTTP = new Port({ value: 80 })
  static readonly HTTPS = new Port({ value: 443 })
}

/**
 * Username - NOT a string!
 * Represents a valid Unix username
 */
export class Username extends Schema.Class<Username>("Username")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z_][a-z0-9_-]*$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
  
  static readonly root = new Username({ value: "root" })
  static readonly vagrant = new Username({ value: "vagrant" })
}

/**
 * SshKeyPath - NOT a string!
 * Represents a path to an SSH private key
 */
export class SshKeyPath extends Schema.Class<SshKeyPath>("SshKeyPath")({
  value: Schema.String.pipe(Schema.nonEmptyString())
}) {
  toString(): string {
    return this.value
  }
}

/**
 * HostConnection - Rich domain model for SSH connection
 * Contains all information needed to connect to a host
 */
export class HostConnection extends Schema.Class<HostConnection>("HostConnection")({
  address: HostAddress,
  port: Port,
  username: Username,
  keyPath: SshKeyPath,
}) {
  /**
   * Format as SSH connection string: user@host:port
   */
  toSshConnectionString(): string {
    return `${this.username.value}@${this.address.value}:${this.port.value}`
  }
  
  /**
   * Create a HostConnection for localhost with defaults
   */
  static localhost(keyPath: SshKeyPath): HostConnection {
    return new HostConnection({
      address: new HostAddress({ value: "localhost" }),
      port: Port.SSH,
      username: Username.vagrant,
      keyPath
    })
  }
}

/**
 * Host Service - Main API for interacting with remote hosts
 * 
 * This is the primary interface for infrastructure testing.
 * It provides access to command execution, file inspection,
 * network interface inspection, etc.
 */
export class Host extends Context.Tag("Host")<
  Host,
  {
    readonly connection: HostConnection
    readonly run: (command: Command) => Effect.Effect<CommandResult, CommandError>
    // These would return inspector interfaces
    // readonly file: (path: FilePath) => FileInspector
    // readonly interface: (name: InterfaceName) => NetworkInterfaceInspector
    // readonly service: (name: ServiceName) => ServiceInspector
    // readonly package: (name: PackageName) => PackageInspector
  }
>() {}
