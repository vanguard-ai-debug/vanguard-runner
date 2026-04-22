# 🚀 自动鉴权导航使用指南

## 概述

NavigationProcessor现在支持在页面导航时**自动注入鉴权信息**，无需在每个workflow中手动处理登录流程。支持多种鉴权方式，可以在导航前自动应用。

## 🎯 使用场景

- ✅ 已登录会话的页面访问
- ✅ 需要Token/API Key的API页面
- ✅ 需要Cookie认证的Web应用
- ✅ 需要localStorage/sessionStorage的SPA应用
- ✅ 多平台切换（不同凭证）

## 📋 支持的鉴权方式

### 1. 使用凭证ID（推荐）⭐

从凭证管理中心加载凭证并自动应用。

```json
{
  "id": "navigate_with_auth",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://example.com/dashboard",
      "credential_id": "example_credential"
    }
  }
}
```

**优势**：
- ✅ 集中管理凭证
- ✅ 自动生成HTTP鉴权头（Bearer Token、API Key等）
- ✅ 支持凭证中的Cookie、localStorage等
- ✅ 凭证可加密存储

### 2. 直接配置Cookie

直接在配置中指定Cookie列表。

```json
{
  "id": "navigate_with_cookies",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://example.com/profile",
      "cookies": [
        {
          "name": "session_id",
          "value": "${SESSION_TOKEN}",
          "domain": ".example.com",
          "path": "/",
          "httpOnly": true,
          "secure": true,
          "sameSite": "Lax"
        },
        {
          "name": "auth_token",
          "value": "${AUTH_TOKEN}",
          "domain": ".example.com"
        }
      ]
    }
  }
}
```

**Cookie属性**：
- `name`: Cookie名称（必需）
- `value`: Cookie值（必需，支持变量 `${VAR}`）
- `domain`: Cookie域（可选，会自动从URL提取）
- `path`: Cookie路径（可选，默认"/"）
- `httpOnly`: 是否仅HTTP访问（可选）
- `secure`: 是否仅HTTPS（可选）
- `sameSite`: SameSite策略（可选："Strict"/"Lax"/"None"）

### 3. 设置HTTP请求头

适用于API请求或需要特定Header的页面。

```json
{
  "id": "navigate_with_headers",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://api.example.com/data",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}",
        "X-API-Key": "${API_KEY}",
        "X-Request-ID": "${REQUEST_ID}",
        "User-Agent": "MyApp/1.0"
      }
    }
  }
}
```

**常用Header**：
- `Authorization`: Bearer Token认证
- `X-API-Key`: API密钥
- `X-Auth-Token`: 自定义Token
- `Cookie`: 也可以在这里设置（但推荐使用cookies配置）

### 4. 设置localStorage

适用于需要前端存储的SPA应用。

```json
{
  "id": "navigate_with_local_storage",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://app.example.com",
      "local_storage": {
        "user_token": "${USER_TOKEN}",
        "user_id": "${USER_ID}",
        "pref_lang": "zh-CN",
        "theme": "dark"
      }
    }
  }
}
```

### 5. 设置sessionStorage

临时会话存储，页面关闭后清除。

```json
{
  "id": "navigate_with_session_storage",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://app.example.com",
      "session_storage": {
        "session_data": "${SESSION_DATA}",
        "temp_token": "${TEMP_TOKEN}"
      }
    }
  }
}
```

## 🔥 组合使用

可以同时使用多种鉴权方式，按优先级应用：

1. **credential_id** - 最高优先级，会加载凭证的所有配置
2. **cookies** - 补充或覆盖凭证中的Cookie
3. **headers** - 补充或覆盖凭证中的Header
4. **local_storage** - 补充或覆盖凭证中的localStorage
5. **session_storage** - 补充或覆盖凭证中的sessionStorage

```json
{
  "id": "navigate_with_all_auth",
  "type": "ui_navigation",
  "data": {
    "config": {
      "operation": "navigate",
      "url": "https://secure.example.com/dashboard",
      "credential_id": "secure_credential",
      "cookies": [
        {
          "name": "additional_cookie",
          "value": "additional_value",
          "domain": ".example.com"
        }
      ],
      "headers": {
        "X-Custom-Header": "custom_value"
      },
      "local_storage": {
        "pref_lang": "zh-CN"
      }
    }
  }
}
```

## 📚 完整示例

