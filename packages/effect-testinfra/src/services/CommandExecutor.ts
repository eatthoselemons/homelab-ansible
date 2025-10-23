import { Effect, Layer, Schedule } from "effect"
import { SSHConnection } from "./SSHConnection.js"
import type { Command } from "../domain/Command.js"
import type { CommandResult } from "../domain/CommandResult.js"
import type { ExitCode } from "../domain/ExitCode.js"
import type { Stdout } from "../domain/Stdout.js"
import type { Stderr } from "../domain/Stderr.js"
import { CommandResultNamespace } from "../domain/CommandResult.js"
import { CommandError } from "../errors/CommandError.js"

/**
 * CommandExecutor Service interface
 */
export interface CommandExecutor {
  readonly run: (command: Command) => Effect.Effect<CommandResult, CommandError>
  readonly runWithRetry: (command: Command, retries: number) => Effect.Effect<CommandResult, CommandError>
  readonly runExpectingSuccess: (command: Command) => Effect.Effect<CommandResult, CommandError>
}

/**
 * CommandExecutor Service - High-level command execution with retry logic
 * 
 * Builds on SSHConnection to provide retry logic and convenience methods.
 * 
 * Usage:
 * ```typescript
 * const program = Effect.gen(function* () {
 *   const executor = yield* CommandExecutor
 *   const result = yield* executor.runExpectingSuccess(command)
 * })
 * ```
 */
export class CommandExecutor extends Effect.Service<CommandExecutor>()(
  "CommandExecutor",
  {
    effect: Effect.gen(function* () {
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
          
          if (CommandResultNamespace.failed(result)) {
            yield* Effect.fail(new CommandError({
              command,
              message: `Command failed with exit code ${result.exitCode}`,
              cause: result.stderr
            }))
          }
          
          return result
        })
      
      return { run, runWithRetry, runExpectingSuccess }
    }),
    dependencies: [SSHConnection.Default]
  }
) {
  static Test = Layer.succeed(CommandExecutor, {
    run: (command: Command) =>
      Effect.succeed({
        command,
        exitCode: 0 as ExitCode,
        stdout: "test output" as Stdout,
        stderr: "" as Stderr,
        duration: 50
      } satisfies CommandResult),
    runWithRetry: (command: Command, _retries: number) =>
      Effect.succeed({
        command,
        exitCode: 0 as ExitCode,
        stdout: "test output" as Stdout,
        stderr: "" as Stderr,
        duration: 50
      } satisfies CommandResult),
    runExpectingSuccess: (command: Command) =>
      Effect.succeed({
        command,
        exitCode: 0 as ExitCode,
        stdout: "test output" as Stdout,
        stderr: "" as Stderr,
        duration: 50
      } satisfies CommandResult)
  })
}
