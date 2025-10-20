import { Schema } from "@effect/schema"

/**
 * VlanId - NOT a number!
 * Represents a validated VLAN ID (1-4094)
 */
export class VlanId extends Schema.Class<VlanId>("VlanId")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 4094) // Valid VLAN range per IEEE 802.1Q
  )
}) {
  toString(): string {
    return this.value.toString()
  }
  
  toInterfaceSuffix(): string {
    return `.${this.value}`
  }
  
  // Homelab-specific VLANs as constants
  static readonly Management = new VlanId({ value: 10 })
  static readonly Private = new VlanId({ value: 20 })
  static readonly Public = new VlanId({ value: 30 })
  static readonly Storage = new VlanId({ value: 40 })
  static readonly Backup = new VlanId({ value: 50 })
  static readonly GuestWifi = new VlanId({ value: 60 })
  static readonly TrustedWifi = new VlanId({ value: 70 })
  static readonly IoT = new VlanId({ value: 80 })
  static readonly Logs = new VlanId({ value: 90 })
}
