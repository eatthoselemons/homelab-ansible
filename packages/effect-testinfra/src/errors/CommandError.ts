import { Data } from "effect"
import type { Command } from "../domain/Command.js"

/**
 * CommandError - Typed error for command execution failures
 */
export class CommandError extends Data.TaggedError("CommandError")<{
  readonly command: Command
  readonly message: string
  readonly cause?: unknown
}> {}
