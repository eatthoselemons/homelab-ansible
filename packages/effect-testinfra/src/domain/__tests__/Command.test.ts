import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"
import { Command } from "../Command.js"
import { ExitCode } from "../ExitCode.js"
import { Stdout } from "../Stdout.js"
import { Stderr } from "../Stderr.js"
import { CommandResult } from "../CommandResult.js"

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
      
      const piped = Command.pipe(cmd1, cmd2)
      
      expect(piped.value).toBe("cat /etc/hosts | grep localhost")
    })
  )
  
  it.effect("ExitCode.isSuccess detects success", () =>
    Effect.gen(function* () {
      const success = ExitCode.Success
      const failure = ExitCode.GeneralError
      
      expect(ExitCode.isSuccess(success)).toBe(true)
      expect(ExitCode.isSuccess(failure)).toBe(false)
    })
  )
  
  it.effect("Stdout.contains finds substrings", () =>
    Effect.gen(function* () {
      const stdout = "Hello World\nTest Output" as Stdout
      
      expect(Stdout.contains(stdout, "Hello")).toBe(true)
      expect(Stdout.contains(stdout, "Missing")).toBe(false)
      expect(Stdout.lines(stdout)).toHaveLength(2)
    })
  )
  
  it.effect("CommandResult.succeeded checks exit code", () =>
    Effect.gen(function* () {
      const result: CommandResult = {
        command: Command.make("test"),
        exitCode: ExitCode.Success,
        stdout: Stdout.Empty,
        stderr: Stderr.Empty,
        duration: 100
      }
      
      expect(CommandResult.succeeded(result)).toBe(true)
      expect(CommandResult.failed(result)).toBe(false)
    })
  )
})
