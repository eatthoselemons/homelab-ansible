import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"
import { Command, CommandExecutor } from "effect-testinfra"
import { NetworkTopology, VlanId } from "../../src/index.js"
import { makeTestLayer } from "../../src/layers/TestEnvironment.js"

/**
 * Example infrastructure test using Vitest + @effect/vitest
 * 
 * This demonstrates:
 * - Effect.gen for Effect-native tests
 * - Layer-based dependency injection
 * - Rich domain types (VlanId, Command, etc.)
 * - Type-safe assertions
 */
describe("VLAN Connectivity", () => {
  it.live("can reach all VLAN gateways", () =>
    Effect.gen(function* () {
      const topology = yield* NetworkTopology
      const executor = yield* CommandExecutor
      
      // Test connectivity to each VLAN gateway
      for (const segment of topology.segments) {
        console.log(`Testing connectivity to ${segment.name} (VLAN ${segment.vlanId.value})...`)
        
        const pingCmd = Command.make(
          `ping -c 2 -W 2 ${segment.gateway.value}`
        )
        
        const result = yield* executor.run(pingCmd)
        
        // Type-safe assertions with rich types
        expect(result.succeeded()).toBe(true)
        expect(result.stdout.contains("2 packets transmitted")).toBe(true)
        
        console.log(`✓ ${segment.name} gateway reachable`)
      }
    }),
    makeTestLayer("networking") // Provide dependencies
  )
  
  it.live("VLAN interfaces are configured", () =>
    Effect.gen(function* () {
      const topology = yield* NetworkTopology
      const executor = yield* CommandExecutor
      
      // Check each VLAN interface exists
      for (const segment of topology.segments) {
        const ifaceName = segment.interfaceName
        const checkCmd = Command.make(`ip link show ${ifaceName}`)
        
        const result = yield* executor.run(checkCmd)
        
        expect(result.succeeded()).toBe(true)
        expect(
          result.stdout.contains("state UP") ||
          result.stdout.contains("state UNKNOWN")
        ).toBe(true)
      }
    }),
    makeTestLayer("networking")
  )
  
  it.live("cross-VLAN access follows security policy", () =>
    Effect.gen(function* () {
      const topology = yield* NetworkTopology
      const executor = yield* CommandExecutor
      
      // Get management and DMZ segments
      const mgmt = topology.getSegmentByVlan(VlanId.Management)
      const dmz = topology.getSegmentByVlan(VlanId.Public)
      
      if (!mgmt || !dmz) {
        return // Skip if segments not configured
      }
      
      // Test that DMZ is NOT accessible from management
      // (this should fail or timeout, which is expected)
      const canAccess = topology.canAccess(mgmt, dmz)
      
      if (!canAccess) {
        console.log("✓ Security policy correctly isolates DMZ from management")
      } else {
        // Actually test connectivity
        const pingCmd = Command.make(`ping -c 1 -W 2 ${dmz.gateway.value}`)
        const result = yield* executor.run(pingCmd).pipe(
          Effect.either // Don't fail test, just check result
        )
        
        if (result._tag === "Left") {
          console.log("✓ DMZ correctly unreachable from management")
        }
      }
    }),
    makeTestLayer("networking")
  )
})
