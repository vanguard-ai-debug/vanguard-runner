# 🌐 多网站上下文管理指南

## 📋 概述

在一个工作流中同时操作多个不同的网站时，需要使用**浏览器上下文（BrowserContext）**进行隔离。每个上下文是完全独立的，拥有自己的：
- ✅ Cookie和Session
- ✅ LocalStorage和SessionStorage  
- ✅ HTTP请求头
- ✅ 页面缓存

## 🎯 核心概念

### Playwright架构

```
Browser (单个浏览器实例)
  ├── Context 1 (网站A - 完全隔离)
  │   ├── Page 1
  │   └── Page 2
  ├── Context 2 (网站B - 完全隔离)
  │   ├── Page 1
  │   └── Page 2
  └── Context 3 (网站C - 完全隔离)
      └── Page 1
```

**关键特性**：
- 一个Browser可以有多个Context
- 每个Context完全隔离（Cookie、Storage独立）
- 可以在Context之间自由切换
- 不同Context可以有不同的鉴权信息

## 🚀 使用方式

### 方式1: 自动创建上下文（推荐）⭐

系统会根据URL自动创建或选择上下文：

```json
{
  "id": "navigate_to_baidu",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://www.baidu.com",
      "auto_create_context": true  // 默认true，自动创建
      // 系统会自动创建context_id: "www_baidu_com"
    }
  }
}
```

### 方式2: 手动指定上下文ID

```json
{
  "id": "navigate_with_context",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://www.baidu.com",
      "context_id": "baidu_site",  // 自定义上下文ID
      "credential_id": "baidu_credential"
    }
  }
}
```

### 方式3: 手动创建上下文

```json
{
  "id": "create_baidu_context",
  "type": "browser_launch",
  "data": {
    "config": {
      "operation": "new_context",
      "context_id": "baidu_site",
      "context_config": {
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN"
      }
    }
  }
}
```

## 📖 完整示例

### 示例1: 同时操作百度和谷歌

```json
{
  "nodes": [
    {
      "id": "launch_browser",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "launch",
          "browser_type": "chromium",
          "headless": false
        }
      }
    },
    {
      "id": "navigate_baidu",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://www.baidu.com",
          "context_id": "baidu",
          "credential_id": "baidu_credential"
        }
      }
    },
    {
      "id": "baidu_search",
      "type": "ui_element",
      "data": {
        "config": {
          "operation": "input",
          "selector": "textbox",
          "selector_type": "role",
          "value": "人工智能"
        }
      }
    },
    {
      "id": "switch_to_google",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "switch_context",
          "context_id": "google"
        }
      }
    },
    {
      "id": "navigate_google",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://www.google.com",
          "context_id": "google",
          "credential_id": "google_credential"
        }
      }
    },
    {
      "id": "switch_back_baidu",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "switch_context",
          "context_id": "baidu"
        }
      }
    }
  ],
  "edges": [
    {"source": "launch_browser", "target": "navigate_baidu"},
    {"source": "navigate_baidu", "target": "baidu_search"},
    {"source": "baidu_search", "target": "switch_to_google"},
    {"source": "switch_to_google", "target": "navigate_google"},
    {"source": "navigate_google", "target": "switch_back_baidu"}
  ]
}
```

### 示例2: 三个平台切换（SEVC、Amazon、Google）

```json
{
  "nodes": [
    {
      "id": "launch",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "launch",
          "browser_type": "chromium"
        }
      }
    },
    {
      "id": "sevc_operation",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://sevc.tst.spotterio.com/dashboard",
          "context_id": "sevc",
          "credential_id": "sevc_credential"
        }
      }
    },
    {
      "id": "switch_to_amazon",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "switch_context",
          "context_id": "amazon"
        }
      }
    },
    {
      "id": "amazon_operation",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://advertising.amazon.com/campaigns",
          "context_id": "amazon",
          "credential_id": "amazon_credential"
        }
      }
    },
    {
      "id": "switch_to_google",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "switch_context",
          "context_id": "google"
        }
      }
    },
    {
      "id": "google_operation",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://ads.google.com/campaigns",
          "context_id": "google",
          "credential_id": "google_credential"
        }
      }
    },
    {
      "id": "switch_back_sevc",
      "type": "browser_launch",
      "data": {
        "config": {
          "operation": "switch_context",
          "context_id": "sevc"
        }
      }
    }
  ],
  "edges": [
    {"source": "launch", "target": "sevc_operation"},
    {"source": "sevc_operation", "target": "switch_to_amazon"},
    {"source": "switch_to_amazon", "target": "amazon_operation"},
    {"source": "amazon_operation", "target": "switch_to_google"},
    {"source": "switch_to_google", "target": "google_operation"},
    {"source": "google_operation", "target": "switch_back_sevc"}
  ]
}
```

## 🔧 BrowserProcessor操作

### 1. 创建新上下文

```json
{
  "id": "create_context",
  "type": "browser_launch",
  "data": {
    "config": {
      "operation": "new_context",
      "context_id": "custom_site",
      "context_config": {
        "viewport": {"width": 1920, "height": 1080},
        "locale": "zh-CN",
        "user_agent": "Custom Agent",
        "timezone_id": "Asia/Shanghai"
      }
    }
  }
}
```

### 2. 切换上下文

