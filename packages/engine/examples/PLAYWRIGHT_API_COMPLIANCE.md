# Playwright API 合规性说明

## ✅ 已按官方API实现

### 1. BrowserContext.add_cookies

按照 [Playwright官方文档](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-add-cookies) 实现：

**API要求**：
- ✅ Cookie必须包含：`name`, `value`, `domain`, `path`
- ✅ 可选字段：`expires`, `httpOnly`, `secure`, `sameSite`

**实现方式**：
```python
# 在浏览器上下文上调用（不是页面上）
page.context.add_cookies([
    {
        'name': 'session_id',
        'value': 'token_value',
        'domain': '.example.com',
        'path': '/',
        'httpOnly': True,
        'secure': True,
        'sameSite': 'Lax'
    }
])
```

**我们的实现**：
- ✅ 验证必需字段（name, value, domain, path）
- ✅ 自动从URL提取domain（如果未指定）
- ✅ 自动设置默认path为"/"
- ✅ 支持所有可选字段
- ✅ 在BrowserContext上调用，不是Page

### 2. BrowserContext.add_init_script

按照 [Playwright官方文档](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-add-init-script) 实现：

**API说明**：
- 在每个页面加载前执行JavaScript脚本
- 适用于设置localStorage、sessionStorage等

**实现方式**：
```python
# 在浏览器上下文上调用
page.context.add_init_script("""
    localStorage.setItem('key', 'value');
    sessionStorage.setItem('key', 'value');
""")
```

**我们的实现**：
- ✅ 使用`add_init_script`而不是`page.evaluate`
- ✅ 在页面加载前执行（确保页面初始化时就有数据）
- ✅ 使用JSON序列化确保安全性
- ✅ 在BrowserContext上调用

## 📋 Cookie格式规范

### 完整示例

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "${SESSION_TOKEN}",
      "domain": ".example.com",
      "path": "/",
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax",
      "expires": 1735689600
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| `name` | string | ✅ | Cookie名称 | - |
| `value` | string | ✅ | Cookie值 | - |
| `domain` | string | ✅ | Cookie域名 | 从URL自动提取 |
| `path` | string | ✅ | Cookie路径 | "/" |
| `httpOnly` | boolean | ❌ | 仅HTTP访问 | false |
| `secure` | boolean | ❌ | 仅HTTPS | false |
| `sameSite` | string | ❌ | SameSite策略 | - |
| `expires` | number | ❌ | 过期时间戳 | - |

## 🔧 使用示例

### 示例1: 最小配置（自动补全）

```json
{
  "operation": "navigate",
  "url": "https://example.com/dashboard",
  "cookies": [
    {
      "name": "token",
      "value": "${AUTH_TOKEN}"
      // domain和path会自动设置
    }
  ]
}
```

### 示例2: 完整配置

```json
{
  "operation": "navigate",
  "url": "https://secure.example.com/app",
  "cookies": [
    {
      "name": "session_id",
      "value": "${SESSION_ID}",
      "domain": ".example.com",
      "path": "/",
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    },
    {
      "name": "csrf_token",
      "value": "${CSRF_TOKEN}",
      "domain": ".example.com",
      "path": "/",
      "secure": true
    }
  ]
}
```

## 🎯 与Playwright API的对应关系

### 我们的配置 → Playwright API

```python
# 配置
cookies = [
    {
        "name": "token",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/"
    }
]

# 转换为Playwright API调用
await context.add_cookies([
    {
        "name": "token",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/"
    }
])
```

## ✅ 合规检查清单

- [x] 使用 `BrowserContext.add_cookies()` 而不是 `Page.add_cookies()`
- [x] Cookie包含必需字段：name, value, domain, path
- [x] 使用 `BrowserContext.add_init_script()` 设置storage
- [x] 自动验证必需字段
- [x] 自动补全默认值（path="/"）
- [x] 支持所有可选字段
- [x] 正确处理变量渲染
- [x] 错误处理和日志记录

## 📚 参考文档

- [Playwright Cookie API](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-add-cookies)
- [Playwright Init Script API](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-add-init-script)
- [Playwright Storage State API](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-storage-state)

## 🎉 总结

实现完全符合Playwright官方API规范：

1. ✅ 使用正确的API方法（BrowserContext级别）
2. ✅ 符合字段要求（必需+可选）
3. ✅ 自动补全缺失字段
4. ✅ 使用官方推荐的init_script方式设置storage
5. ✅ 完整的错误处理和验证

现在可以放心使用，完全兼容Playwright标准！🚀

