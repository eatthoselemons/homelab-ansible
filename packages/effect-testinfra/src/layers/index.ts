import { Layer } from "effect"
import type { HostConnection } from "../domain/Host.js"
import { makeSSHConnectionLayer } from "../services/SSHConnection.js"
import { CommandExecutor } from "../services/CommandExecutor.js"

/**
 * Create a complete layer stack for testing a host
 * 
 * Example:
 *   const layer = makeHostTestLayer(connection)
 *   const test = Effect.provide(myTest, layer)
 */
export const makeHostTestLayer = (connection: HostConnection) => {
  const sshLayer = makeSSHConnectionLayer(connection)
  
  return CommandExecutor.Default.pipe(
    Layer.provide(sshLayer)
  )
}
