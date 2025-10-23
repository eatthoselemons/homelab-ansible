import { Schema } from "@effect/schema"
import { ReadonlyArray } from "effect"

/**
 * Stderr - NOT a string!
 * Represents command standard error with useful operations
 */
export const Stderr = Schema.String.pipe(Schema.brand("Stderr"))

export type Stderr = Schema.Schema.Type<typeof Stderr>

/**
 * Pure functions for working with Stderr
 */
export namespace Stderr {
  export const isEmpty = (stderr: Stderr): boolean =>
    stderr.trim().length === 0
  
  export const contains = (stderr: Stderr, substring: string): boolean =>
    stderr.includes(substring)
  
  export const lines = (stderr: Stderr): ReadonlyArray<string> =>
    stderr.split('\n')
  
  export const hasError = (stderr: Stderr): boolean =>
    !isEmpty(stderr)
  
  export const Empty: Stderr = "" as Stderr
}
