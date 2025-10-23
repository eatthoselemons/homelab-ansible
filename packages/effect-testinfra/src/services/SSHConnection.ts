import { Effect, Layer } from "effect"
import { NodeSSH } from "node-ssh"
import type { HostConnection } from "../domain/Host.js"
import type { Command } from "../domain/Command.js"
import type { CommandResult } from "../domain/CommandResult.js"
import { ExitCode } from "../domain/ExitCode.js"
import { Stdout } from "../domain/Stdout.js"
import { Stderr } from "../domain/Stderr.js"
import { CommandError } from "../errors/CommandError.js"
import { SSHConnectionError } from "../errors/SSHConnectionError.js"

/**
 * SSHConnection Service interface
 */
export interface SSHConnection {
  readonly execute: (command: Command) => Effect.Effect<CommandResult, CommandError>
}

/**
 * SSHConnection Service - Manages SSH connection and command execution
 * 
 * This service provides low-level SSH command execution.
 * Resources are automatically managed via Layer.scoped.
 * 
 * Usage:
 * ```typescript
 * const program = Effect.gen(function* () {
 *   const ssh = yield* SSHConnection
 *   const result = yield* ssh.execute(command)
 * })
 * ```
 */
export class SSHConnection extends Effect.Service<SSHConnection>()(
  "SSHConnection",
  {
    effect: Effect.dieMessage("SSHConnection must be created via makeSSHConnectionLayer"),
    dependencies: []
  }
) {
  static Test = Layer.succeed(SSHConnection, {
    execute: (_command: Command) =>
      Effect.succeed({
        command: _command,
        exitCode: 0 as ExitCode,
        stdout: "mock output" as Stdout,
        stderr: "" as Stderr,
        duration: 100
      } satisfies CommandResult)
  })
}

/**
 * Create an SSHConnection layer for a given host
 * 
 * Uses Layer.scoped for automatic resource cleanup
 */
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
            message: `Failed to connect to ${connection.toSshConnectionString()}`,
            cause: error
          })
        }),
        () => Effect.sync(() => ssh.dispose())
      )
      
      // Return service implementation
      const execute = (command: Command) =>
        Effect.gen(function* () {
          const startTime = Date.now()
          
          const result = yield* Effect.tryPromise({
            try: () => ssh.execCommand(
              command.value,
              { 
                cwd: command.workingDir
              }
            ),
            catch: (error) => new CommandError({
              command,
              message: "Command execution failed",
              cause: error
            })
          })
          
          const duration = Date.now() - startTime
          
          return {
            command,
            exitCode: (result.code ?? 0) as ExitCode,
            stdout: (result.stdout ?? "") as Stdout,
            stderr: (result.stderr ?? "") as Stderr,
            duration
          } satisfies CommandResult
        })
      
      return { execute }
    })
  )
