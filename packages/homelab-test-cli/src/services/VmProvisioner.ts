import { Effect, Context } from "effect"
import { VmSpec, ProvisionedVm } from "../domain/provisioning/VmSpec.js"

/**
 * VmProvisionError - Typed error for VM provisioning failures
 */
export class VmProvisionError extends Effect.Error<{
  readonly spec: VmSpec
  readonly message: string
  readonly cause?: unknown
}>("VmProvisionError") {}

/**
 * VmProvisioner Service - Abstract interface for VM provisioning
 * 
 * Different backends (libvirt, vagrant, harvester) implement this interface
 */
export class VmProvisioner extends Context.Tag("VmProvisioner")<
  VmProvisioner,
  {
    readonly provision: (
      spec: VmSpec
    ) => Effect.Effect<ProvisionedVm, VmProvisionError>
    
    readonly provisionMany: (
      specs: ReadonlyArray<VmSpec>
    ) => Effect.Effect<ReadonlyArray<ProvisionedVm>, VmProvisionError>
    
    readonly destroy: (
      vm: ProvisionedVm
    ) => Effect.Effect<void, VmProvisionError>
    
    readonly snapshot: (
      vm: ProvisionedVm,
      name: string
    ) => Effect.Effect<void, VmProvisionError>
    
    readonly restore: (
      vm: ProvisionedVm,
      name: string
    ) => Effect.Effect<void, VmProvisionError>
  }
>() {}
