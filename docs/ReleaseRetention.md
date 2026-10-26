# 公开发行保留与清理

## 范围与状态

`Release retention` 工作流只维护 `FeiSiPub/TongWenReleases`：删除符合条件的 Release
（同时删除它的全部附件），然后删除本仓库同名 Tag。它不修改 `FsDiG/TongWen` 的源码、Tag
或发布证据，不修改 R2、官网和线上升级策略，不使已安装的软件停用。

首版提供手动预览和手动执行，没有定时删除。脚本与配置经过检查后可生成实际库存预览；
真实删除属于独立操作，必须由维护者核对具体预览后主动选择 `execute`。
历史原包保持不可替换：保留期间不改名、不覆盖；退休公开镜像属于本流程的明确例外，
不授权改写源码发行证据。部分旧版没有 R2 镜像，清理前应自行确认是否仍需离线存档。

## 默认规则

| 分类 | 至少保留数量 | 最短保留时间 |
| --- | ---: | ---: |
| 经典版 `v0.2.x` 正式版 | 3 | 30 天 |
| 同文 2 `v2.x.x` 正式版 | 3 | 30 天 |
| 每条产品线的预发布版 | 1 | 14 天 |

删除条件同时满足：**超出保留数量、已超过最短保留时间、不受保护、身份与资产完整**。
按数值版本号保留较新版本；按 `published_at` 计算年龄，不能使用镜像的 `created_at`
或 Tag 指向提交的时间。达到指定天数即满足年龄条件。数量不足时全部保留。
仅完整可分类的公开 Release 计入数量，无法识别或资产不完整的版本不挤占保留名额。

分类依据 GitHub `prerelease`，不是产品标题。“同文2.0 Preview”的纯数字正式发行仍按
正式版保留。`v0.2.21` 虽无后缀，实际 `prerelease=true`，属于经典版预发布。
接受 `v0.2.x`、`v2.x.x` 和这两类的 `-preview.N` 后缀；带后缀却标记正式的异常项跳过。
Draft、未知格式、重复 Tag 的 Release、缺少发布时间、缺 Tag、不可变 Release、资产
不完整或含额外附件的 Release 只报告。完整资产指唯一对应的 `TongWen_Installer_<tag>.msi`
和 `SHA256SUMS.txt`，均已上传且非空。

每次最多处理 5 个 Release，按 `published_at` 从旧到新选取。其余符合条件的项目显示为
`defer`；后续需要重新预览。没有对应 Release 的 Tag 只报告，不根据其提交日期自动删除。

## 保护来源

以下保护优先于数量和年龄条件：

- 每条产品线最新的正式版，以及 GitHub `/releases/latest`。
- `config/ReleaseRetention.json` 的 `website_download_tags`：当前为 `v2.0.4`、`v0.2.29`。
- 配置的 `pinned_tags`：初始为 `v0.2.27`，保留历史回退选择。
- 必需的线上策略 `https://fscad.xyz/updates/tongwen/stable.json`：保护 `latest_version`、
  下载地址指向版本，以及非 `0.0.0` 的最低支持版本。策略目前还指向 `v2.0.2`。

官网当前下载通过显式配置登记，不解析 HTML。**修改官网当前版本或增加回退入口时，必须
同步更新此配置，再生成清理预览。** 新增独立经典版策略时需一起修改配置验证与解析，
不能把目前不存在的端点当作已接入。保护源请求失败、响应不受支持，或保护目标缺少
公开 Release/Tag 时，预览和执行都阻止；不忽略错误后继续删除。

## Actions 使用

