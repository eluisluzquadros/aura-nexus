# Claude Flow Coordination Demo

## Overview
This demonstrates how Claude Flow MCP tools coordinate with Claude Code to create intelligent workflows.

## Key Concepts

### 1. MCP Tools Coordinate, Claude Code Executes
- **MCP Tools**: Planning, memory, and coordination
- **Claude Code**: All actual implementation and file operations

### 2. Swarm Coordination Pattern
```bash
# Step 1: Initialize swarm (MCP coordination)
mcp__claude-flow__swarm_init --topology mesh --maxAgents 5

# Step 2: Spawn specialized agents (MCP planning)
mcp__claude-flow__agent_spawn --type researcher
mcp__claude-flow__agent_spawn --type coder
mcp__claude-flow__agent_spawn --type tester

# Step 3: Orchestrate tasks (MCP workflow)
mcp__claude-flow__task_orchestrate --task "Build feature" --strategy parallel

# Step 4: Claude Code executes using Task tool
Task("Research best practices", "full instructions", "researcher")
Task("Implement feature", "full instructions", "coder")
Task("Create tests", "full instructions", "tester")
```

### 3. Memory Persistence
```bash
# Store decisions and context
mcp__claude-flow__memory_usage --action store --key "project/decisions"

# Retrieve in future sessions
mcp__claude-flow__memory_usage --action retrieve --key "project/decisions"
```

## Example: Building a REST API

### Coordination Phase (MCP)
1. Initialize swarm with hierarchical topology
2. Spawn specialized agents (architect, backend-dev, tester)
3. Store architectural decisions in memory
4. Orchestrate parallel task execution

### Execution Phase (Claude Code)
1. Use Task tool to deploy agents with coordination hooks
2. Use TodoWrite to track all tasks in parallel
3. Use Read/Write/Edit for actual file operations
4. Use Bash for running commands

## Best Practices

1. **Always Batch Operations**: Use multiple tool calls in single messages
2. **Parallel Execution**: Never wait for one task before starting another
3. **Memory Coordination**: Store all decisions for cross-agent communication
4. **Hook Integration**: Every agent must use coordination hooks

## Performance Benefits
- 84.8% SWE-Bench solve rate
- 32.3% token reduction
- 2.8-4.4x speed improvement
- 27+ neural models for diverse approaches