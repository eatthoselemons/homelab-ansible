import { Schema } from "@effect/schema"

/**
 * Stderr - NOT a string!
 * Represents command standard error with useful operations
 */
export const StderrSchema = Schema.String.pipe(Schema.brand("Stderr"))

export type Stderr = Schema.Schema.Type<typeof StderrSchema>

/**
 * Pure functions for working with Stderr
 */
export namespace Stderr {
  export const isEmpty = (stderr: Stderr): boolean =>
    stderr.trim().length === 0
  
  export const contains = (stderr: Stderr, substring: string): boolean =>
    stderr.includes(substring)
  
  export const lines = (stderr: Stderr): readonly string[] =>
    stderr.split('\n')
  
  export const hasError = (stderr: Stderr): boolean =>
    !isEmpty(stderr)
  
  export const Empty: Stderr = "" as Stderr
}
