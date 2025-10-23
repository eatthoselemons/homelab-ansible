import { Schema } from "@effect/schema"

/**
 * ServiceName - NOT a string!
 * Represents a system service name
 */
export class ServiceName extends Schema.Class<ServiceName>("ServiceName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9_-]+$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
  
  static readonly sshd = new ServiceName({ value: "sshd" })
  static readonly nginx = new ServiceName({ value: "nginx" })
  static readonly docker = new ServiceName({ value: "docker" })
}

/**
 * ServiceState - Tagged union for service states
 */
export class ServiceState extends Schema.TaggedEnum<ServiceState>()(
  "ServiceState",
  {
    Running: Schema.Struct({}),
    Stopped: Schema.Struct({}),
    Failed: Schema.Struct({ reason: Schema.String }),
    Unknown: Schema.Struct({})
  }
) {}
