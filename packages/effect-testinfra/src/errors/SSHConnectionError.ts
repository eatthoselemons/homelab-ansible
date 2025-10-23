import { Data } from "effect"

/**
 * SSHConnectionError - Typed error for SSH connection failures
 */
export class SSHConnectionError extends Data.TaggedError("SSHConnectionError")<{
  readonly message: string
  readonly cause?: unknown
}> {}
