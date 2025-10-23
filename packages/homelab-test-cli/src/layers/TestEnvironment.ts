import { Layer } from "effect"
import { HomelabConfigLive } from "./HomelabConfig.js"

/**
 * Complete test environment layer
 * Composes all necessary services for testing
 */
export const makeTestEnvironment = (
  backend: "libvirt" | "vagrant" | "harvester" = "libvirt"
) => {
  // For now, just provide config
  // TODO: Add provisioner, resource manager, etc.
  return HomelabConfigLive
}

/**
 * Create a test-specific layer
 */
export const makeTestLayer = (
  sectionName: string,
  backend: "libvirt" | "vagrant" | "harvester" = "libvirt"
) => {
  const baseLayer = makeTestEnvironment(backend)
  
  // TODO: Add test-specific context
  return baseLayer
}
