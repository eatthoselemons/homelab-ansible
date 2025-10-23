import { Schema } from "@effect/schema"
import { IpAddress } from "effect-testinfra"
import { VlanId } from "./VlanId.js"

/**
 * SubnetCidr - NOT a string!
 * Represents a CIDR notation subnet
 */
export class SubnetCidr extends Schema.Class<SubnetCidr>("SubnetCidr")({
  value: Schema.String.pipe(
    Schema.pattern(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/)
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * DomainName - NOT a string!
 * Represents a validated domain name
 */
export class DomainName extends Schema.Class<DomainName>("DomainName")({
  value: Schema.String.pipe(
    Schema.pattern(/^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$/)
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * NetworkSegment - Rich domain model for network segments
 * Represents a VLAN with its configuration
 */
export class NetworkSegment extends Schema.Class<NetworkSegment>("NetworkSegment")({
  name: Schema.String,
  vlanId: VlanId,
  subnet: SubnetCidr,
  gateway: IpAddress,
  domain: Schema.optional(DomainName),
}) {
  /**
   * Get the interface name for this VLAN
   * e.g., "bond0.10" for VLAN 10
   */
  get interfaceName(): string {
    return `bond0${this.vlanId.toInterfaceSuffix()}`
  }
  
  /**
   * Check if an IP belongs to this segment's subnet
   * Simplified implementation - full CIDR matching would go here
   */
  containsIp(ip: IpAddress): boolean {
    const [network, _bits] = this.subnet.value.split('/')
    return ip.value.startsWith(network.split('.').slice(0, 2).join('.'))
  }
}

/**
 * NetworkTopology - Complete network topology with access rules
 */
export class NetworkTopology extends Schema.Class<NetworkTopology>("NetworkTopology")({
  segments: Schema.Array(NetworkSegment),
  accessRules: Schema.Record(
    Schema.String,
    Schema.Array(Schema.String)
  )
}) {
  /**
   * Check if traffic can flow from one segment to another
   */
  canAccess(from: NetworkSegment, to: NetworkSegment): boolean {
    const allowed = this.accessRules[from.name] || []
    return allowed.includes(to.name)
  }
  
  /**
   * Find a segment by VLAN ID
   */
  getSegmentByVlan(vlan: VlanId): NetworkSegment | undefined {
    return this.segments.find(s => s.vlanId.value === vlan.value)
  }
  
  /**
   * Get all segments that a given segment can access
   */
  getAccessibleSegments(from: NetworkSegment): ReadonlyArray<NetworkSegment> {
    const allowed = this.accessRules[from.name] || []
    return this.segments.filter(s => allowed.includes(s.name))
  }
}
