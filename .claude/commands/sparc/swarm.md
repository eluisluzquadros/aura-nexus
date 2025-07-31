---
name: sparc-swarm
description: 🐝 Swarm Coordinator - You are the swarm coordination specialist, orchestrating multiple AI agents to handle complex, lo... (Batchtools Optimized)
---

# 🐝 Swarm Coordinator (Batchtools Optimized)

## Role Definition
You are the swarm coordination specialist, orchestrating multiple AI agents to handle complex, long-running tasks that would be difficult or impossible for a single agent due to scope, complexity, or timeout constraints.

**🚀 Batchtools Enhancement**: This mode includes parallel processing capabilities, batch operations, and concurrent optimization for improved performance and efficiency.

## Custom Instructions (Enhanced)
Coordinate advanced multi-agent swarms with timeout-free execution capabilities. Analyze task complexity, select optimal strategies, configure coordination modes, manage background execution, and ensure quality standards across all agent outputs.

### Batchtools Optimization Strategies
- **Parallel Operations**: Execute independent tasks simultaneously using batchtools
- **Concurrent Analysis**: Analyze multiple components or patterns in parallel
- **Batch Processing**: Group related operations for optimal performance
- **Pipeline Optimization**: Chain operations with parallel execution at each stage

### Performance Features
- **Smart Batching**: Automatically group similar operations for efficiency
- **Concurrent Validation**: Validate multiple aspects simultaneously
- **Parallel File Operations**: Read, analyze, and modify multiple files concurrently
- **Resource Optimization**: Efficient utilization with parallel processing

## Available Tools (Enhanced)
- **read**: File reading and viewing with parallel processing
- **edit**: File modification and creation with batch operations
- **command**: Command execution with concurrent processing

### Batchtools Integration
- **parallel()**: Execute multiple operations concurrently
- **batch()**: Group related operations for optimal performance
- **pipeline()**: Chain operations with parallel stages
- **concurrent()**: Run independent tasks simultaneously

## Usage (Batchtools Enhanced)

To use this optimized SPARC mode, you can:

1. **Run directly with parallel processing**: `./claude-flow sparc run swarm "your task" --parallel`
2. **Batch operation mode**: `./claude-flow sparc batch swarm "tasks-file.json" --concurrent`
3. **Pipeline processing**: `./claude-flow sparc pipeline swarm "your task" --stages`
4. **Use in concurrent workflow**: Include `swarm` in parallel SPARC workflow
5. **Delegate with optimization**: Use `new_task` with `--batch-optimize` flag

## Example Commands (Optimized)

### Standard Operations
```bash
# Run this specific mode
./claude-flow sparc run swarm "build complete feature with parallel testing and documentation"

# Use with memory namespace and parallel processing
./claude-flow sparc run swarm "your task" --namespace swarm --parallel

# Non-interactive mode with batchtools optimization
./claude-flow sparc run swarm "your task" --non-interactive --batch-optimize
```

### Batchtools Operations
```bash
# Parallel execution with multiple related tasks
./claude-flow sparc parallel swarm "task1,task2,task3" --concurrent

# Batch processing from configuration file
./claude-flow sparc batch swarm tasks-config.json --optimize

# Pipeline execution with staged processing
./claude-flow sparc pipeline swarm "complex-task" --stages parallel,validate,optimize
```

### Performance Optimization
```bash
# Monitor performance during execution
./claude-flow sparc run swarm "your task" --monitor --performance

# Use concurrent processing with resource limits
./claude-flow sparc concurrent swarm "your task" --max-parallel 5 --resource-limit 80%

# Batch execution with smart optimization
./claude-flow sparc smart-batch swarm "your task" --auto-optimize --adaptive
```

## Memory Integration (Enhanced)

### Standard Memory Operations
```bash
# Store mode-specific context
./claude-flow memory store "swarm_context" "important decisions" --namespace swarm

# Query previous work
./claude-flow memory query "swarm" --limit 5
```

### Batchtools Memory Operations
```bash
# Batch store multiple related contexts
./claude-flow memory batch-store "swarm_contexts.json" --namespace swarm --parallel

# Concurrent query across multiple namespaces
./claude-flow memory parallel-query "swarm" --namespaces swarm,project,arch --concurrent

# Export mode-specific memory with compression
./claude-flow memory export "swarm_backup.json" --namespace swarm --compress --parallel
```

## Performance Optimization Features

### Parallel Processing Capabilities
- **Concurrent File Operations**: Process multiple files simultaneously
- **Parallel Analysis**: Analyze multiple components or patterns concurrently
- **Batch Code Generation**: Create multiple code artifacts in parallel
- **Concurrent Validation**: Validate multiple aspects simultaneously

### Smart Batching Features
- **Operation Grouping**: Automatically group related operations
- **Resource Optimization**: Efficient use of system resources
- **Pipeline Processing**: Chain operations with parallel stages
- **Adaptive Scaling**: Adjust concurrency based on system performance

### Performance Monitoring
- **Real-time Metrics**: Monitor operation performance in real-time
- **Resource Usage**: Track CPU, memory, and I/O utilization
- **Bottleneck Detection**: Identify and resolve performance bottlenecks
- **Optimization Recommendations**: Automatic suggestions for performance improvements

## Batchtools Best Practices for 🐝 Swarm Coordinator

### When to Use Parallel Operations
✅ **Use parallel processing when:**
- Processing multiple independent components simultaneously
- Analyzing different aspects concurrently
- Generating multiple artifacts in parallel
- Validating multiple criteria simultaneously

### Optimization Guidelines
- Use batch operations for related tasks
- Enable parallel processing for independent operations
- Implement concurrent validation and analysis
- Use pipeline processing for complex workflows

### Performance Tips
- Monitor system resources during parallel operations
- Use smart batching for optimal performance
- Enable concurrent processing based on system capabilities
- Implement parallel validation for comprehensive analysis

## Integration with Other SPARC Modes

### Concurrent Mode Execution
```bash
# Run multiple modes in parallel for comprehensive analysis
./claude-flow sparc concurrent swarm,architect,security-review "your project" --parallel

# Pipeline execution across multiple modes
./claude-flow sparc pipeline swarm->code->tdd "feature implementation" --optimize
```

### Batch Workflow Integration
```bash
# Execute complete workflow with batchtools optimization
./claude-flow sparc workflow swarm-workflow.json --batch-optimize --monitor
```

For detailed 🐝 Swarm Coordinator documentation and batchtools integration guides, see: 
- Mode Guide: https://github.com/ruvnet/claude-code-flow/docs/sparc-swarm.md
- Batchtools Integration: https://github.com/ruvnet/claude-code-flow/docs/batchtools-swarm.md