### 示例1: 使用凭证ID访问需要认证的页面

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
      "id": "navigate_to_dashboard",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://ob.spotter.ink/dashboards",
          "credential_id": "spotter_credential"
        }
      }
    }
  ],
  "edges": [
    {"source": "launch_browser", "target": "navigate_to_dashboard"}
  ]
}
```

### 示例2: 使用Cookie访问需要会话的页面

```json
{
  "nodes": [
    {
      "id": "navigate_with_session",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://example.com/user/profile",
          "cookies": [
            {
              "name": "JSESSIONID",
              "value": "${SESSION_ID}",
              "domain": ".example.com",
              "path": "/",
              "httpOnly": true
            }
          ]
        }
      }
    }
  ]
}
```

### 示例3: 多平台切换

```json
{
  "nodes": [
    {
      "id": "navigate_sevc",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://sevc.tst.spotterio.com/dashboard",
          "credential_id": "sevc_credential"
        }
      }
    },
    {
      "id": "navigate_amazon",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://advertising.amazon.com/campaigns",
          "credential_id": "amazon_credential"
        }
      }
    },
    {
      "id": "navigate_google",
      "type": "ui_navigation",
      "data": {
        "config": {
          "operation": "navigate",
          "url": "https://ads.google.com/campaigns",
          "credential_id": "google_credential"
        }
      }
    }
  ],
  "edges": [
    {"source": "navigate_sevc", "target": "navigate_amazon"},
    {"source": "navigate_amazon", "target": "navigate_google"}
  ]
}
```

## 🔧 凭证管理

### 创建凭证

```python
from src.core.credential_store import add_bearer_credential

# 添加Bearer Token凭证
add_bearer_credential(
    credential_id="spotter_credential",
    name="Spotter平台凭证",
    token="${SPOTTER_TOKEN}",
    description="Spotter平台的Bearer Token",
    expires_in_days=30
)
```

### 凭证配置示例

```python
from src.core.credential_store import credential_store, AuthType

# 添加包含Cookie的凭证
credential_store.add_credential(
    credential_id="full_auth_credential",
    name="完整鉴权凭证",
    auth_type=AuthType.BEARER.value,
    config={
        "token": "${TOKEN}",
        "cookies": [
            {
                "name": "session_id",
                "value": "${SESSION_ID}",
                "domain": ".example.com"
            }
        ],
        "local_storage": {
            "user_token": "${USER_TOKEN}"
        }
    }
)
```

## 💡 最佳实践

### 1. 优先使用凭证ID

```json
// ✅ 推荐
{
  "credential_id": "my_credential"
}

// ❌ 不推荐（直接在配置中硬编码敏感信息）
{
  "cookies": [
    {"name": "token", "value": "hardcoded_token_here"}
  ]
}
```

### 2. 使用环境变量

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "${SESSION_ID}"  // ✅ 使用变量
    }
  ],
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}"  // ✅ 使用变量
  }
}
```

### 3. 自动提取Domain

如果不指定`domain`，系统会自动从URL中提取：

```json
{
  "url": "https://app.example.com/dashboard",
  "cookies": [
    {
      "name": "token",
      "value": "${TOKEN}"
      // domain会自动设置为 "app.example.com"
    }
  ]
}
```

### 4. 组合策略

- 基础认证用**credential_id**
- 临时参数用**cookies/headers**
- 前端状态用**local_storage/session_storage**

```json
{
  "credential_id": "base_credential",  // 基础认证
  "headers": {
    "X-Request-ID": "${REQUEST_ID}"  // 临时Header
  },
  "local_storage": {
    "ui_theme": "dark"  // UI偏好
  }
}
```

## ⚠️ 注意事项

1. **注入时机**：鉴权信息在导航**之前**注入，确保页面加载时已包含认证信息
2. **Cookie Domain**：如果不指定domain，会从URL自动提取，但建议明确指定
3. **变量渲染**：所有配置值支持变量 `${VAR}`，会在运行时渲染
4. **优先级**：如果同时使用`credential_id`和直接配置，直接配置会**补充或覆盖**凭证中的对应项
5. **错误处理**：如果注入失败，会记录警告但**继续执行导航**，确保workflow不会中断

## 🔍 调试技巧

### 查看注入的鉴权信息

导航节点的日志会显示注入的信息：

```
[NavigationProcessor] 已应用凭证: spotter_credential
[NavigationProcessor] 已注入 2 个Cookie
[NavigationProcessor] 已注入请求头: ['Authorization', 'X-API-Key']
[NavigationProcessor] 已注入 3 个localStorage项
```

### 验证鉴权是否生效

```json
{
  "id": "verify_auth",
  "type": "ui_element",
  "data": {
    "config": {
      "operation": "get_text",
      "selector": ".user-name"
    }
  }
}
```

如果能获取到用户信息，说明鉴权成功。

## 📖 相关文档

- [凭证管理指南](../docs/CREDENTIAL_BASED_AUTH_GUIDE.md)
- [UI鉴权指南](../docs/UI_AUTHENTICATION_GUIDE.md)
- [凭证CLI工具](../src/tools/credential_manager.py)

## 🎉 总结

现在您可以在每个导航节点中直接配置鉴权信息，无需额外的手动登录步骤：

```json
{
  "operation": "navigate",
  "url": "https://secure.example.com/dashboard",
  "credential_id": "my_credential"  // 一行配置，自动认证！
}
```

简单、安全、高效！🚀

