import { Schema } from "@effect/schema"
import { Effect } from "effect"
import { CommandSchema } from "./Command.js"
import { ExitCodeSchema, ExitCode } from "./ExitCode.js"
import { StdoutSchema } from "./Stdout.js"
import { StderrSchema, Stderr } from "./Stderr.js"
import { CommandError } from "../errors/CommandError.js"

/**
 * CommandResult - Rich result from command execution
 * Contains everything about how the command executed
 */
export const CommandResultSchema = Schema.Struct({
  command: CommandSchema,
  exitCode: ExitCodeSchema,
  stdout: StdoutSchema,
  stderr: StderrSchema,
  duration: Schema.Number.pipe(Schema.nonNegative()), // milliseconds
})

export type CommandResult = Schema.Schema.Type<typeof CommandResultSchema>

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
