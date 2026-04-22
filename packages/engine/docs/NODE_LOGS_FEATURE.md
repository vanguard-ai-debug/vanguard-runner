# 节点日志收集功能

## 功能说明

在工作流执行结束后，`execution_result = executor.execute()` 不仅能够获取每个step的结果，还能够获取到每个节点详细的打印日志。

每个节点的执行结果包含：
- `logs`: 日志列表（详细格式，包含时间戳、级别等信息）
- `message`: 所有日志拼接成的字符串，方便直接查看

## 使用方法

执行工作流后，可以通过 `execution_result.steps` 访问每个节点的执行结果。

### 示例代码 - 使用 message 字段（推荐）

```python
from packages.engine.workflow_engine import WorkflowExecutor

# 创建工作流执行器
executor = WorkflowExecutor(workflow_data)

# 执行工作流
execution_result = executor.execute()

# 遍历所有步骤，直接查看每个节点的日志message
for step in execution_result.steps:
    print(f"\n节点: {step.node_id} ({step.node_type})")
    print(f"状态: {step.status.value}")
    
    # 直接打印所有日志（已拼接好的字符串）
    if step.message:
        print("日志内容:")
        print(step.message)
```

### 示例代码 - 使用 logs 字段（详细格式）

```python
# 如果需要详细的日志信息，可以使用 logs 字段
for step in execution_result.steps:
    print(f"\n节点: {step.node_id} ({step.node_type})")
    print(f"状态: {step.status.value}")
    print(f"日志数量: {len(step.logs)}")
    
    # 遍历日志列表获取详细信息
    for log in step.logs:
        print(f"  [{log['timestamp']}] {log['level']}: {log['message']}")
```

### 日志格式

每个日志条目包含以下字段：

- `timestamp`: 日志时间戳（ISO格式）
- `level`: 日志级别（DEBUG, INFO, WARNING, ERROR等）
- `message`: 日志消息内容
- `module`: 日志来源模块
- `function`: 日志来源函数
- `line`: 日志来源行号
- `name`: 日志来源名称

### 获取特定节点的日志

```python
# 获取特定节点的执行结果
step = execution_result.get_step("node_id")

if step:
    # 方式1: 直接使用 message 字段（推荐，已拼接好的字符串）
    if step.message:
        print(step.message)
    
    # 方式2: 使用 logs 字段（获取详细信息）
    for log in step.logs:
        print(f"{log['timestamp']} - {log['level']}: {log['message']}")
```

### 在 ExecutionResult 的字典表示中

当调用 `execution_result.to_dict()` 时，每个步骤的 `logs` 和 `message` 字段都会被包含在内：

```python
result_dict = execution_result.to_dict()

# 访问第一个节点的日志message（推荐）
first_step_message = result_dict['steps'][0].get('message', '')

# 或者访问详细的日志列表
first_step_logs = result_dict['steps'][0].get('logs', [])
```

### message 字段格式

`message` 字段包含所有日志的拼接结果，格式如下：

```
[2025-01-13T10:30:45.123] INFO: 开始执行节点: node1
[2025-01-13T10:30:45.456] DEBUG: 节点输入: node1 - 2个前置结果
[2025-01-13T10:30:46.789] INFO: 节点输出: node1 - 执行成功
[2025-01-13T10:30:46.790] INFO: 节点执行完成: node1 (状态: SUCCESS) (耗时: 1.667s)
```

每行日志的格式为：`[时间戳] 级别: 消息内容`

## 实现细节

- 日志收集器会在每个节点执行开始时自动启动
- 日志收集器会在每个节点执行结束时自动停止
- 只收集节点执行期间产生的日志（基于时间戳过滤）
- 支持所有日志级别（DEBUG, INFO, WARNING, ERROR等）
- 线程安全，支持并发执行（虽然当前工作流引擎是顺序执行的）

## 注意事项

1. 日志收集会增加一定的性能开销，但对于大多数用例来说影响很小
2. 日志消息会包含完整的格式化信息（时间戳、级别等）
3. 如果节点执行失败，错误日志也会被收集
4. 跳过的节点不会有日志（因为它们没有执行）
