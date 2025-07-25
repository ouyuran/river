# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

River is a Python-native orchestration system for automating complex task workflows across distributed sandboxes. It consists of:

- **SDK** (`sdk/`): Core orchestration components (Job, Task, Sandbox abstractions)
- **Controller** (`controller/`): Central brain for executing job logic (planned)
- **Runner** (planned): Execution environments (local, Docker, K8s)

## Key Architecture Components

### Job System (`sdk/src/job.py`)
- **Job**: Main orchestration unit with upstream dependencies and validation
- Jobs execute on the controller, not remote nodes
- Supports dependency DAGs with cycle detection
- Status tracking: PENDING � RUNNING � SUCCESS/FAILED/SKIPPED

### Task System (`sdk/src/task.py`)
- **Task**: Atomic work units (currently ShellTask)
- Tasks run in sandboxes and are executed by jobs
- Uses job context to access sandbox executors

### Sandbox System (`sdk/src/sandbox/`)
- **BaseSandbox**: Abstract interface for execution environments
- **DockerSandbox**: Docker-based execution (in development)
- **SandboxManager**: Manages sandbox lifecycle (create, fork, destroy, snapshot)

## Development Commands

### Package Management
```bash
# Install dependencies (uses uv package manager)
uv sync

# Install SDK with test dependencies
cd sdk && uv sync --extra test
```

### Testing
```bash
# Run all tests
cd sdk && uv run pytest

# Run specific test file
cd sdk && uv run pytest test/test_job.py

# Run with coverage
cd sdk && uv run pytest --cov
```

### Running Examples
```bash
# Run main example
uv run python main.py
```

## Project Structure

```
river/
   sdk/                    # Core SDK components
      src/
         job.py         # Job orchestration logic
         task.py        # Task execution units
         sandbox/       # Sandbox execution abstractions
      test/              # Test suite
   controller/            # Job execution controller (planned)
   main.py               # Example usage
   pyproject.toml        # Root project configuration
```

## Important Development Notes

- Uses Python 3.12+ with uv package manager
- Jobs contain orchestration logic and run on controller
- Tasks are atomic units executed in sandboxes
- Architecture separates concerns: Controller = orchestration, Sandbox = execution
- Cycle detection prevents infinite dependency loops
- Context variables (`job_context`) provide access to current job state