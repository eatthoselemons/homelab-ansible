import { Schema } from "@effect/schema"
import { VmSpec } from "../provisioning/VmSpec.js"

/**
 * TestSectionName - NOT a string!
 */
export class TestSectionName extends Schema.Class<TestSectionName>("TestSectionName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z_]+$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * TestMarker - Test classification tags
 */
export class TestMarker extends Schema.Class<TestMarker>("TestMarker")({
  value: Schema.Literal("network", "storage", "critical", "slow", "harvester", "vyos")
}) {}

/**
 * EstimatedDuration - NOT a number!
 */
export class EstimatedDuration extends Schema.Class<EstimatedDuration>("EstimatedDuration")({
  milliseconds: Schema.Number.pipe(Schema.positive())
}) {
  static fromMinutes(minutes: number): EstimatedDuration {
    return new EstimatedDuration({ milliseconds: minutes * 60 * 1000 })
  }
  
  toMinutes(): number {
    return this.milliseconds / (60 * 1000)
  }
  
  isQuick(): boolean {
    return this.toMinutes() < 10
  }
}

/**
 * TestSection - Complete test section specification
 */
export class TestSection extends Schema.Class<TestSection>("TestSection")({
  name: TestSectionName,
  description: Schema.String,
  playbookPath: Schema.String,
  tags: Schema.Array(Schema.String),
  vmSpecs: Schema.Array(VmSpec),
  estimatedDuration: EstimatedDuration,
  requiresNestedVirt: Schema.Boolean,
  markers: Schema.Array(TestMarker),
  testFiles: Schema.Array(Schema.String),
}) {
  /**
   * Calculate total CPU requirements
   */
  totalCpus(): number {
    return this.vmSpecs.reduce((sum, vm) => sum + vm.cpus.value, 0)
  }
  
  /**
   * Calculate total memory requirements in MB
   */
  totalMemoryMB(): number {
    return this.vmSpecs.reduce((sum, vm) => sum + vm.memory.value, 0)
  }
  
  /**
   * Check if this is a quick test (< 10 minutes)
   */
  isQuick(): boolean {
    return this.estimatedDuration.isQuick()
  }
}
