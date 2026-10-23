"""Public-mirror retention: read-only plans, then explicitly dispatched execution.

The source repository, R2, website and update policy are never mutation targets.
See docs/ReleaseRetention.md for the plan/execute contract and failure recovery.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


REPOSITORY = "FeiSiPub/TongWenReleases"
WORKFLOW = ".github/workflows/cleanup-releases.yml"
ARTIFACT = "release-cleanup-plan"
ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = (
    "product_line", "keep_classic_stable", "keep_v2_stable",
    "stable_min_age_days", "keep_prerelease_per_line", "prerelease_min_age_days",
)
TAG_PATTERN = re.compile(
    r"^v(0|2)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-preview\.([1-9][0-9]*))?$"
)


class CleanupError(Exception):
    """An unsafe, incomplete or failed operation; never silently continue."""


class NoRedirect(HTTPRedirectHandler):
    # API redirects must not forward a repository token to another origin.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def now_utc():
    return datetime.now(timezone.utc)


def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def date(value):
    if not isinstance(value, str):
        raise CleanupError("Missing or invalid timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CleanupError("Invalid timestamp") from error
    if result.tzinfo is None:
        raise CleanupError("Timestamp must have a timezone")
    return result.astimezone(timezone.utc)


def digest(value):
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def read_json(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise CleanupError("JSON input exceeds 16 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def version(tag):
    match = TAG_PATTERN.fullmatch(tag) if isinstance(tag, str) else None
    if not match:
        return None
    major, minor, patch = (int(match[i]) for i in (1, 2, 3))
    if major == 0 and minor != 2:
        return None
    preview = int(match[4]) if match[4] else None
    return ("classic" if major == 0 else "v2", (major, minor, patch, preview is None, preview or 0))


def validate_parameters(values):
    if set(values) != set(PARAMETERS) or values["product_line"] not in ("all", "classic", "v2"):
        raise CleanupError("Invalid retention parameters")
    result = {"product_line": values["product_line"]}
    for key in PARAMETERS[1:]:
        value = values[key]
        if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]*", str(value)):
            raise CleanupError(f"{key} must be a positive integer")
        result[key] = int(value)
        if result[key] > 3650:
            raise CleanupError(f"{key} exceeds the supported maximum (3650)")
    return result


def load_config():
    config = read_json(ROOT / "config/ReleaseRetention.json")
    expected = {
        "schema_version", "repository", "default_branch", "preview_valid_hours",
        "max_deletions_per_run", "website_download_tags", "pinned_tags",
        "required_policy_urls", "defaults",
    }
    if set(config) != expected or config["schema_version"] != 1:
        raise CleanupError("Unsupported retention configuration")
    if config["repository"] != REPOSITORY or config["default_branch"] != "main":
        raise CleanupError("This script is restricted to the public mirror on main")
    if type(config["preview_valid_hours"]) is not int or not 1 <= config["preview_valid_hours"] <= 24:
        raise CleanupError("Preview validity must be 1..24 hours")
    if type(config["max_deletions_per_run"]) is not int or not 1 <= config["max_deletions_per_run"] <= 5:
        raise CleanupError("Deletion cap must be 1..5 releases")
    for key in ("website_download_tags", "pinned_tags"):
        if not isinstance(config[key], list) or any(not version(tag) for tag in config[key]):
            raise CleanupError(f"Invalid {key}")
    # New policy channels must be deliberately reviewed in code and configuration.
    if config["required_policy_urls"] != ["https://fscad.xyz/updates/tongwen/stable.json"]:
        raise CleanupError("The current shared stable policy is required")
    config["defaults"] = validate_parameters(config["defaults"])
    return config


def fetch_json(url, token=None, allow_missing=False, method="GET"):
    headers = {"User-Agent": "TongwenReleaseRetention/1", "Cache-Control": "no-cache"}
    if token:
        headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
    try:
        with build_opener(NoRedirect()).open(Request(url, headers=headers, method=method), timeout=30) as response:
            if method == "DELETE":
                if response.status != 204:
                    raise CleanupError("Delete did not return HTTP 204")
                return None
            body = response.read(32 * 1024 * 1024 + 1)
            if len(body) > 32 * 1024 * 1024:
                raise CleanupError("API response exceeds 32 MiB")
            return json.loads(body)
    except HTTPError as error:
        if allow_missing and method == "GET" and error.code == 404:
            return None
        # Never include headers, token, signed URLs or arbitrary response bodies.
        raise CleanupError(f"{method} {urlparse(url).path}: HTTP {error.code}") from None
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise CleanupError(f"{method} {urlparse(url).path}: {type(error).__name__}") from None


class GitHub:
    def __init__(self, token):
        if not token:
            raise CleanupError("GH_TOKEN is required; never put it in configuration")
        self.token = token

    def get(self, path, allow_missing=False):
        return fetch_json(f"https://api.github.com/repos/{REPOSITORY}/{path}", self.token, allow_missing)

    def pages(self, path, field=None):
        result = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            data = self.get(f"{path}{separator}per_page=100&page={page}")
            items = data[field] if field else data
            if not isinstance(items, list):
                raise CleanupError("Expected a paginated list")
            result.extend(items)
            if len(items) < 100:
                return result
        raise CleanupError("Pagination limit reached; no partial inventory is safe")

    def delete_release(self, release_id):
        if type(release_id) is not int or release_id <= 0:
            raise CleanupError("Invalid release ID")
        fetch_json(f"https://api.github.com/repos/{REPOSITORY}/releases/{release_id}", self.token, method="DELETE")

    def delete_tag(self, tag):
        if not version(tag):
            raise CleanupError("Only a recognized, planned release tag can be deleted")
        fetch_json(f"https://api.github.com/repos/{REPOSITORY}/git/refs/tags/{quote(tag, safe='')}", self.token, method="DELETE")


def release_snapshot(release):
    fields = ("id", "tag_name", "name", "draft", "prerelease", "created_at", "published_at", "updated_at", "immutable")
    result = {field: release.get(field) for field in fields}
    result["body_sha256"] = digest(release.get("body"))
    asset_fields = ("id", "name", "size", "digest", "state", "content_type", "created_at", "updated_at")
    result["assets"] = sorted(
        ({field: asset.get(field) for field in asset_fields} for asset in release.get("assets", [])),
        key=lambda item: item["id"],
    )
    return result


def collect_inventory(api):
    releases = [release_snapshot(item) for item in api.pages("releases")]
    tags = []
    for tag in api.pages("tags"):
        ref = api.get(f"git/ref/tags/{quote(tag['name'], safe='')}", allow_missing=True)
        if ref is None:
            raise CleanupError("A tag changed during inventory; generate a fresh preview")
        tags.append({
            "name": tag["name"], "sha": ref["object"]["sha"],
            "type": ref["object"]["type"], "commit_sha": tag["commit"]["sha"],
        })
    return {"releases": sorted(releases, key=lambda item: item["id"]), "tags": sorted(tags, key=lambda item: item["name"])}


def policy_tags(policy):
    if not isinstance(policy, dict):
        raise CleanupError("Stable policy is not an object")
    latest = policy.get("latest_version")
    if not isinstance(latest, str) or not version("v" + latest):
        raise CleanupError("Stable policy has no recognized latest_version")
    tags = {"v" + latest}
    minimum = policy.get("minimum_supported_version")
    if minimum not in (None, "0.0.0"):
        if not isinstance(minimum, str) or not version("v" + minimum):
            raise CleanupError("Stable policy minimum version is unrecognized")
        tags.add("v" + minimum)
    parsed = urlparse(policy.get("download_url", ""))
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        raise CleanupError("Stable policy download_url is unsupported")
    if parsed.netloc == "github.com":
        match = re.fullmatch(r"/FeiSiPub/TongWenReleases/releases/(?:tag|download)/(v[^/]+)(?:/[^/]+)?", parsed.path)
    elif parsed.netloc == "tongwen-download.278848.xyz":
        match = re.fullmatch(r"/releases/(v[^/]+)/[^/]+", parsed.path)
    else:
        match = None
    if not match or not version(match[1]):
        raise CleanupError("Stable policy download target is unrecognized")
    tags.add(match[1])
    return sorted(tags)


def collect_protection(api, config, inventory, policy_reader=fetch_json):
    reasons = {}

    def protect(tag, reason):
        reasons.setdefault(tag, []).append(reason)

    for tag in config["website_download_tags"]:
        protect(tag, "website_download")
    for tag in config["pinned_tags"]:
        protect(tag, "manual_pin")
    latest = api.get("releases/latest", allow_missing=True)
    if latest:
        protect(latest["tag_name"], "github_latest")
    elif any(not item["draft"] and not item["prerelease"] for item in inventory["releases"]):
        raise CleanupError("GitHub latest is missing despite stable releases")
    for line in ("classic", "v2"):
        stable = [item for item in inventory["releases"] if not item["draft"] and not item["prerelease"]
                  and version(item["tag_name"]) and version(item["tag_name"])[0] == line]
        if stable:
            newest = max(stable, key=lambda item: version(item["tag_name"])[1])
            protect(newest["tag_name"], "newest_stable_in_line")
    policies = []
    for url in config["required_policy_urls"]:
        policy = policy_reader(url)
        targets = policy_tags(policy)
        policies.append({"url": url, "policy_sha256": digest(policy), "tags": targets})
        for tag in targets:
            protect(tag, "online_update_policy")
    known_tags = {item["name"] for item in inventory["tags"]}
    published_tags = {item["tag_name"] for item in inventory["releases"] if not item["draft"]}
    # A missing pinned/current target signals drift, not permission to delete more.
    if not set(reasons).issubset(known_tags & published_tags):
        raise CleanupError("A protected version is missing its public Release or Tag")
    return {"tags": {tag: sorted(values) for tag, values in sorted(reasons.items())}, "policies": policies}


def release_problem(release, tags, reference_time):
    tag = release["tag_name"]
    if release["draft"]:
        return "draft"
    if not version(tag):
        return "unknown_tag_format"
    if "-" in tag and not release["prerelease"]:
        return "suffix_with_stable_flag"
    if release["immutable"]:
        return "immutable_release"
    if tag not in tags or tags[tag]["type"] not in ("commit", "tag"):
        return "missing_or_unsupported_tag"
    try:
        published = date(release["published_at"])
    except CleanupError:
        return "missing_publication_time"
    if published > reference_time:
        return "future_publication_time"
    assets = release["assets"]
    names = {item["name"] for item in assets}
    if len(assets) != 2 or names != {f"TongWen_Installer_{tag}.msi", "SHA256SUMS.txt"}:
        return "unexpected_or_incomplete_assets"
    if any(type(item["id"]) is not int or type(item["size"]) is not int or item["size"] <= 0 or item["state"] != "uploaded" for item in assets):
        return "incomplete_asset_upload"
    return None


def decisions(inventory, protection, parameters, reference_time, cap):
    tags = {item["name"]: item for item in inventory["tags"]}
    counts = {}
    for item in inventory["releases"]:
        counts[item["tag_name"]] = counts.get(item["tag_name"], 0) + 1
    valid = []
    result = []
    for item in inventory["releases"]:
        tag = item["tag_name"]
        problem = release_problem(item, tags, reference_time)
        if counts[tag] != 1:
            problem = "duplicate_release_tag"
        row = {"release": item, "tag": tags.get(tag), "status": "skip", "reasons": []}
        if problem:
            row["reasons"] = [problem]
        else:
            row["line"], _ = version(tag)
            row["age_days"] = (reference_time - date(item["published_at"])).total_seconds() / 86400
            valid.append(row)
        result.append(row)
    # Only complete, classifiable published releases count toward the retained floor.
    for line in ("classic", "v2"):
        for pre in (False, True):
            group = sorted([row for row in valid if row["line"] == line and row["release"]["prerelease"] == pre],
                           key=lambda row: version(row["release"]["tag_name"])[1], reverse=True)
            floor = parameters["keep_prerelease_per_line"] if pre else parameters[f"keep_{line}_stable"]
            minimum_age = parameters["prerelease_min_age_days"] if pre else parameters["stable_min_age_days"]
            for index, row in enumerate(group):
                reasons = row["reasons"]
                if parameters["product_line"] not in ("all", line):
                    reasons.append("outside_selected_line")
                reasons.extend(protection["tags"].get(row["release"]["tag_name"], []))
                if index < floor:
                    reasons.append("within_count_floor")
                if row["age_days"] < minimum_age:
                    reasons.append("too_recent")
                row["status"] = "retain" if reasons else "eligible"
                if not reasons:
                    reasons.append("outside_floor_and_old_enough")
    eligible = sorted([row for row in result if row["status"] == "eligible"],
                      key=lambda row: (row["release"]["published_at"], row["release"]["id"]))
    for index, row in enumerate(eligible):
        row["status"] = "delete" if index < cap else "defer"
        if index >= cap:
            row["reasons"].append("per_run_cap")
    release_tags = {item["tag_name"] for item in inventory["releases"]}
    orphans = [tag for tag in inventory["tags"] if tag["name"] not in release_tags]
    return result, orphans


def make_plan(config, parameters, inventory, protection, provenance, reference_time):
    # Persist and recompute at the same precision; do not invalidate a plan because
    # the preview clock originally contained microseconds.
    reference_time = date(stamp(reference_time))
    rows, orphans = decisions(inventory, protection, parameters, reference_time, config["max_deletions_per_run"])
    targets = sorted([{"release": row["release"], "tag": row["tag"]} for row in rows if row["status"] == "delete"],
                     key=lambda item: (item["release"]["published_at"], item["release"]["id"]))
    plan = {
        "schema_version": 1, "repository": REPOSITORY, "mode": "preview",
        "generated_at": stamp(reference_time),
        "expires_at": stamp(reference_time + timedelta(hours=config["preview_valid_hours"])),
        "configuration": config, "config_sha256": digest(config), "parameters": parameters, "provenance": provenance,
        "inventory": inventory, "protection": protection, "decisions": rows,
        "orphan_tags": orphans, "targets": targets,
    }
    plan["plan_sha256"] = digest(plan)
    return plan


def validate_plan(plan, config, reference_time):
    payload = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if plan.get("schema_version") != 1 or plan.get("repository") != REPOSITORY or plan.get("mode") != "preview":
        raise CleanupError("Unsupported cleanup plan")
    if digest(payload) != plan.get("plan_sha256") or plan.get("config_sha256") != digest(config):
        raise CleanupError("Plan or configuration changed; generate a new preview")
    generated = date(plan["generated_at"])
    if generated > reference_time or reference_time >= date(plan["expires_at"]):
        raise CleanupError("Preview is stale or dated in the future")
    parameters = validate_parameters(plan["parameters"])
    expected = make_plan(config, parameters, plan["inventory"], plan["protection"], plan["provenance"], generated)
    if expected != plan:
        raise CleanupError("Plan is not the deterministic result of its saved inputs")
    return plan


def action_provenance(mode):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        if mode == "execute":
            raise CleanupError("Real deletion is restricted to the manual GitHub workflow")
        return {"workflow": WORKFLOW, "run_id": "local", "run_attempt": "1", "head_sha": "local", "ref": "local"}
    expected_ref = "refs/heads/main"
    if (os.environ.get("GITHUB_REPOSITORY") != REPOSITORY
            or os.environ.get("GITHUB_REF") != expected_ref
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or os.environ.get("GITHUB_WORKFLOW_REF") != f"{REPOSITORY}/{WORKFLOW}@{expected_ref}"):
        raise CleanupError("Cleanup must run manually from this repository's main branch")
    event = read_json(Path(os.environ["GITHUB_EVENT_PATH"]))
    if event.get("inputs", {}).get("mode") != mode:
        raise CleanupError("Workflow mode does not match the requested operation")
    return {
        "workflow": WORKFLOW, "run_id": os.environ["GITHUB_RUN_ID"],
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "head_sha": os.environ["GITHUB_SHA"], "ref": expected_ref,
    }


def validate_preview_run(api, plan, run_id, current):
    if not re.fullmatch(r"[1-9][0-9]*", run_id) or run_id == current["run_id"]:
        raise CleanupError("A separate successful preview run ID is required")
    event = read_json(Path(os.environ["GITHUB_EVENT_PATH"]))
    if event.get("inputs", {}).get("preview_run_id") != run_id:
        raise CleanupError("Preview ID differs from the workflow input")
    run = api.get(f"actions/runs/{run_id}")
    workflow = api.get("actions/workflows/cleanup-releases.yml")
    origin = plan["provenance"]
    if (str(run["id"]) != run_id or str(origin["run_id"]) != run_id
            or run["workflow_id"] != workflow["id"] or run["path"] != WORKFLOW
            or run["repository"]["full_name"] != REPOSITORY
            or run["head_repository"]["full_name"] != REPOSITORY
            or run["event"] != "workflow_dispatch" or run["head_branch"] != "main"
            or run["status"] != "completed" or run["conclusion"] != "success"
            or str(run["run_attempt"]) != str(origin["run_attempt"])
            or run["head_sha"] != current["head_sha"] or origin["head_sha"] != current["head_sha"]
            or origin["workflow"] != WORKFLOW or origin["ref"] != "refs/heads/main"):
        raise CleanupError("Preview provenance is untrusted, failed or from a different main commit")
    artifacts = [item for item in api.pages(f"actions/runs/{run_id}/artifacts", "artifacts") if item["name"] == ARTIFACT]
    if len(artifacts) != 1 or artifacts[0]["expired"] or artifacts[0]["workflow_run"]["id"] != int(run_id):
        raise CleanupError("Exactly one unexpired preview artifact is required")
    verify_execution_window(api, plan)


def markdown_text(value):
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ").replace("`", "'").replace("<", "&lt;")


def render_preview(plan):
    lines = [
        "# 公开安装包清理预览", "", "本次为只读预览，未删除任何 Release、资产或 Tag。", "",
        f"- 仓库：`{REPOSITORY}`；预览 run：`{plan['provenance']['run_id']}`",
        f"- 计划摘要：`{plan['plan_sha256']}`",
        f"- 生成：{plan['generated_at']}；执行截止：{plan['expires_at']}（UTC）",
        f"- 有效参数：`{json.dumps(plan['parameters'], ensure_ascii=False)}`",
        "- 发布时间用于年龄判定；版本号用于保留数量排序。Draft、未知或不完整项只报告。",
        "- 不改源码仓库、R2、官网或升级策略。此操作不等于软件停用或全渠道下架。", "",
        "| 状态 | Tag | GitHub 分类 | published_at (UTC) | 资产 bytes | Tag object SHA | 原因 |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in sorted(plan["decisions"], key=lambda item: (item["release"]["published_at"] or "", item["release"]["id"])):
        release = row["release"]
        tag = row["tag"]
        values = (row["status"], release["tag_name"], "prerelease" if release["prerelease"] else "stable",
                  release["published_at"], sum(item["size"] or 0 for item in release["assets"]),
                  tag["sha"] if tag else "missing", ", ".join(row["reasons"]))
        lines.append("| " + " | ".join(markdown_text(value) for value in values) + " |")
    total = sum(asset["size"] for target in plan["targets"] for asset in target["release"]["assets"])
    lines += ["", f"计划删除 **{len(plan['targets'])}** 个 Release 及对应 Tag，包含资产 **{total:,} bytes**。",
              "资产字节数用于范围估算，不代表计费节省；Release 删除会移除其所有附件。", "", "## 保护来源", ""]
    for tag, reasons in plan["protection"]["tags"].items():
        lines.append(f"- `{tag}`：{', '.join(reasons)}")
    for policy in plan["protection"]["policies"]:
        lines.append(f"- 策略：{policy['url']}；响应摘要 `{policy['policy_sha256']}`")
    lines += ["", "## 没有 Release 的 Tag（只报告）", ""]
    for tag in plan["orphan_tags"]:
        lines.append(f"- `{markdown_text(tag['name'])}` → `{tag['sha']}`")
    if not plan["orphan_tags"]:
        lines.append("无。")
    lines += ["", "## 执行", "", "核对上述 delete 行后，手动重跑本工作流，mode=execute，preview_run_id=本预览 run ID。",
              "执行只读取本计划保存的参数；其他保留参数输入不生效。main 或配置变化、计划过期、保护源不可读会阻止执行。",
              "每项执行前重新核对保护、数量与身份；只允许跳过原目标，不能增加目标。Tag 单独存在不代表过期。", ""]
    return "\n".join(lines)


def write_outputs(directory, data, report, stem):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{stem}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (directory / f"{stem}.md").write_text(report, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(report + "\n")


def current_tag(api, name):
    ref = api.get(f"git/ref/tags/{quote(name, safe='')}", allow_missing=True)
    return {"sha": ref["object"]["sha"], "type": ref["object"]["type"]} if ref else None


def same_ref(actual, planned):
    return actual is not None and actual["sha"] == planned["sha"] and actual["type"] == planned["type"]


def verify_execution_window(api, plan):
    if now_utc() >= date(plan["expires_at"]):
        raise CleanupError("Preview expired; no further deletion permitted")
    # Re-running an old workflow keeps GITHUB_SHA unchanged even if main moved.
    # Compare the live branch as well, including before each destructive API call.
    main_ref = api.get("git/ref/heads/main")
    if main_ref["object"]["sha"] != plan["provenance"]["head_sha"]:
        raise CleanupError("Live main changed; generate a new preview")


def finish_tag(api, config, plan, target, progress):
    # A publisher may reuse the tag between the two DELETE operations. Recheck
    # public references and the exact ref again instead of deleting a new target.
    inventory = collect_inventory(api)
    protection = collect_protection(api, config, inventory)
    name = target["tag"]["name"]
    if name in protection["tags"] or any(item["tag_name"] == name for item in inventory["releases"]):
        raise CleanupError("Release removed; tag now protected or has a new Release. Tag retained")
    verify_execution_window(api, plan)
    actual = current_tag(api, name)
    if actual is None:
        progress["status"] = "already_absent" if not progress.get("release_deleted") else "deleted"
        return
    if not same_ref(actual, target["tag"]):
        raise CleanupError("Release removed; tag target changed. Tag retained")
    progress["tag_delete_requested"] = True
    api.delete_tag(name)
    if current_tag(api, name) is not None:
        raise CleanupError("Tag deletion could not be confirmed")
    progress["tag_deleted"] = True
    progress["status"] = "deleted"


def execute_targets(api, config, plan, results, checkpoint):
    for target in plan["targets"]:
        validate_plan(plan, config, now_utc())
        name = target["release"]["tag_name"]
        progress = {"tag": name, "release_id": target["release"]["id"], "status": "checking"}
        results.append(progress)
        checkpoint()
        try:
            inventory = collect_inventory(api)
            protection = collect_protection(api, config, inventory)
            matches = [item for item in inventory["releases"] if item["tag_name"] == name]
            if not matches:
                progress.update({"release_absent": True, "status": "release_absent_tag_pending"})
                checkpoint()
                # Only the tag tied to this successful preview may be completed
                # on retry; unrelated orphan tags never enter this code path.
                finish_tag(api, config, plan, target, progress)
            else:
                rows, _ = decisions(inventory, protection, plan["parameters"], now_utc(), config["max_deletions_per_run"])
                row = next((item for item in rows if item["release"]["id"] == target["release"]["id"]), None)
                actual = api.get(f"releases/{target['release']['id']}", allow_missing=True)
                verify_execution_window(api, plan)
                if (len(matches) != 1 or row is None or row["status"] not in ("delete", "defer")
                        or actual is None or release_snapshot(actual) != target["release"]
                        or not same_ref(current_tag(api, name), target["tag"])):
                    progress.update({"status": "skipped_changed_or_retained", "reasons": row["reasons"] if row else ["release_replaced"]})
                    checkpoint()
                    continue
                progress["release_delete_requested"] = True
                checkpoint()
                api.delete_release(target["release"]["id"])
                progress.update({"release_delete_acknowledged": True, "status": "release_delete_pending_confirmation"})
                checkpoint()
                if api.get(f"releases/{target['release']['id']}", allow_missing=True) is not None:
                    raise CleanupError("Release deletion could not be confirmed; no tag deletion attempted")
                progress.update({"release_deleted": True, "status": "release_deleted_tag_pending"})
                checkpoint()
                finish_tag(api, config, plan, target, progress)
            checkpoint()
        except Exception as error:
            # A DELETE timeout may mean the server completed it. Record only
            # confirmed results instead of asserting that an object still exists.
            progress.update({"status": "failed_after_release_delete" if progress.get("release_deleted") else "failed", "error": str(error) if isinstance(error, CleanupError) else type(error).__name__})
            checkpoint()
            raise


def render_execution(result):
    lines = ["# 公开安装包清理执行", "", f"状态：**{result['status']}**；预览 run：`{result.get('preview_run_id', '')}`。", "",
             "| Tag | Release ID | 结果 | 本次确认 Release 删除 | 本次确认 Tag 删除 | 说明 |", "| --- | --- | --- | --- | --- | --- |"]
    for item in result["results"]:
        values = (item["tag"], item["release_id"], item["status"], item.get("release_deleted", False), item.get("tag_deleted", False), item.get("error", ", ".join(item.get("reasons", []))))
        lines.append("| " + " | ".join(markdown_text(value) for value in values) + " |")
    if result.get("error"):
        lines += ["", "阻止/停止原因：" + markdown_text(result["error"])]
    lines += ["", "只处理本预览的固定目标；未处理项不会自动重试。源码仓库、R2、官网和策略未修改。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("validate-config", "preview", "execute"))
    parser.add_argument("--output", type=Path, default=ROOT / "cleanup-output")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--preview-run-id", default="")
    args = parser.parse_args()
    result = {"status": "blocked", "preview_run_id": args.preview_run_id, "results": []}
    try:
        config = load_config()
        if args.mode == "validate-config":
            print("Retention configuration valid")
            return 0
        provenance = action_provenance(args.mode)
        api = GitHub(os.environ.get("GH_TOKEN"))
        if args.mode == "preview":
            values = {key: os.environ.get("INPUT_" + key.upper(), str(value)) for key, value in config["defaults"].items()}
            parameters = validate_parameters(values)
            inventory = collect_inventory(api)
            protection = collect_protection(api, config, inventory)
            plan = make_plan(config, parameters, inventory, protection, provenance, now_utc())
            write_outputs(args.output, plan, render_preview(plan), "cleanup-plan")
            print(f"Read-only preview: {len(plan['targets'])} releases proposed; no deletions")
        else:
            if args.plan is None:
                raise CleanupError("Execution requires a downloaded preview plan")
            plan = validate_plan(read_json(args.plan), config, now_utc())
            validate_preview_run(api, plan, args.preview_run_id, provenance)
            result.update({"status": "running", "plan_sha256": plan["plan_sha256"], "started_at": stamp(now_utc())})

            def checkpoint():
                write_outputs(args.output, result, render_execution(result), "cleanup-result")

            execute_targets(api, config, plan, result["results"], checkpoint)
            result.update({"status": "completed", "finished_at": stamp(now_utc())})
            checkpoint()
        return 0
    except Exception as error:
        message = str(error) if isinstance(error, CleanupError) else type(error).__name__
        print(f"Cleanup stopped: {message}", file=sys.stderr)
        if args.mode != "validate-config":
            result.update({"status": "failed_or_blocked", "error": message})
            stem = "cleanup-result" if args.mode == "execute" else "cleanup-blocked"
            write_outputs(args.output, result, render_execution(result), stem)
        return 1


if __name__ == "__main__":
    sys.exit(main())
