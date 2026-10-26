"""Small offline suite for destructive-operation boundaries; no network calls."""

import copy
from datetime import timedelta
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cleanup_releases as cleanup


NOW = cleanup.date("2026-10-23T14:00:00Z")
POLICY = {
    "latest_version": "2.0.2", "minimum_supported_version": "0.0.0",
    "download_url": "https://github.com/FeiSiPub/TongWenReleases/releases/tag/v2.0.2",
}


def raw_release(tag, release_id, age=90, pre=False):
    published = cleanup.stamp(NOW - timedelta(days=age))
    return {
        "id": release_id, "tag_name": tag, "name": tag, "body": "Original notes",
        "draft": False, "prerelease": pre, "immutable": False,
        "created_at": "2026-10-12T00:00:00Z", "published_at": published, "updated_at": published,
        "assets": [
            {"id": release_id * 10, "name": f"TongWen_Installer_{tag}.msi", "size": 200,
             "digest": "sha256:" + "a" * 64, "state": "uploaded", "content_type": "application/octet-stream",
             "created_at": published, "updated_at": published},
            {"id": release_id * 10 + 1, "name": "SHA256SUMS.txt", "size": 80,
             "digest": None, "state": "uploaded", "content_type": "text/plain",
             "created_at": published, "updated_at": published},
        ],
    }


