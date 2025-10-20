import { Effect, Context, Layer } from "effect"
import { NodeSSH } from "node-ssh"
import type { HostConnection } from "../domain/Host.js"
import { Command, CommandResult, ExitCode, Stdout, Stderr } from "../domain/Command.js"
import { CommandError } from "../errors/CommandError.js"
import { SSHConnectionError } from "../errors/SSHConnectionError.js"

/**
 * SSHConnection Service - Manages SSH connection and command execution
 * 
 * This service provides low-level SSH command execution.
 * Resources are automatically managed via Layer.scoped.
 */
export class SSHConnection extends Context.Tag("SSHConnection")<
  SSHConnection,
  {
    readonly execute: (
      command: Command
    ) => Effect.Effect<CommandResult, CommandError>
  }
>() {}

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