打开 [Release retention](https://github.com/FeiSiPub/TongWenReleases/actions/workflows/cleanup-releases.yml)，
点击 **Run workflow**，分支必须选择 `main`。

| 输入 | 默认值 | 作用 |
| --- | --- | --- |
| `mode` | `preview` | 预览或执行 |
| `product_line` | `all` | `all` / `classic` / `v2` |
| `keep_classic_stable` | `3` | 经典版正式版保留数量 |
| `keep_v2_stable` | `3` | 同文 2 正式版保留数量 |
| `stable_min_age_days` | `30` | 正式版最短保留天数 |
| `keep_prerelease_per_line` | `1` | 各产品线预发布保留数量 |
| `prerelease_min_age_days` | `14` | 预发布最短保留天数 |
| `preview_run_id` | 空 | 执行时填成功预览的运行编号 |

数量和天数必须为 1–3650 的整数。输入只在预览时生效；执行时使用预览中保存的参数，
不会把当前表单参数或新出现的候选加入删除清单。工作流输入默认值与配置默认值应一起维护，
聚焦检查会核对二者。

1. 先运行 `mode=preview`。Summary 按 `retain`、`delete`、`defer`、`skip` 列出每版理由、
   发布时间、全部附件大小和公开 Tag 的对象 SHA。另列孤立 Tag 与保护来源。
2. 下载 `release-cleanup-plan` artifact。它包含 `cleanup-plan.json` 和 `cleanup-plan.md`；
   保留参数、完整库存身份、Release/附件 ID、大小/可用摘要、Tag 对象、保护快照、代码提交、
   run ID/attempt、计划摘要和有效期。附件字节数不代表账单节省。
3. 核对所有 `delete` 行，确认确实不再需要这些公开下载。需要排除版本时先修改手动保留
   配置，再生成预览。不要手工修改下载的 JSON。
4. 在 **24 小时内**再手动运行 `mode=execute`，填写该预览的 `preview_run_id`。
   main 必须仍是同一提交。无需复制计划内容或配置新的 PAT。
5. 查阅执行 Summary 和 `release-cleanup-result-<attempt>` artifact，逐项确认删除、跳过或失败。

计划文件保留 14 天，但执行有效期仅 24 小时。执行报告保留 90 天。PR/push 只运行离线检查，
手动预览使用 `contents: read`；执行单独获得 `contents: write` 和 `actions: read`。
使用本仓库的 `GITHUB_TOKEN`，不需要源码仓库或 R2 凭据。工作流固定 Actions 完整提交 SHA。

## 执行与失败语义

执行先确认计划来自本仓库此工作流、`main`、相同提交的成功手动预览，并核对 run attempt、
唯一未过期 artifact、配置摘要、计划摘要及根据保存输入重算的确定性清单。本地生成的计划
不能用于真实删除。每项删除前重新读取库存、GitHub Latest 和线上保护策略，确认数量下限
仍成立，Release/附件元数据与原计划完全一致，Tag 仍指向原对象。变化项仅跳过，不扩大清单。

每版顺序为 **删除 Release → 确认 Release 不存在 → 再核对保护与 Tag → 删除 Tag → 确认 Tag
不存在**。两步不是事务；第二步失败时立即停止后续目标，保留已完成与待处理状态。
跨仓库发布者不受本工作流 concurrency 约束，应避免同时发布和清理。API 不提供 Tag 的
条件删除，最终核对与 DELETE 之间仍存在很短的并发窗口。

同一有效预览可以再次 `execute`，用于补完已删除 Release 后遗留的原 Tag；仅允许该计划的
同一 Tag 对象，不能处理其他孤立 Tag。两者都不存在时报告 `already_absent`，不会伪称新删除。
目标重新发布、Tag 改指、出现新保护或数量限制时停止或跳过；API 失败不自动重试。
计划过期或 main 变化后禁止执行：重新预览会把遗留 Tag 列为孤立项，需要维护者另行核对处理，
不能通过放宽孤立 Tag 规则绕过。

网络请求每次 30 秒超时，不重试；工作流 15 分钟上限。正常失败会保存诊断。强制取消或宿主
终止可能发生在两个 API 操作之间，报告也可能来不及上传，此时需读取 GitHub 实际状态后恢复，
不能仅根据缺少最终报告断言没有删除。脚本不写入 token、请求头或任意服务端响应正文。

## 维护与验证

实现集中在 `scripts/cleanup_releases.py`，仅 Python 标准库，无 CAD、MSI 或 .NET 构建依赖。
预览与执行共用同一候选判定函数；执行不接受任意仓库、Tag 列表或删除 URL。
README 中的当前下载、配置中的保护集合和 `docs/ReleaseLifecycle.md` 应保持一致。

```powershell
python -m unittest discover -s tests -v
python scripts/cleanup_releases.py validate-config
```

聚焦离线检查覆盖数量/年龄交集、数值排序、实际预发布标记、异常项、孤立 Tag、保护目标、
计划篡改/过期、来源验证、执行时变化、部分失败与同计划恢复；不会访问网络或执行真实删除。
真实 Actions 预览证明只读库存链路；它不证明真实删除权限或两步删除已经实测。
