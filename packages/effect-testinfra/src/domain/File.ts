import { Schema } from "@effect/schema"

/**
 * FilePath - NOT a string!
 * Represents a Unix file path with useful operations
 */
export class FilePath extends Schema.Class<FilePath>("FilePath")({
  value: Schema.String.pipe(Schema.nonEmptyString())
}) {
  get basename(): string {
    return this.value.split('/').pop() || ''
  }
  
  get dirname(): string {
    const parts = this.value.split('/')
    parts.pop()
    return parts.join('/') || '/'
  }
  
  join(other: string): FilePath {
    const normalized = `${this.value}/${other}`.replace(/\/+/g, '/')
    return new FilePath({ value: normalized })
  }
  
  toString(): string {
    return this.value
  }
}

/**
 * FileMode - NOT a number!
 * Represents Unix file permissions
 */
export class FileMode extends Schema.Class<FileMode>("FileMode")({
  value: Schema.Number.pipe(
    Schema.int(),
    Schema.between(0, 0o777)
  )
}) {
  toString(): string {
    return '0' + this.value.toString(8)
  }
  
  isExecutable(): boolean {
    return (this.value & 0o111) !== 0
  }
  
  isReadable(): boolean {
    return (this.value & 0o444) !== 0
  }
  
  isWritable(): boolean {
    return (this.value & 0o222) !== 0
  }
  
  static readonly ReadWrite = new FileMode({ value: 0o644 })
  static readonly Executable = new FileMode({ value: 0o755 })
}

/**
 * FileSize - NOT a number!
 * Represents file size in bytes with conversion methods
 */
export class FileSize extends Schema.Class<FileSize>("FileSize")({
  bytes: Schema.Number.pipe(Schema.nonnegative())
}) {
  toKB(): number {
    return this.bytes / 1024
  }
  
  toMB(): number {
    return this.bytes / (1024 * 1024)
  }
  
  toGB(): number {
    return this.bytes / (1024 * 1024 * 1024)
  }
}

/**
 * FileContent - NOT a string!
 * Represents file content with useful operations
 */
export class FileContent extends Schema.Class<FileContent>("FileContent")({
  value: Schema.String
}) {
  contains(substring: string): boolean {
    return this.value.includes(substring)
  }
  
  matches(regex: RegExp): boolean {
    return regex.test(this.value)
  }
  
  lines(): ReadonlyArray<string> {
    return this.value.split('\n')
  }
}
