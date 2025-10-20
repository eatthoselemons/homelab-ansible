import { Effect, Context, Layer, Schedule } from "effect"
import { SSHConnection } from "./SSHConnection.js"
import type { Command, CommandResult } from "../domain/Command.js"
import type { CommandError } from "../errors/CommandError.js"

/**
 * CommandExecutor Service - High-level command execution with retry logic
 * 
 * Builds on SSHConnection to provide retry logic and convenience methods.
 */
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

/**
 * CommandExecutor layer implementation
 * Depends on SSHConnection
 */
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
