# 参与贡献 🎉

欢迎任何形式的贡献 —— 代码、文档、Bug 反馈、功能建议。

## 快速链接

- 📖 **项目文档**: [service.fastapiadmin.com](https://service.fastapiadmin.com/)
- 🐛 **反馈 Bug**: [GitHub Issues](https://github.com/fastapiadmin/FastapiAdmin/issues) | [Gitee Issues](https://gitee.com/fastapiadmin/FastapiAdmin/issues)
- 💡 **功能建议**: 先提 Issue 讨论，再动手写代码
- 📝 **开发规范**: [代码风格指南](https://service.fastapiadmin.com/guide/guidelines)
- 💬 **社区交流**: 扫码加入微信群（二维码见 [README](./README.md)）

## 开始之前

1. 先搜索现有 [Issues](https://github.com/fastapiadmin/FastapiAdmin/issues)，避免重复提交
2. 较大改动建议先开 Issue 讨论方案
3. 遵循 [提交信息规范](https://service.fastapiadmin.com/guide/guidelines)

## 本地开发环境

```bash
# 后端
cd backend && uv sync && uv run main.py run --env=dev

# 前端
cd frontend/web && pnpm install && pnpm run dev

# 小程序（uni-app，微信开发者工具导入 dist/dev/mp-weixin）
cd frontend/app && pnpm install && pnpm dev:mp-weixin

# 文档
cd frontend/docs && pnpm install && pnpm run dev
```

## Pull Request 流程

1. Fork 仓库，创建功能分支（`feature/xxx` 或 `bugfix/xxx`）
2. 完成修改，使用约定式提交信息
3. 运行检查：`ruff check`（后端）/ `pnpm lint`（前端）
4. 提交 PR 到 **`dev`** 分支
5. 等待审核 —— 我们会尽快回复

## 贡献者协议

提交贡献即表示你同意将代码以项目的 [MIT 协议](./LICENSE) 开源。

---

**每一点贡献都很重要 —— 从修复错别字到开发新功能。感谢！❤️**
