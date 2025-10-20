import { Schema } from "@effect/schema"

/**
 * PackageName - NOT a string!
 * Represents a system package name
 */
export class PackageName extends Schema.Class<PackageName>("PackageName")({
  value: Schema.String.pipe(
    Schema.pattern(/^[a-z0-9_+-]+$/),
    Schema.nonEmptyString()
  )
}) {
  toString(): string {
    return this.value
  }
}

/**
 * PackageVersion - NOT a string!
 * Represents a package version
 */
export class PackageVersion extends Schema.Class<PackageVersion>("PackageVersion")({
  value: Schema.String.pipe(Schema.nonEmptyString())
}) {
  toString(): string {
    return this.value
  }
}
