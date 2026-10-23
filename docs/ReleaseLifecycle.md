# Tongwen 发布与下载链路

本仓库只负责公开安装包分发，不构建产品，也不决定最低支持版本。

## 三仓库职责

| 仓库 | 职责 |
| --- | --- |
| [FsDiG/TongWen](https://github.com/FsDiG/TongWen) | 产品源码、contract、候选构建与验收、MSI、R2 原包镜像、内部保护符号 |
| [FeiSiPub/feisi-website](https://github.com/FeiSiPub/feisi-website) | 产品页、在线帮助、cn/global 静态托管与 stable 策略 |
| [FeiSiPub/TongWenReleases](https://github.com/FeiSiPub/TongWenReleases) | 同 Tag 公开 Release、用户 MSI 与 SHA256SUMS.txt |

源码 Release 默认生成受保护的内部候选。产品负责人明确授权 publish 后，流水线核对原
candidate 的 run ID、source commit、版本、大小、SHA256 和保护凭证，再原样发布该 MSI。
已验收的候选不重建、不重新保护；符号、PDB、Reactor 映射和凭据不进入公开资产。

同文 2 的源 Release 与公开镜像当前标题固定为 `同文 2 Preview vX.Y.Z`，与 Tag 一致；旧版标题保留。
当前/最新状态使用 GitHub
Latest/Pre-release 标记，功能主题与范围写入 Release Notes，不能放入会随时间失真的标题。
公开说明置顶 R2 主下载、GitHub 备用下载，并附 SHA256SUMS.txt 核对说明与源码 Release 回链；GitHub
自动生成的 Source code 压缩包是本分发仓库的快照，不是用户安装包。

同文 2 长期显示 Preview；实际使用稳定一段时间后，产品负责人另行决定正式定位。
Preview 不改变数字版本、Tag、MSI 名称或 GitHub 技术分类，也不能由自动化通过自动晋级。
经典版持续维护0.2.x系列，当前0.2.28；历史0.2.27目前另行保留原包供回退。维护线与main/2.0运行时分开。

## 当前双下载入口

| 版本 | 角色 | MSI 大小 | SHA256 |
| --- | --- | --- | --- |
| [v2.0.4](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v2.0.4) | 当前同文2.0 Preview | 163,717,440 bytes | `eb7d87798b89ef88259818f0b98236aedef57a5a3f462ec86fa6f5fea4a7a9c5` |
| [v0.2.28](https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.28) | 当前同文经典版，持续维护0.2.x | 24,171,184 bytes | `e0b843d1d986555ff4c7e09684a11a597eeb506fce87fa04f158bfaae13eae7c` |

产品页保留 Preview/经典版两张卡片，各提供 R2 主下载及 GitHub 备用，共四个链接、两份原包。
Preview与经典版各显式指定一个已公开的当前版本，不使用跨产品动态`/latest`选包。官网按钮
统一“下载 · v<完整版本号>”，版本下方展示实际公开Release的北京时间日期。历史版本统一从
可用的历史Releases访问；过期公开镜像遵循下方保留规则。当前为2.0.4与0.2.28，不再按通道新增第三个下载入口。
同文 2 会替换 Preview/旧版安装，不能同机并存、不会迁移旧
工作区。返回旧版前必须先卸载同文 2；Windows Installer 不支持直接降级覆盖。

2.0.1 的业务源码提交为 `d255854b425d133de1ad0ff726e2d2e9d08a4b6b`，内部 candidate run
[37763677968](https://github.com/FsDiG/TongWen/actions/runs/37763677968) 已完成编译、普通 .NET
测试、Reactor 保护与 MSI 审计。[publish run 37768676552](https://github.com/FsDiG/TongWen/actions/runs/37768676552)
按产品负责人本次明确授权公开了同一份 MSI。真实 AutoCAD GUI、Provider、安装升级/卸载
与其他年份宿主仍未验证；不将发布授权或静态审计写成这些项目通过。

2.0.2 候选 run [37802883739](https://github.com/FsDiG/TongWen/actions/runs/37802883739)
来源为 `d927aae21be07298902cb34a3ea5bcf2a9606765`；publish run
[37804156655](https://github.com/FsDiG/TongWen/actions/runs/37804156655) 原样公开该受保护 MSI。
完整 Release 0 errors/100 warnings，普通测试 866 通过、1 项 Sentry smoke 跳过；401 项 File
表、ProductName 同文 2 Preview、ProductVersion 2.0.2、同数值覆盖关闭与 runtime 门禁均已核对。
2.0.2、2.0.1、0.2.27 公网 MSI 已匿名下载并核对摘要；2.0.1 与旧版原资产未替换。

2.0.4的source commit为`597804d1b0d73a4a3d76748645fab362cb01d59b`，candidate run
[39945726070](https://github.com/FsDiG/TongWen/actions/runs/39945726070)通过本机NUC11编译、
普通测试1087通过/1跳过、Reactor保护与1253项MSI File表审计；ProductName为“同文 2 Preview”、
ProductVersion为2.0.4、同数值覆盖关闭。publish run
[39946467421](https://github.com/FsDiG/TongWen/actions/runs/39946467421)发布同一候选，未重新构建。
真实GUI、Undo、Provider、安装及其他年份宿主仍未验收。

2026-10-12 仅将现有 2.0.2 与 0.2.27 原包镜像到独立 `tongwen-releases` bucket，自定义域名为
`tongwen-download.278848.xyz`，直接提供对象，不增加 Worker。每版只上传 MSI 与 SHA256SUMS.txt，
对象路径为 `releases/vX.Y.Z/`；附件保留原文件名，版本缓存不可变，错误响应不缓存。
四个下载地址已匿名验证 HEAD、Range、附件名称、完整大小和上述 SHA256；两渠道校验文件逐字节一致。
没有重编译、重打包、重新构建旧版或替换 GitHub 资产；其他历史版本保持原状。

## stable 策略发布顺序

1. 源码仓库明确 publish 原 candidate，完成正式 stable Release。
2. 镜像相同 Tag、说明、唯一匹配 MSI 与 SHA256SUMS.txt 到本仓库。
3. 核对两边资产大小/摘要一致，并确认公开链接可下载、Release 非 Draft/Pre-release。
4. 上传原 MSI 和校验文件到 R2，验证公网 HEAD、Range、校验文件与完整 SHA256 后更新置顶下载说明。
5. 源码工作流按`sync_website_policy`选项通知官网（默认true）；官网再次比较 R2 大小和原始校验文件后递增 policy revision、更新 latest/download，原样
   保留 enforcement、minimum 与 grace 字段，并调用双站静态发布。
6. 部署后核对产品页、帮助和无参数公网 stable JSON。冷缓存探针不能代替最终公开地址验收。

仅已公开的数字 stable `vX.Y.Z` 自动镜像到 R2，内部候选和带后缀的 Beta 不纳入。
Preview 仍只表达成熟度；客户端当前 GitHub 下载白名单及 `stable.json` 的下载契约不变。

普通 stable 发布只提示更新，不自动下载、执行 MSI 或开启强制升级。当前策略为 revision 10、
latest 2.0.2、`enforcement_enabled=false`、minimum 0.0.0、grace 30 天；关闭时不启动宽限或停用。
未来开启 30 天普通宽限或 0 天紧急停用，必须取得产品负责人独立授权并提高 revision。
Beta、Draft、Pre-release 不推进 stable 策略。

2026-10-23的2.0.4发行明确关闭`sync_website_policy`：R2/GitHub原包核验后独立更新官网两个
下载卡片，客户端策略保持revision 10/latest 2.0.2。纯数字版本不改变Preview定位；旧后缀包
不改名重发。负责人授权编译与必要打包核验后直接发布，不等待PR CI或网页缓存自然过期。

## 历史基线

| 版本 | 当时的用途 | MSI SHA256 |
| --- | --- | --- |
| v0.2.22 | 首个策略客户端稳定基线 | `6b57352aab1f59f12c69eaaf863d5fdb151ed50f43a932d5b778d20695cc4dfb` |
| v0.2.23 | 首次升级与历史七天宽限验证 | `f62667e2c46e61ed5c0d514d0cc486f12a1e8a623000bcfd2c59cdcfb8e2f067` |
| v0.2.24 | 安装完成页产品链接修正 | `c773a9b178060cfad61479dc60038a014afca82ba62675455f0ebcfaf6e4b5c2` |

0.2.22/0.2.23 均由源码提交 `9a86100fa33314eb3941eb44b7960f3149c6930a` 构建，功能源码相同，
使用独立版本与 ProductCode 验证当时的升级关系；这些历史验证不代表同文 2 的安装验收。
以上为历史证据，不承诺对应公开镜像永久可下载；源码发行身份与摘要仍保留。

## 公开镜像保留与退休

维护入口为 [Release retention](https://github.com/FeiSiPub/TongWenReleases/actions/workflows/cleanup-releases.yml)，
详细契约见 [ReleaseRetention.md](ReleaseRetention.md)。默认两条线各保留至少 3 个正式版
（至少 30 天）、1 个预发布版（至少 14 天），并保护官网当前下载、线上策略指向版本、每条线
最新正式版、GitHub Latest 与手动保留项。一次最多清理 5 个 Release。

只有核对成功预览并在 24 小时内手动选择执行，才删除预览中的公开 Release、全部附件与本仓库
同名 Tag；孤立 Tag 只报告。它不修改源码仓库历史、R2、官网或升级策略，也不允许替换原包。
此处为正常保留策略下的退休操作，与下方发布故障恢复中“不删除重传、不删除包”的规则分开。
调整官网版本时需同步 `config/ReleaseRetention.json` 的保护集合；失败或保护源不可读时停止。

## 核对与维护

```powershell
Get-FileHash .\TongWen_Installer_v2.0.2.msi -Algorithm SHA256
```

- 每个镜像 Tag 恰好有一份对应版本 MSI 和一份 SHA256SUMS.txt。
- 标题、来源说明、stable/prerelease 状态、大小和 SHA256 与源 Release 一致；置顶下载区和
  唯一源码回链属于公开镜像的固定包装。
- 当前 MSI 没有 Authenticode 发布者签名；SHA256 只能确认下载完整性，不能替代发布者签名。
- 已有同 SHA256 的 GitHub/R2 对象复用，只补缺失文件；同名内容冲突立即停止，不删除重传。
- R2 失败保留 GitHub 下载，并阻止官网推进。修复后只运行源码仓库“恢复公开 R2 下载镜像”，
  输入已经发布的数字 Tag；不会构建或重建 Release，官网同步默认关闭，首次两个版本均保持关闭。
- R2 故障可把官网主按钮恢复为原 GitHub 地址；不删除安装包、不回退版本或更新策略。
- 镜像或网站通知失败时按同一 Tag 幂等重试，不虚构新版本。
- 回滚保留已经公开的资产；策略使用更高 revision 关闭 enforcement，并指向确认可用版本。
  若负责人另行决定回退推荐版本，先确认目标历史 Tag 的 R2 原包完整验证通过；缺失时使用
  恢复入口且保持 `sync_website=false`，或先把官网主按钮恢复为该版本 GitHub 下载。
  历史 Release 不代表已有 R2 镜像，自动官网同步仍拒绝旧版本回退。
  在线客户端刷新后解除限制；完全离线且已有到期缓存的客户端不会立即收到放宽策略。

相关入口：

- [源码发布运维](https://github.com/FsDiG/TongWen/blob/main/docs/guides/StableUpdateReleaseOperations.md)
- [普通更新与显式强制升级 ADR](https://github.com/FsDiG/TongWen/blob/main/docs/adr/0017-AdvisoryUpdatesAndExplicitEnforcement.md)
- [官网发布运维](https://github.com/FeiSiPub/feisi-website/blob/main/docs/tongwen-release-lifecycle.md)
- [公开 stable 策略](https://fscad.xyz/updates/tongwen/stable.json)
