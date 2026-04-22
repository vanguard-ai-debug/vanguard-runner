# XXL-Job 批量执行请求格式说明

## ⚠️ 重要提示

批量执行接口 `/workflow/execute/batch` 需要特定的请求格式，**不能直接发送工作流定义**。

## ❌ 错误的请求格式

如果您直接发送工作流定义，会收到 `422 Unprocessable Entity` 错误：

```json
{
  "name": "XXL-Job 任务触发工作流示例",
  "nodes": [...],
  "edges": [],
  "variables": {...}
}
```

## ✅ 正确的请求格式

批量执行接口需要以下格式：

```json
{
  "workflows": [
    {
      "workflow": {
        "name": "XXL-Job 任务触发工作流示例",
        "nodes": [...],
        "edges": []
      },
      "variables": {
        "xxljob_url": "...",
        "username": "..."
      },
      "runId": "test_run_001"
    }
  ],
  "priority": "normal",
  "maxBatchSize": 1000
}
```

## 📋 完整示例

### 单节点 XXL-Job 批量执行请求

```json
{
  "workflows": [
    {
      "workflow": {
        "name": "XXL-Job 任务触发工作流示例",
        "description": "演示如何使用 XXL-Job 处理器触发任务执行",
        "version": "1.0.0",
        "work_id": "xxljob_workflow_example",
        "work_name": "XXL-Job 任务触发示例",
        "nodes": [
          {
            "id": "trigger_xxljob",
            "type": "xxljob",
            "name": "触发XXL-Job任务",
            "data": {
              "config": {
                "xxjob_url": "https://developer.dev.spotterio.com/xxl-job",
                "username": "demo.wang@spotterio.com",
                "password": "MTExMTEx",
                "executor_handler": "autoCreateOutboundOrderPo",
                "executor_param": "",
                "site_tenant": "DEFAULT",
                "db_name": "xxl_job",
                "output_variable": "job_result"
              }
            },
            "position": {
              "x": 100,
              "y": 100
            }
          }
        ],
        "edges": []
      },
      "variables": {
        "xxljob_url": "https://developer.dev.spotterio.com/xxl-job",
        "username": "demo.wang@spotterio.com",
        "password": "MTExMTEx",
        "handler_name": "autoCreateOutboundOrderPo",
        "tenant": "DEFAULT",
        "xxl_job": {
          "host": "mysql.tst.spotter.ink",
          "port": 31070,
          "user": "root",
          "password": "root",
          "database": "xxl_job"
        }
      },
      "runId": "test_run_001"
    }
  ],
  "priority": "normal",
  "maxBatchSize": 1000
}
```

## 🔑 关键字段说明

### 顶层字段

- **workflows** (必需) - 工作流数组，每个元素包含：
  - **workflow** (必需) - 工作流定义（必须包含 `nodes` 和 `edges`）
  - **variables** (可选) - 初始变量
  - **runId** (可选) - 运行ID，用于追踪
- **priority** (可选) - 优先级：`urgent` / `high` / `normal`，默认 `normal`
- **maxBatchSize** (可选) - 单次批量处理的最大数量，默认 1000

### workflow 字段要求

工作流定义必须包含：
- **nodes** (必需) - 节点数组
- **edges** (必需) - 边数组（即使为空数组 `[]`）

## 🚀 使用 curl 测试

```bash
curl -X POST "http://localhost:8000/workflow/execute/batch" \
  -H "Content-Type: application/json" \
  -d @xxljob_batch_request_example.json
```

## 🐍 使用 Python 测试

```python
import json
import requests

# 加载工作流定义
with open('xxljob_single_node_batch_test.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# 创建批量请求（注意：工作流需要包装在 workflow 字段中）
batch_request = {
    "workflows": [
        {
            "workflow": workflow,  # 工作流定义放在这里
            "variables": workflow.get("variables", {}),
            "runId": "test_run_001"
        }
    ],
    "priority": "normal",
    "maxBatchSize": 1000
}

# 发送请求
response = requests.post(
    "http://localhost:8000/workflow/execute/batch",
    json=batch_request,
    headers={"Content-Type": "application/json"}
)

print(response.json())
```

## 📝 常见错误

### 错误 1: 422 Unprocessable Entity

**原因**: 直接发送工作流定义，缺少外层包装

**解决**: 将工作流定义包装在 `workflows[0].workflow` 中

### 错误 2: 工作流数据必须包含 nodes 和 edges 字段

**原因**: 工作流定义缺少 `nodes` 或 `edges` 字段

**解决**: 确保工作流定义包含这两个字段（`edges` 可以为空数组）

### 错误 3: 工作流列表不能为空

**原因**: `workflows` 数组为空

**解决**: 确保 `workflows` 数组至少包含一个元素

## 📚 参考文件

- `xxljob_batch_request_example.json` - 正确的批量请求格式示例
- `xxljob_single_node_batch_test.json` - 工作流定义（需要包装后使用）
- `run_xxljob_batch_test.py` - Python 测试脚本

