import { Schema } from "@effect/schema"
import { Effect } from "effect"
import { Command } from "./Command.js"
import { ExitCode } from "./ExitCode.js"
import { Stdout } from "./Stdout.js"
import { Stderr } from "./Stderr.js"

/**
 * CommandResult - Rich result from command execution
 * Contains everything about how the command executed
 */
export const CommandResult = Schema.Struct({
  command: Command,
  exitCode: ExitCode,
  stdout: Stdout,
  stderr: Stderr,
  duration: Schema.Number.pipe(Schema.nonnegative()), // milliseconds
})

export interface CommandResult extends Schema.Schema.Type<typeof CommandResult> {}

/**
 * Pure functions and Effects for working with CommandResults
 */
export namespace CommandResult {
  // Pure calculations
  export const succeeded = (result: CommandResult): boolean =>
    ExitCode.isSuccess(result.exitCode)
  
  export const failed = (result: CommandResult): boolean =>
    ExitCode.isFailure(result.exitCode)
  
  export const hasStderr = (result: CommandResult): boolean =>
    !Stderr.isEmpty(result.stderr)
  
  // Effect actions
  export const expectSuccess = (result: CommandResult): Effect.Effect<CommandResult, Error> =>
    succeeded(result)
      ? Effect.succeed(result)
      : Effect.fail(
          new Error(
            `Command failed with exit code ${result.exitCode}: ${result.command.value}\n` +
            `stderr: ${result.stderr}`
          )
        )
}
