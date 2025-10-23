import { Schema } from "@effect/schema"

/**
 * Command - NOT a string!
 * Represents a shell command with optional configuration
 * 
 * Using Schema.Struct + namespace pattern (no `this` keyword)
 */
export const Command = Schema.Struct({
  value: Schema.String.pipe(Schema.nonEmptyString()),
  timeout: Schema.optional(Schema.Number.pipe(Schema.positive())),
  workingDir: Schema.optional(Schema.String),
})

export interface Command extends Schema.Schema.Type<typeof Command> {}

/**
 * Pure functions for working with Commands
 */
export namespace Command {
  /**
   * Create a simple command from a string
   */
  export const make = (
    value: string,
    options?: {
      timeout?: number
      workingDir?: string
    }
  ): Command => ({
    value,
    timeout: options?.timeout,
    workingDir: options?.workingDir
  })
  
  /**
   * Pipe two commands together
   */
  export const pipe = (cmd1: Command, cmd2: Command): Command => ({
    value: `${cmd1.value} | ${cmd2.value}`,
    timeout: cmd1.timeout,
    workingDir: cmd1.workingDir
  })
  
  /**
   * Pipe multiple commands together
   */
  export const pipeMany = (commands: ReadonlyArray<Command>): Command =>
    commands.reduce(pipe)
}


