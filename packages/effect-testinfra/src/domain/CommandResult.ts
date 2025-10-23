import { Schema } from "@effect/schema"
import { Effect } from "effect"
import { Command } from "./Command.js"
import { ExitCode, ExitCodeNamespace } from "./ExitCode.js"
import { Stdout } from "./Stdout.js"
import { Stderr, StderrNamespace } from "./Stderr.js"
import { CommandError } from "../errors/CommandError.js"

/**
 * CommandResult - Rich result from command execution
 * Contains everything about how the command executed
 */
export const CommandResult = Schema.Struct({
  command: Command,
  exitCode: ExitCode,
  stdout: Stdout,
  stderr: Stderr,
  duration: Schema.Number.pipe(Schema.nonNegative()), // milliseconds
})

export type CommandResult = Schema.Schema.Type<typeof CommandResult>

/**
 * Pure functions and Effects for working with CommandResults
 */
export namespace CommandResultNamespace {
  // Pure calculations
  export const succeeded = (result: CommandResult): boolean =>
    ExitCodeNamespace.isSuccess(result.exitCode)
  
  export const failed = (result: CommandResult): boolean =>
    ExitCodeNamespace.isFailure(result.exitCode)
  
  export const hasStderr = (result: CommandResult): boolean =>
    !StderrNamespace.isEmpty(result.stderr)
  
  // Effect actions
  export const expectSuccess = (result: CommandResult): Effect.Effect<CommandResult, CommandError> =>
    succeeded(result)
      ? Effect.succeed(result)
      : Effect.fail(
          new CommandError({
            command: result.command,
            message: `Command failed with exit code ${result.exitCode}: ${result.stderr}`
          })
        )
}