```json
{
  "id": "switch_context",
  "type": "browser_launch",
  "data": {
    "config": {
      "operation": "switch_context",
      "context_id": "baidu_com"
    }
  }
}
```

### 3. 关闭上下文

```json
{
  "id": "close_context",
  "type": "browser_launch",
  "data": {
    "config": {
      "operation": "close_context",
      "context_id": "baidu_com"
    }
  }
}
```

### 4. 列出所有上下文

```json
{
  "id": "list_contexts",
  "type": "browser_launch",
  "data": {
    "config": {
      "operation": "list_contexts"
    }
  }
}
```

**返回结果**：
```json
{
  "status": "success",
  "context_ids": ["default", "baidu_com", "google_com"],
  "count": 3,
  "current_context_id": "baidu_com"
}
```

## 💡 上下文ID规则

### 自动生成规则

如果不指定`context_id`，系统会根据URL自动生成：

```
URL: https://www.baidu.com
→ context_id: "www_baidu_com"

URL: https://sevc.tst.spotterio.com
→ context_id: "sevc_tst_spotterio_com"

URL: https://advertising.amazon.com
→ context_id: "advertising_amazon_com"
```

**规则**：
1. 提取域名（去掉协议和路径）
2. 去掉"www."前缀
3. 将"."替换为"_"
4. 转换为小写

### 自定义上下文ID

建议使用有意义的名称：

```json
{
  "context_id": "baidu"  // ✅ 简单明了
}
```

```json
{
  "context_id": "sevc_production"  // ✅ 包含环境信息
}
```

## 🎯 使用场景

### 场景1: 数据同步工作流

```
SEVC平台获取数据 
    ↓
切换到Amazon上下文
    ↓
Amazon平台上传数据
    ↓
切换回SEVC上下文
    ↓
验证数据同步结果
```

### 场景2: 多平台对比

```
同时打开3个平台
    ↓
逐个切换并截图
    ↓
对比分析结果
```

### 场景3: 跨平台数据迁移

```
源平台导出数据
    ↓
切换目标平台
    ↓
导入并验证
    ↓
切换回源平台确认
```

## ⚠️ 重要注意事项

### 1. 上下文隔离

不同上下文之间**完全隔离**：
- ✅ Cookie不会共享
- ✅ Session独立
- ✅ 鉴权信息独立
- ✅ 页面状态独立

### 2. 上下文切换

切换上下文会：
- ✅ 自动切换到该上下文的默认页面
- ✅ 保留该上下文的所有状态
- ✅ 不影响其他上下文

### 3. 资源管理

- 每个上下文会占用内存
- 建议及时关闭不需要的上下文
- 浏览器关闭时会自动清理所有上下文

### 4. 默认上下文

- `default`上下文始终存在
- 不能手动关闭默认上下文
- 如果未指定context_id，使用默认上下文

## 📊 最佳实践

### 1. 命名规范

```json
// ✅ 推荐：使用平台名称
"context_id": "baidu"
"context_id": "google"  
"context_id": "amazon"

// ✅ 推荐：包含环境信息
"context_id": "sevc_production"
"context_id": "sevc_staging"

// ❌ 不推荐：无意义名称
"context_id": "context1"
"context_id": "test123"
```

### 2. 上下文生命周期

```json
// 方式1: 自动管理（推荐）
{
  "operation": "navigate",
  "url": "https://example.com",
  "auto_create_context": true  // 自动创建和管理
}

// 方式2: 手动管理
{
  "operation": "new_context",
  "context_id": "example"
},
// ... 使用上下文 ...
{
  "operation": "close_context",
  "context_id": "example"
}
```

### 3. 鉴权信息隔离

每个上下文可以有独立的鉴权：

```json
{
  "context_id": "baidu",
  "credential_id": "baidu_credential"
}

{
  "context_id": "google",
  "credential_id": "google_credential"
}
```

## 🔍 调试技巧

### 查看当前上下文

```json
{
  "operation": "list_contexts"
}
```

### 验证上下文隔离

在不同上下文执行相同操作，验证结果是否独立：

```json
{
  "id": "check_baidu_cookie",
  "type": "ui_action",
  "data": {
    "config": {
      "operation": "get_cookie",
      "name": "session_id",
      "context_id": "baidu"
    }
  }
},
{
  "id": "check_google_cookie",
  "type": "ui_action",
  "data": {
    "config": {
      "operation": "get_cookie",
      "name": "session_id",
      "context_id": "google"
    }
  }
}
```

## 📚 相关文档

- [自动鉴权导航指南](./AUTO_AUTH_NAVIGATION_GUIDE.md)
- [Playwright API合规性](./PLAYWRIGHT_API_COMPLIANCE.md)
- [会话共享指南](../docs/SESSION_SHARING_GUIDE.md)

## 🎉 总结

多网站上下文管理提供了：

1. ✅ **完全隔离** - 每个网站独立的Cookie、Storage
2. ✅ **自动切换** - 根据URL自动创建/选择上下文
3. ✅ **灵活控制** - 支持手动创建、切换、关闭
4. ✅ **独立鉴权** - 每个上下文可以使用不同的凭证
5. ✅ **资源管理** - 自动清理，支持手动关闭

现在您可以：
- 🌐 同时操作多个网站
- 🔄 自由切换不同网站
- 🔐 为每个网站设置独立的鉴权
- ✅ 完全隔离，互不干扰

开始使用多网站上下文管理，让您的工作流更加强大！🚀