class FakeGitHub:
    def __init__(self):
        tags = ["v0.2.20", "v0.2.22", "v0.2.23", "v0.2.24", "v0.2.25", "v0.2.26", "v0.2.27", "v0.2.28",
                "v2.0.1", "v2.0.2", "v2.0.4"]
        self.releases = {index: raw_release(tag, index) for index, tag in enumerate(tags, 1)}
        for index, tag in enumerate(("v0.2.21", "v2.0.0-preview.3", "v2.0.0-preview.4", "v2.0.3-preview.1"), 20):
            self.releases[index] = raw_release(tag, index, pre=True)
        self.tags = {item["tag_name"]: {"name": item["tag_name"], "sha": str(index).zfill(40),
                                      "commit_sha": str(index).zfill(40), "type": "commit"}
                     for index, item in self.releases.items()}
        self.tags["0.2.10"] = {"name": "0.2.10", "sha": "c" * 40, "commit_sha": "c" * 40, "type": "commit"}
        self.calls = []
        self.fail_tag = False

    def inventory(self):
        return {"releases": sorted((cleanup.release_snapshot(item) for item in self.releases.values()), key=lambda item: item["id"]),
                "tags": sorted(copy.deepcopy(list(self.tags.values())), key=lambda item: item["name"])}

    def get(self, path, allow_missing=False):
        if path == "git/ref/heads/main":
            return {"object": {"sha": "a" * 40}}
        if path == "releases/latest":
            return copy.deepcopy(next(item for item in self.releases.values() if item["tag_name"] == "v2.0.4"))
        if path.startswith("releases/"):
            result = self.releases.get(int(path.split("/")[1]))
            return copy.deepcopy(result)
        if path.startswith("git/ref/tags/"):
            tag = self.tags.get(path.split("git/ref/tags/")[1])
            return {"object": {"sha": tag["sha"], "type": tag["type"]}} if tag else None
        raise AssertionError(f"Unexpected API path: {path}")

    def delete_release(self, release_id):
        self.calls.append(("release", release_id))
        del self.releases[release_id]

    def delete_tag(self, name):
        if self.fail_tag:
            raise cleanup.CleanupError("Injected tag deletion failure")
        self.calls.append(("tag", name))
        del self.tags[name]


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.config = cleanup.load_config()
        # Match this fixed historical inventory, independently of current website releases.
        self.config["website_download_tags"] = ["v0.2.28", "v2.0.4"]
        self.api = FakeGitHub()
        self.parameters = copy.deepcopy(self.config["defaults"])
        self.origin = {"workflow": cleanup.WORKFLOW, "run_id": "123", "run_attempt": "1",
                       "head_sha": "a" * 40, "ref": "refs/heads/main"}

    def protection(self):
        return cleanup.collect_protection(self.api, self.config, self.api.inventory(), policy_reader=lambda url: POLICY)

    def plan(self):
        return cleanup.make_plan(self.config, self.parameters, self.api.inventory(), self.protection(), self.origin, NOW)

    def rows(self):
        return {item["release"]["tag_name"]: item for item in self.plan()["decisions"]}

    def test_count_age_and_cap_intersection(self):
        rows = self.rows()
        self.assertEqual([rows[f"v0.2.{number}"]["status"] for number in (26, 27, 28)], ["retain"] * 3)
        self.assertEqual(len(self.plan()["targets"]), 5)
        self.assertEqual(sum(item["status"] == "defer" for item in rows.values()), 2)
        self.api.releases[1]["published_at"] = cleanup.stamp(NOW - timedelta(days=29))
        self.assertIn("too_recent", self.rows()["v0.2.20"]["reasons"])
        self.api.releases[1]["published_at"] = cleanup.stamp(NOW - timedelta(days=30))
        self.assertIn(self.rows()["v0.2.20"]["status"], ("delete", "defer"))

    def test_numeric_sort_actual_prerelease_and_publication_date(self):
        self.assertGreater(cleanup.version("v0.2.28")[1], cleanup.version("v0.2.9")[1])
        self.assertGreater(cleanup.version("v2.0.0-preview.10")[1], cleanup.version("v2.0.0-preview.9")[1])
        self.assertEqual(self.rows()["v0.2.21"]["status"], "retain")
        self.assertEqual(self.rows()["v2.0.3-preview.1"]["status"], "retain")
        self.assertEqual(self.rows()["v0.2.20"]["age_days"], 90)
        # created_at is recent, but the public release is old enough.
        self.assertEqual(self.rows()["v0.2.20"]["status"], "delete")

    def test_protected_target_survives_small_floor(self):
        self.parameters["keep_v2_stable"] = 1
        self.assertIn("online_update_policy", self.rows()["v2.0.2"]["reasons"])
        self.assertIn("manual_pin", self.rows()["v0.2.27"]["reasons"])
        self.assertIn("website_download", self.rows()["v2.0.4"]["reasons"])
        self.parameters["product_line"] = "v2"
        self.assertTrue(all(target["release"]["tag_name"].startswith("v2.") for target in self.plan()["targets"]))

    def test_abnormal_releases_and_orphans_are_report_only(self):
        self.api.releases[1]["assets"].append({**self.api.releases[1]["assets"][0], "id": 999, "name": "extra.zip"})
        self.api.releases[2]["draft"] = True
        self.api.releases[3]["published_at"] = None
        del self.api.tags["v0.2.24"]
        rows = self.rows()
        for tag in ("v0.2.20", "v0.2.22", "v0.2.23", "v0.2.24"):
            self.assertEqual(rows[tag]["status"], "skip")
        self.assertEqual([item["name"] for item in self.plan()["orphan_tags"]], ["0.2.10"])
        self.assertFalse(cleanup.version("0.2.10"))
        self.assertFalse(cleanup.version("v3.0.0"))

    def test_plan_round_trip_microseconds_tampering_and_expiry(self):
        plan = cleanup.make_plan(self.config, self.parameters, self.api.inventory(), self.protection(), self.origin,
                                 NOW + timedelta(microseconds=123456))
        cleanup.validate_plan(json.loads(json.dumps(plan)), self.config, NOW + timedelta(seconds=1))
        changed = copy.deepcopy(plan)
        changed["targets"].append(changed["targets"][0])
        with self.assertRaises(cleanup.CleanupError):
            cleanup.validate_plan(changed, self.config, NOW)
        changed["plan_sha256"] = cleanup.digest({key: value for key, value in changed.items() if key != "plan_sha256"})
        with self.assertRaises(cleanup.CleanupError):
            cleanup.validate_plan(changed, self.config, NOW)
        with self.assertRaises(cleanup.CleanupError):
            cleanup.validate_plan(plan, self.config, NOW + timedelta(hours=24))
        changed_config = copy.deepcopy(self.config)
        changed_config["pinned_tags"].append("v0.2.20")
        with self.assertRaises(cleanup.CleanupError):
            cleanup.validate_plan(plan, changed_config, NOW)

    def execute(self, plan, result, policy=POLICY):
        protection_reader = cleanup.collect_protection
        with patch.object(cleanup, "collect_inventory", side_effect=lambda api: api.inventory()), \
             patch.object(cleanup, "collect_protection", side_effect=lambda api, config, inventory: protection_reader(api, config, inventory, policy_reader=lambda url: policy)), \
             patch.object(cleanup, "now_utc", return_value=NOW):
            cleanup.execute_targets(self.api, self.config, plan, result, lambda: None)

    def test_execution_skips_changed_assets_and_never_adds_targets(self):
        plan = self.plan()
        self.api.releases[1]["assets"][0]["size"] += 1
        result = []
        self.execute(plan, result)
        self.assertEqual(result[0]["status"], "skipped_changed_or_retained")
        deleted_ids = {value for kind, value in self.api.calls if kind == "release"}
        planned_ids = {item["release"]["id"] for item in plan["targets"]}
        self.assertTrue(deleted_ids < planned_ids)
        self.assertTrue(all(value in planned_ids for value in deleted_ids))
        self.assertIn("0.2.10", self.api.tags)

    def test_live_floor_recheck_prevents_over_deletion(self):
        plan = self.plan()
        for release_id in (2, 3, 4, 5):
            del self.api.releases[release_id]
        result = []
        self.execute(plan, result)
        remaining = [item for item in self.api.releases.values() if item["tag_name"].startswith("v0.2.") and not item["prerelease"]]
        self.assertEqual(len(remaining), 3)
        self.assertTrue(all(item["tag_name"] in ("v0.2.26", "v0.2.27", "v0.2.28") for item in remaining))

    def test_partial_failure_stops_and_same_plan_resumes(self):
        plan = self.plan()
        self.api.fail_tag = True
        result = []
        with self.assertRaises(cleanup.CleanupError):
            self.execute(plan, result)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["release_deleted"])
        self.assertEqual(result[0]["status"], "failed_after_release_delete")
        self.assertIn("v0.2.20", self.api.tags)
        self.api.fail_tag = False
        result = []
        self.execute(plan, result)
        self.assertNotIn("v0.2.20", self.api.tags)
        self.assertEqual(sum(item == ("release", 1) for item in self.api.calls), 1)
        result = []
        self.execute(plan, result)
        self.assertTrue(all(item["status"] == "already_absent" for item in result))

    def test_changed_tag_new_policy_and_timeouts_stop(self):
        plan = self.plan()
        self.api.tags["v0.2.20"]["sha"] = "d" * 40
        result = []
        self.execute(plan, result)
        self.assertEqual(result[0]["status"], "skipped_changed_or_retained")
        # Required protection failures cannot turn into an empty protected set.
        with patch.object(cleanup, "collect_inventory", side_effect=lambda api: api.inventory()), \
             patch.object(cleanup, "collect_protection", side_effect=cleanup.CleanupError("TimeoutError")), \
             patch.object(cleanup, "now_utc", return_value=NOW):
            self.api.calls.clear()
            with self.assertRaises(cleanup.CleanupError):
                cleanup.execute_targets(self.api, self.config, plan, [], lambda: None)
        self.assertEqual(self.api.calls, [])
        with self.assertRaises(cleanup.CleanupError):
            cleanup.policy_tags({**POLICY, "download_url": "https://example.com/v2.0.2"})

    def test_new_protection_and_republished_tag_are_not_deleted(self):
        plan = self.plan()
        result = []
        self.execute(plan, result, {**POLICY, "latest_version": "0.2.20",
                                   "download_url": "https://github.com/FeiSiPub/TongWenReleases/releases/tag/v0.2.20"})
        self.assertEqual(result[0]["status"], "skipped_changed_or_retained")
        self.assertIn(1, self.api.releases)
        self.api = FakeGitHub()
        original_delete = self.api.delete_release

        def republish(release_id):
            original_delete(release_id)
            self.api.releases[999] = raw_release("v0.2.20", 999)

        with patch.object(self.api, "delete_release", side_effect=republish):
            with self.assertRaises(cleanup.CleanupError):
                self.execute(plan, [])
        self.assertIn("v0.2.20", self.api.tags)
        self.assertEqual(self.api.calls, [("release", 1)])

    def test_preview_provenance_and_local_delete_guard(self):
        plan = self.plan()
        current = {**self.origin, "run_id": "456"}
        run = {"id": 123, "workflow_id": 1, "path": cleanup.WORKFLOW, "event": "workflow_dispatch",
               "head_sha": self.origin["head_sha"], "head_branch": "main", "status": "completed", "conclusion": "success",
               "run_attempt": 1, "repository": {"full_name": cleanup.REPOSITORY}, "head_repository": {"full_name": cleanup.REPOSITORY}}
        class RunApi:
            def get(self, path):
                if path == "git/ref/heads/main":
                    return {"object": {"sha": "a" * 40}}
                return run if path.startswith("actions/runs/") else {"id": 1}

            def pages(self, path, field):
                return [{"name": cleanup.ARTIFACT, "expired": False, "workflow_run": {"id": 123}}]

        with tempfile.TemporaryDirectory() as temp:
            event = Path(temp) / "event.json"
            event.write_text(json.dumps({"inputs": {"preview_run_id": "123"}}), encoding="utf-8")
            with patch.dict("os.environ", {"GITHUB_EVENT_PATH": str(event)}), patch.object(cleanup, "now_utc", return_value=NOW):
                cleanup.validate_preview_run(RunApi(), plan, "123", current)
                run["head_sha"] = "b" * 40
                with self.assertRaises(cleanup.CleanupError):
                    cleanup.validate_preview_run(RunApi(), plan, "123", current)
                run["head_sha"] = self.origin["head_sha"]
                run["conclusion"] = "failure"
                with self.assertRaises(cleanup.CleanupError):
                    cleanup.validate_preview_run(RunApi(), plan, "123", current)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(cleanup.CleanupError):
                cleanup.action_provenance("execute")

    def test_live_main_change_blocks_old_workflow_rerun(self):
        plan = self.plan()
        with patch.object(self.api, "get", return_value={"object": {"sha": "b" * 40}}), \
             patch.object(cleanup, "now_utc", return_value=NOW):
            with self.assertRaisesRegex(cleanup.CleanupError, "Live main changed"):
                cleanup.verify_execution_window(self.api, plan)
        self.assertEqual(self.api.calls, [])

    def test_workflow_defaults_match_configuration(self):
        # Avoid a YAML dependency just to check these six scalar defaults.
        workflow = (cleanup.ROOT / cleanup.WORKFLOW).read_text(encoding="utf-8")
        for key, expected in self.config["defaults"].items():
            section = re.split(r"\n {6}[a-z_]+:", workflow.split("      " + key + ":\n", 1)[1], maxsplit=1)[0]
            if key == "product_line":
                self.assertIn("default: " + expected, section)
            else:
                self.assertIn("default: '" + str(expected) + "'", section)


if __name__ == "__main__":
    unittest.main()
