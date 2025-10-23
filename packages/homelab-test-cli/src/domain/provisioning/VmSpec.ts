import { Schema } from "@effect/schema"
import { HostConnection } from "effect-testinfra"

/**
 * VmName - NOT a string!
 * Represents a valid VM name
 */
export class VmName extends Schema.Class<VmName>("VmName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9-]+$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * CpuCount - NOT a number!
 * Represents number of CPU cores
 */
export class CpuCount extends Schema.Class<CpuCount>("CpuCount")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 64)
  )
}) {}

/**
 * MemoryMB - NOT a number!
 * Represents memory in megabytes
 */
export class MemoryMB extends Schema.Class<MemoryMB>("MemoryMB")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(512, 524288) // 512MB to 512GB
  )
}) {
  toGB(): number {
    return this.value / 1024
  }
}

/**
 * DiskSizeGB - NOT a number!
 * Represents disk size in gigabytes
 */
export class DiskSizeGB extends Schema.Class<DiskSizeGB>("DiskSizeGB")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 10000)
  )
}) {}

/**
 * DiskSpec - Specification for a virtual disk
 */
export class DiskSpec extends Schema.Class<DiskSpec>("DiskSpec")({
  size: DiskSizeGB,
  type: Schema.Literal("virtio", "scsi", "ide"),
}) {}

/**
 * NetworkInterfaceCount - NOT a number!
 */
export class NetworkInterfaceCount extends Schema.Class<NetworkInterfaceCount>(
  "NetworkInterfaceCount"
)({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(1, 8)
  )
}) {}

/**
 * VmSpec - Complete VM specification
 */
export class VmSpec extends Schema.Class<VmSpec>("VmSpec")({
  name: VmName,
  cpus: CpuCount,
  memory: MemoryMB,
  disks: Schema.Array(DiskSpec),
  networkInterfaces: NetworkInterfaceCount,
  nestedVirtualization: Schema.Boolean,
  baseImage: Schema.optional(Schema.String),
}) {
  /**
   * Check if this VM requires a high-memory host
   */
  requiresHighMemoryHost(): boolean {
    return this.memory.value > 16384 // > 16GB
  }
  
  /**
   * Calculate total disk space required
   */
  totalDiskGB(): number {
    return this.disks.reduce((sum, disk) => sum + disk.size.value, 0)
  }
}

/**
 * ProvisionedVm - A VM that has been provisioned
 */
export class ProvisionedVm extends Schema.Class<ProvisionedVm>("ProvisionedVm")({
  spec: VmSpec,
  connection: HostConnection,
  vmId: Schema.String,
  status: Schema.Literal("running", "stopped", "error"),
}) {}
