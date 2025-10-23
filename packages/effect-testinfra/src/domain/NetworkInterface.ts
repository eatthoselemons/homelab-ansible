import { Schema } from "@effect/schema"
import { Effect } from "effect"

/**
 * InterfaceName - NOT a string!
 * Represents a valid network interface name
 */
export class InterfaceName extends Schema.Class<InterfaceName>("InterfaceName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9]+[a-z0-9._-]*$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
  
  static readonly loopback = new InterfaceName({ value: "lo" })
  static readonly eth0 = new InterfaceName({ value: "eth0" })
}

/**
 * MacAddress - NOT a string!
 * Represents a validated MAC address
 */
export class MacAddress extends Schema.Class<MacAddress>("MacAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/)
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * IpAddress - NOT a string!
 * Represents a validated IPv4 address
 */
export class IpAddress extends Schema.Class<IpAddress>("IpAddress")({
  value: Schema.String.pipe(
    Schema.pattern(/^(\d{1,3}\.){3}\d{1,3}$/)
  )
}) {
  toString(): string {
    return this.value
  }
  
  /**
   * Parse a string into an IpAddress with validation
   */
  static parse(value: string): Effect.Effect<IpAddress, Schema.ParseError> {
    return Schema.decode(IpAddress)({ value })
  }
  
  static readonly localhost = new IpAddress({ value: "127.0.0.1" })
}

/**
 * Netmask - NOT a number!
 * Represents a CIDR netmask (0-32)
 */
export class Netmask extends Schema.Class<Netmask>("Netmask")({
  value: Schema.Number.pipe(Schema.int(), Schema.between(0, 32))
}) {
  toString(): string {
    return `/${this.value}`
  }
}

/**
 * InterfaceState - Tagged union for interface state
 * More type-safe than string literals
 */
export class InterfaceState extends Schema.TaggedEnum<InterfaceState>()(
  "InterfaceState",
  {
    Up: Schema.Struct({}),
    Down: Schema.Struct({}),
    Unknown: Schema.Struct({})
  }
) {}

/**
 * NetworkInterface - Rich domain model for network interfaces
 * Contains all information about a network interface
 */
export class NetworkInterface extends Schema.Class<NetworkInterface>("NetworkInterface")({
  name: InterfaceName,
  state: InterfaceState,
  addresses: Schema.Array(IpAddress),
  macAddress: Schema.optional(MacAddress),
  mtu: Schema.optional(Schema.Number.pipe(Schema.positive())),
}) {
  isUp(): boolean {
    return this.state._tag === "Up"
  }
  
  isDown(): boolean {
    return this.state._tag === "Down"
  }
  
  hasAddress(addr: IpAddress): boolean {
    return this.addresses.some(a => a.value === addr.value)
  }
}
