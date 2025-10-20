import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"
import { Command, ExitCode, Stdout, Stderr } from "../Command.js"

describe("Command Domain", () => {
  it.effect("Command.make creates valid command", () =>
    Effect.gen(function* () {
      const cmd = Command.make("ls -la")
      
      expect(cmd.value).toBe("ls -la")
      expect(cmd.timeout).toBeUndefined()
    })
  )
  
  it.effect("Command.pipe combines commands", () =>
    Effect.gen(function* () {
      const cmd1 = Command.make("cat /etc/hosts")
      const cmd2 = Command.make("grep localhost")
      
      const piped = cmd1.pipe(cmd2)
      
      expect(piped.value).toBe("cat /etc/hosts | grep localhost")
    })
  )
  
  it.effect("ExitCode.isSuccess detects success", () =>
    Effect.gen(function* () {
      const success = new ExitCode({ value: 0 })
      const failure = new ExitCode({ value: 1 })
      
      expect(success.isSuccess()).toBe(true)
      expect(failure.isSuccess()).toBe(false)
    })
  )
  
  it.effect("Stdout.contains finds substrings", () =>
    Effect.gen(function* () {
      const stdout = new Stdout({ value: "Hello World\nTest Output" })
      
      expect(stdout.contains("Hello")).toBe(true)
      expect(stdout.contains("Missing")).toBe(false)
      expect(stdout.lines()).toHaveLength(2)
    })
  )
})
