# homelab-test-cli

CLI tool for testing homelab infrastructure using effect-testinfra.

## Installation

```bash
pnpm install
pnpm build
```

## Usage

```bash
# List available test sections
homelab-test list

# Run specific test section
homelab-test run networking

# Run with specific backend
homelab-test run networking --backend libvirt

# Run all tests
homelab-test run --all

# Run quick tests only (< 10 minutes)
homelab-test run --quick
```

## Project Structure

- `src/domain/` - Domain models (VLANs, VMs, Tests)
- `src/services/` - Business logic services
- `src/layers/` - Effect layers for DI
- `src/cli/` - CLI implementation
- `tests/` - Actual infrastructure tests

## Writing Tests

See `tests/networking/` for examples of infrastructure tests using Vitest + @effect/vitest.
