<div align="center">

  <h1>同文 (Tongwen CAD Suite)</h1>
  <p><b>面向工程领域的无损 CAD/BIM 图纸翻译套件</b></p>

  <p>
    <img src="https://img.shields.io/badge/Platform-Windows-blue.svg?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/CAD-AutoCAD%20%7C%20Revit-brightgreen.svg?style=flat-square" alt="CAD Support">
  </p>
</div>

---

同文 (Tongwen) 是一个专为工程领域设计的无损 CAD/BIM 图纸翻译工具。通过先进的提取与回写技术，同文能够在跨语言翻译的同时，完美保留原生图纸的各项核心属性。

> **核心理念**：车同轨，书同文。

<div align="center">
  <img src="assets/mockup_splash.png" alt="TongWen Software Showcase" width="80%">
</div>

## 🌟 核心特性

- **无损回写**：在翻译过程中，完全保留原生图层、坐标、字体、块属性、尺寸标注和 BIM 参数等。
- **术语约束**：支持行业术语库 (Glossary) 和翻译记忆库 (Translation Memory)，确保专业词汇翻译的一致性和准确性。
- **跨平台支持**：支持主流的 CAD/BIM 软件，如 AutoCAD、Revit、SolidWorks 等（需配合相应的插件使用）。
- **人工干预闭环**：提供从文本提取、术语约束翻译、人工校对、质量检查到精准回写的完整工作流。

## 🚀 快速开始

本项目仅作为 `Tongwen CAD Suite` 的公开发布仓库。如果您是最终用户，请直接前往 **[Releases](https://github.com/FeiSiPub/TongWenReleases/releases)** 页面下载最新版本的安装包。

### 下载与安装流程：

1. 访问 [Releases 页面](https://github.com/FeiSiPub/TongWenReleases/releases)。
2. 下载最新正式版本的 `TongWen_Installer_vX.Y.Z.msi` 和同一 Release 中的 `SHA256SUMS.txt`。
3. 按照安装向导完成安装，确保您的电脑上已安装支持的 CAD/BIM 宿主软件。
4. 启动同文工作台，或在 CAD 软件中加载同文插件。

当前推荐正式版为 [v0.2.24](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.24)。
`v0.2.22` 是首个包含稳定版策略客户端的基线安装包，主要用于验证升级和七天宽限链路；
普通用户应优先安装当前正式版。

安装包当前没有 Authenticode 发布者签名，Windows 可能显示“未知发布者”。请从本仓库的
Release 下载，并使用同一 Release 内的 `SHA256SUMS.txt` 核对文件完整性。

## 📚 文档与支持

关于如何配置术语库、进行翻译和回写操作，请参考我们在安装包中附带的用户指南（`USER_GUIDE.md` / `USER_GUIDE.html`）。

- **术语库使用指南**：了解如何管理术语库、翻译记忆，以及进行人工修正。
- **交互流程说明**：了解 Headless 批处理模式和 GUI 交互模式的操作差异。

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
