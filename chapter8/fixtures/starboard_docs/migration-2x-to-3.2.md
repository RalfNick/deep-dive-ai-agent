# 从 2.x 升级到 3.2

## 升级前检查

导出成员清单，并确认当前套餐与身份提供方。

## SSO 迁移

Team 版不能在 3.2 保留旧式 SAML SSO。请选择 OIDC，或先升级到 Enterprise。

## 成员处理

升级不会删除成员。超过套餐人数时，已有成员仍保留，但新的邀请会被阻止。

## 执行示例

```text
starboard migrate --target 3.2 --dry-run
```
