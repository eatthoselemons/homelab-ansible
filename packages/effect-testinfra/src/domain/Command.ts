import { Schema } from "@effect/schema"
import { Effect } from "effect"

/**
 * Command - NOT a string!
 * Represents a shell command with optional configuration
 */
export class Command extends Schema.Class<Command>("Command")({
  value: Schema.String.pipe(Schema.nonEmptyString()),
  timeout: Schema.optional(Schema.Number.pipe(Schema.positive())),
  workingDir: Schema.optional(Schema.String),
}) {
  /**
   * Create a simple command from a string
   */
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
  
  /**
   * Pipe multiple commands together
   */
  pipe(other: Command): Command {
    return new Command({
      value: `${this.value} | ${other.value}`,
      timeout: this.timeout,
      workingDir: this.workingDir
    })
  }
}

/**
 * ExitCode - NOT a number!
 * Represents a process exit code
 */
export class ExitCode extends Schema.Class<ExitCode>("ExitCode")({
  value: Schema.Number.pipe(Schema.int(), Schema.between(0, 255))
}) {
  isSuccess(): boolean {
    return this.value === 0
  }
  
  isFailure(): boolean {
    return this.value !== 0
  }
  
  static readonly Success = new ExitCode({ value: 0 })
  static readonly GeneralError = new ExitCode({ value: 1 })
  static readonly CommandNotFound = new ExitCode({ value: 127 })
}

/**
 * Stdout - NOT a string!
 * Represents command standard output with useful operations
 */
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
  
  isEmpty(): boolean {
    return this.value.trim().length === 0
  }
  
  static readonly Empty = new Stdout({ value: "" })
}

/**
 * Stderr - NOT a string!
 * Represents command standard error with useful operations
 */
export class Stderr extends Schema.Class<Stderr>("Stderr")({
  value: Schema.String
}) {
  isEmpty(): boolean {
    return this.value.trim().length === 0
  }
  
  contains(substring: string): boolean {
    return this.value.includes(substring)
  }
  
  lines(): ReadonlyArray<string> {
    return this.value.split('\n')
  }
  
  static readonly Empty = new Stderr({ value: "" })
}

/**
 * CommandResult - Rich result from command execution
 * Contains everything about how the command executed
 */
export class CommandResult extends Schema.Class<CommandResult>("CommandResult")({
  command: Command,
  exitCode: ExitCode,
  stdout: Stdout,
  stderr: Stderr,
  duration: Schema.Number.pipe(Schema.nonnegative()), // milliseconds
}) {
  succeeded(): boolean {
    return this.exitCode.isSuccess()
  }
  
  failed(): boolean {
    return this.exitCode.isFailure()
  }
  
  /**
   * Get the result or fail with an error
   */
  expectSuccess(): Effect.Effect<CommandResult, Error> {
    if (this.succeeded()) {
      return Effect.succeed(this)
    }
    return Effect.fail(
      new Error(
        `Command failed with exit code ${this.exitCode.value}: ${this.command.value}\n` +
        `stderr: ${this.stderr.value}`
      )
    )
  }
}
