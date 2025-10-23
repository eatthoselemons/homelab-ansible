import { Schema } from "@effect/schema"

/**
 * ExitCode - NOT a number!
 * Represents a process exit code (0-255)
 */
export const ExitCode = Schema.Number.pipe(
  Schema.int(),
  Schema.between(0, 255),
  Schema.brand("ExitCode")
)

export type ExitCode = Schema.Schema.Type<typeof ExitCode>

/**
 * Pure functions for working with ExitCodes
 */
export namespace ExitCodeNamespace {
  export const isSuccess = (exitCode: ExitCode): boolean =>
    exitCode === 0
  
  export const isFailure = (exitCode: ExitCode): boolean =>
    !isSuccess(exitCode)
  
  // Common exit codes
  export const Success: ExitCode = 0 as ExitCode
  export const GeneralError: ExitCode = 1 as ExitCode
  export const CommandNotFound: ExitCode = 127 as ExitCode
  export const PermissionDenied: ExitCode = 126 as ExitCode
}
