<div align="center">

  <h1>同文 2 Preview (Tongwen)</h1>
  <p><b>AutoCAD 图纸翻译、人工审校与受控写回</b></p>

  <p>
    <img src="https://img.shields.io/badge/Platform-Windows-blue.svg?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/CAD-AutoCAD%202019–2026-brightgreen.svg?style=flat-square" alt="AutoCAD 2019–2026">
  </p>
</div>

---

同文 2 Preview 在 AutoCAD 中提取 DBText/MText，使用 CSV 术语约束翻译，逐项人工审校，并在图纸内
预览版面。明确采用后，译文写入独立图层，源对象保持不变。本仓库只分发用户安装包；
产品源码和发布证据由 [Tongwen 源码仓库](https://github.com/FsDiG/TongWen) 维护。

> **核心理念**：车同轨，书同文。

同文 2 长期保持 Preview，继续积累真实使用反馈。数字版本、GitHub Latest 和技术 stable 通道
只用于发布索引，不代表完整业务已经充分验证；正式定位将由产品负责人另行决定。

## 下载与安装

| 入口 | 适用情况 | 版本说明与校验文件 |
| --- | --- | --- |
| [下载 Preview · v2.0.2 MSI](https://github.com/FeiSiPub/TongWenReleases/releases/download/v2.0.2/TongWen_Installer_v2.0.2.msi) | 用图纸副本体验新的 AutoCAD 工作流程 | [v2.0.2 Release](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v2.0.2) |
| [下载经典版 · v0.2.27 MSI](https://github.com/FeiSiPub/TongWenReleases/releases/download/v0.2.27/TongWen_Installer_v0.2.27.msi) | 需要继续既有 1.x 工作流程 | [v0.2.27 Release](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.27) |

同文 2 会替换已安装的 Preview 或旧版，不能同机并存；旧工作区不迁移，请先备份图纸和数据。
如需返回旧版，先卸载同文 2，再安装 0.2.27，不能直接降级覆盖；旧版不读取同文 2 工作区。
经典版 0.2.27 保留原始安装包，不再构建或发布旧版 MSI。已发布 2.0.1 的 Tag、包和哈希不变。
历史 Preview 和其他版本继续保留在 [全部 Releases](https://github.com/FeiSiPub/TongWenReleases/releases)。

1. 下载所选版本的 MSI 和同一 Release 中的 `SHA256SUMS.txt`，核对文件摘要。
2. 同文 2 要求 Windows x64、AutoCAD 2019–2026 和 x64 .NET 8 Desktop Runtime；缺少运行时时，
   MSI 会阻止新装或升级。旧版的运行要求以其 Release 为准。
3. 安装后使用 Studio 配置 Provider、启动 AutoCAD，再执行 `TW_WORKSPACE` 或 `TW_WORKSPACE_ALL`。

安装包当前没有 Authenticode 发布者签名，Windows 可能显示“未知发布者”。请从本仓库的
Release 下载，并使用同一 Release 内的 `SHA256SUMS.txt` 核对文件完整性。

## 当前能力与验证范围

- 唯一业务工作区由 AutoCAD 插件拥有；Studio 提供启动器和 Provider 设置。
- 支持 CSV 术语快照、同一翻译请求内的精确重复复用、候选选择、人工修改、审校与 JSON/CSV 报告。
- 支持 DBText/MText 的原生版面预览、明确采用与独立译文图层写回。
- 2019–2024 使用 net48，2025–2026 使用 net8；三个 SDK 的 Release 编译成功是当前支持判定依据。
- Revit/SolidWorks、AttributeReference/Dimension、替换原文/双语追加、模糊 TM 和 Studio 完整工作区
  不属于当前 Preview 范围。

2.0.1 曾完成完整 Release 编译、普通 .NET 测试（866 通过、1 项真实 Sentry smoke 跳过）、
AutoCAD 2026 Core Console 无 UI 检查和 MSI 静态审计。产品负责人明确授权发布；真实
AutoCAD GUI、Provider、安装升级/卸载及其他年份宿主仍未验证，编译和无 UI 检查不代表这些项目通过。

2.0.2 统一软件和安装器的 Preview 标识，保留数字 Tag 与文件名。完整 Release、普通 .NET
测试（866 通过、1 项 Sentry smoke 跳过）、Reactor 与 401 项 File 表审计通过；真实 GUI、
Provider、安装升级和各年份宿主没有因文案修改重做。发布为同一份封存候选，建议先用图纸副本体验。

## 文档与支持

- [产品页与两个下载入口](https://fscad.xyz/products/dwg-translator/)
- [当前在线帮助](https://fscad.xyz/products/dwg-translator/docs/getting-started/)
- 安装目录中的 `USER_GUIDE.html`：离线帮助，与该安装包的版本一起保存。
- [最后一个 1.x 版本的源码与历史说明](https://github.com/FsDiG/TongWen/tree/v1)：仅供旧版工作流程参考。

如果您在使用过程中遇到任何 Bug，或有新的功能建议，欢迎在 [Issues](https://github.com/FeiSiPub/TongWenReleases/issues) 页面提交反馈。

## 🔗 发布链路

本仓库只负责公开安装包分发。源码、官网更新策略和公开下载分别由三个仓库维护；版本镜像、
策略发布顺序、首组正式安装包摘要和回滚边界见
[Release Lifecycle](docs/ReleaseLifecycle.md)。Tongwen 客户端读取的公开 stable 策略为
[https://fscad.xyz/updates/tongwen/stable.json](https://fscad.xyz/updates/tongwen/stable.json)。

## 💬 社区与交流

加入我们的官方用户交流群，获取第一手更新资讯，或与其他开发者/工程师交流使用心得：

<div align="center">
  <img src="assets/qq_group_qr.png" alt="QQ Group QR Code" width="250">
  <br>
  <b>同文 (Tongwen) 翻译软件官方 QQ 群</b>: <code>1035193929</code>
</div>
