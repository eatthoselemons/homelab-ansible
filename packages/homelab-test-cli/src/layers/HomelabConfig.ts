import { Effect, Context, Layer } from "effect"
import { Schema } from "@effect/schema"
import { NetworkTopology } from "../domain/infrastructure/NetworkSegment.js"
import { TestSection } from "../domain/testing/TestSection.js"
import type { HostConnection } from "effect-testinfra"

/**
 * HomelabConfig Service - Configuration loaded from YAML
 */
export class HomelabConfig extends Context.Tag("HomelabConfig")<
  HomelabConfig,
  {
    readonly networkTopology: NetworkTopology
    readonly testSections: ReadonlyArray<TestSection>
    readonly devices: Record<string, HostConnection>
  }
>() {}

/**
 * HomelabConfig layer implementation
 * Loads configuration from YAML file
 */
export const HomelabConfigLive = Layer.effect(
  HomelabConfig,
  Effect.gen(function* () {
    // TODO: Load from YAML using @effect/schema
    // For now, return a placeholder
    
    const networkTopology = yield* Schema.decode(NetworkTopology)({
      segments: [],
      accessRules: {}
    })
    
    return {
      networkTopology,
      testSections: [],
      devices: {}
    }
  })
)
