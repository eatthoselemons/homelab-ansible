import { Schema } from "@effect/schema"
import { ReadonlyArray } from "effect"

/**
 * Stdout - NOT a string!
 * Represents command standard output with useful operations
 */
export const Stdout = Schema.String.pipe(Schema.brand("Stdout"))

export type Stdout = Schema.Schema.Type<typeof Stdout>

/**
 * Pure functions for working with Stdout
 */
export namespace Stdout {
  export const contains = (stdout: Stdout, substring: string): boolean =>
    stdout.includes(substring)
  
  export const matches = (stdout: Stdout, regex: RegExp): boolean =>
    regex.test(stdout)
  
  export const lines = (stdout: Stdout): ReadonlyArray<string> =>
    stdout.split('\n')
  
  export const isEmpty = (stdout: Stdout): boolean =>
    stdout.trim().length === 0
  
  export const lineCount = (stdout: Stdout): number =>
    lines(stdout).length
  
  export const Empty: Stdout = "" as Stdout
}
