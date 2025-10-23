import { describe, it, expect } from "@effect/vitest"
import { Effect } from "effect"
import { CommandNamespace, type Command } from "../Command.js"
import { ExitCodeNamespace, type ExitCode } from "../ExitCode.js"
import { StdoutNamespace, type Stdout } from "../Stdout.js"
import { StderrNamespace, type Stderr } from "../Stderr.js"
import { CommandResultNamespace, type CommandResult } from "../CommandResult.js"

describe("Command Domain", () => {
  it.effect("Command.make creates valid command", () =>
    Effect.gen(function* () {
      const cmd = CommandNamespace.make("ls -la")
      
      expect(cmd.value).toBe("ls -la")
      expect(cmd.timeout).toBeUndefined()
    })
  )
  
  it.effect("Command.pipe combines commands", () =>
    Effect.gen(function* () {
      const cmd1 = CommandNamespace.make("cat /etc/hosts")
      const cmd2 = CommandNamespace.make("grep localhost")
      
      const piped = CommandNamespace.pipe(cmd1, cmd2)
      
      expect(piped.value).toBe("cat /etc/hosts | grep localhost")
    })
  )
  
  it.effect("ExitCode.isSuccess detects success", () =>
    Effect.gen(function* () {
      const success = ExitCodeNamespace.Success
      const failure = ExitCodeNamespace.GeneralError
      
      expect(ExitCodeNamespace.isSuccess(success)).toBe(true)
      expect(ExitCodeNamespace.isSuccess(failure)).toBe(false)
    })
  )
  
  it.effect("Stdout.contains finds substrings", () =>
    Effect.gen(function* () {
      const stdout = "Hello World\nTest Output" as Stdout
      
      expect(StdoutNamespace.contains(stdout, "Hello")).toBe(true)
      expect(StdoutNamespace.contains(stdout, "Missing")).toBe(false)
      expect(StdoutNamespace.lines(stdout)).toHaveLength(2)
    })
  )
  
  it.effect("CommandResult.succeeded checks exit code", () =>
    Effect.gen(function* () {
      const result: CommandResult = {
        command: CommandNamespace.make("test"),
        exitCode: ExitCodeNamespace.Success,
        stdout: StdoutNamespace.Empty,
        stderr: StderrNamespace.Empty,
        duration: 100
      }
      
      expect(CommandResultNamespace.succeeded(result)).toBe(true)
      expect(CommandResultNamespace.failed(result)).toBe(false)
    })
  )
})
