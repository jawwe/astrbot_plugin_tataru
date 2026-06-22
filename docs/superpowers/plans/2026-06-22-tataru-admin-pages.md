# Tataru Admin Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AstrBot Plugin Pages for operating, testing, and safely administering the Tataru plugin.

**Architecture:** Keep all page assets under `pages/admin/` and expose a small authenticated plugin Web API namespace through `Context.register_web_api`. Store page-only settings, telemetry, and future FFLogs tracking rows in a plugin-private SQLite database; preserve the existing Rising Stones account database and expose it only through masked aggregate/read APIs. The page is a single operational shell with client-side navigation so metrics, tests, and sensitive configuration never depend on public HTTP endpoints.

**Tech Stack:** AstrBot Plugin Pages, `AstrBotPluginPage` bridge, Python 3.12, `sqlite3`, `asyncio`, vanilla HTML/CSS/JavaScript, `pytest`, Ruff.

---

### Task 1: Page infrastructure and private admin store

**Files:**
- Create: `pages/admin/index.html`
- Create: `pages/admin/app.js`
- Create: `pages/admin/style.css`
- Modify: `main.py`
- Modify: `tests/test_plugin_core.py`

- [ ] **Step 1: Write failing tests for persistent admin settings and masked summaries**

```python
def test_admin_store_persists_feature_flags_and_masks_accounts(plugin_module, tmp_path) -> None:
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    store.set_feature_flags({"fflogs": False, "risingstones": True})
    assert store.get_feature_flags()["fflogs"] is False
    store.record_activity("test", "success", "secret-value")
    assert "secret-value" not in store.recent_activity()[0]["detail"]
```

- [ ] **Step 2: Run the focused test and verify it fails because `PluginAdminStore` is absent**

Run: `uv run --with pytest --with PyYAML --with-requirements requirements.txt python -m pytest tests/test_plugin_core.py::test_admin_store_persists_feature_flags_and_masks_accounts -q`

Expected: failure mentioning `PluginAdminStore`.

- [ ] **Step 3: Implement the store and Web API registration**

```python
context.register_web_api(f"/{PLUGIN_NAME}/admin/overview", self.admin_overview, ["GET"], "Get Tataru admin overview")
context.register_web_api(f"/{PLUGIN_NAME}/admin/features", self.admin_features, ["GET", "POST"], "Get or save feature flags")
```

Create `PluginAdminStore` with tables `admin_settings`, `admin_activity`, and `fflogs_tracking_accounts`; use JSON for feature flags, short masked activity details, and schema migration through `CREATE TABLE IF NOT EXISTS`.

- [ ] **Step 4: Run the focused test and verify it passes**

Run: same command as Step 2.

Expected: `1 passed`.

- [ ] **Step 5: Add the static Page shell**

Create a semantic sidebar and six view sections: `overview`, `features`, `tests`, `risingstones`, `database`, and `activity`. Call `await bridge.ready()` before initial API reads. Do not embed secrets in DOM attributes or browser storage.

- [ ] **Step 6: Run formatting and page asset validation**

Run: `uv run ruff format main.py tests && uv run ruff check main.py tests && uv run --with PyYAML python scripts/validate_plugin_layout.py`

- [ ] **Step 7: Commit the page foundation**

```bash
git add main.py tests/test_plugin_core.py pages/admin docs/superpowers/plans/2026-06-22-tataru-admin-pages.md
git commit -m "feat: add Tataru admin page foundation"
```

### Task 2: Operational overview and feature switches

**Files:**
- Modify: `main.py`
- Modify: `pages/admin/index.html`
- Modify: `pages/admin/app.js`
- Modify: `pages/admin/style.css`
- Modify: `tests/test_plugin_core.py`

- [ ] **Step 1: Write failing tests for overview payload and disabled feature behavior**

```python
def test_feature_flag_blocks_command_group(plugin_module, tmp_path) -> None:
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    store.set_feature_flags({"fflogs": False})
    assert plugin_module.feature_enabled(store, "fflogs") is False

def test_admin_overview_contains_real_runtime_fields(plugin_module, tmp_path) -> None:
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    overview = plugin_module.build_admin_overview(store, version="1.0.25")
    assert {"version", "database", "activity", "tasks"} <= overview.keys()
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `uv run --with pytest --with PyYAML --with-requirements requirements.txt python -m pytest tests/test_plugin_core.py -k "feature_flag or admin_overview" -q`

Expected: failure because the helper functions are absent.

- [ ] **Step 3: Implement feature gates and overview API**

Map commands to groups (`core`, `party_finder`, `market`, `fflogs`, `risingstones`, `weibo`) and return `该功能已在塔塔露管理台中停用。` before source calls when disabled. Overview values must come from plugin task references, account-store counts, SQLite file sizes, cache timestamps, and recent activity only; do not fabricate time-series values.

- [ ] **Step 4: Render the overview and switches**

Use compact status panels, data-source health rows, a recent activity list, and switch controls. Persist switches through `bridge.apiPost("admin/features", payload)`. Keep button dimensions stable and expose pending/error state.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: command from Step 2.

Expected: all selected tests pass.

- [ ] **Step 6: Commit operational controls**

```bash
git add main.py tests/test_plugin_core.py pages/admin
git commit -m "feat: add Tataru admin overview and feature controls"
```

### Task 3: Isolated integration tests and Rising Stones administration

**Files:**
- Modify: `main.py`
- Modify: `pages/admin/index.html`
- Modify: `pages/admin/app.js`
- Modify: `tests/test_plugin_core.py`

- [ ] **Step 1: Write failing tests for safe test results and cURL validation**

```python
def test_admin_test_result_never_returns_credentials(plugin_module) -> None:
    result = plugin_module.sanitize_admin_test_result({"cookie": "abc", "latency_ms": 12})
    assert "cookie" not in result
    assert result["latency_ms"] == 12

def test_owner_curl_test_requires_get_user_info(plugin_module) -> None:
    assert plugin_module.validate_owner_curl_for_admin("curl https://example.test") is False
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `uv run --with pytest --with PyYAML --with-requirements requirements.txt python -m pytest tests/test_plugin_core.py -k "admin_test_result or owner_curl_test" -q`

Expected: failure because the sanitizing and validation helpers are absent.

- [ ] **Step 3: Implement explicit test endpoints**

Register `POST /admin/tests/proxy`, `POST /admin/tests/fflogs`, `POST /admin/tests/risingstones`, and `POST /admin/tests/sources`. Each endpoint returns status, latency, source, and a safe message. It must not mutate configuration, execute check-in, return cURL, return Cookie values, or relay arbitrary URLs.

- [ ] **Step 4: Implement Rising Stones configuration and account endpoints**

Register `GET/POST /admin/risingstones/owner-curl`, `GET /admin/risingstones/accounts`, and `POST /admin/risingstones/validate`. Accept only `getUserInfo` cURL (bash), store the configured credential through the existing owner-configuration mechanism, return masked summaries, and keep per-user account rows masked.

- [ ] **Step 5: Render separate Tests and Rising Stones views**

Use separate test action cards for proxy, FFLogs, source health, and Rising Stones. Put owner cURL configuration, validation, account table, and auto-check-in result history in the Rising Stones view. Require a confirmation dialog before any explicit immediate check-in action; do not add this action in the initial endpoint set.

- [ ] **Step 6: Run focused tests and verify they pass**

Run: command from Step 2.

Expected: all selected tests pass.

- [ ] **Step 7: Commit integrations administration**

```bash
git add main.py tests/test_plugin_core.py pages/admin
git commit -m "feat: add Tataru integration tests and Rising Stones admin"
```

### Task 4: Database visibility, activity log, documentation, and release validation

**Files:**
- Modify: `main.py`
- Modify: `pages/admin/index.html`
- Modify: `pages/admin/app.js`
- Modify: `pages/admin/style.css`
- Modify: `_conf_schema.json`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `metadata.yaml`
- Modify: `tests/test_plugin_core.py`

- [ ] **Step 1: Write failing tests for database summaries and FFLogs tracking schema**

```python
def test_admin_database_summary_reserves_fflogs_tracking(plugin_module, tmp_path) -> None:
    store = plugin_module.PluginAdminStore(tmp_path / "admin.sqlite3")
    store.initialize()
    summary = store.database_summary()
    assert "fflogs_tracking_accounts" in summary["tables"]
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `uv run --with pytest --with PyYAML --with-requirements requirements.txt python -m pytest tests/test_plugin_core.py::test_admin_database_summary_reserves_fflogs_tracking -q`

Expected: failure because the summary API or table is absent.

- [ ] **Step 3: Implement database and activity endpoints**

Register `GET /admin/database/summary`, `POST /admin/database/backup`, `POST /admin/database/clear-cache`, and `GET /admin/activity`. Backups must target the plugin data directory and return a downloadable file reference only through AstrBot's authenticated page bridge. Do not expose direct SQLite paths, raw tables, arbitrary SQL, or credential columns.

- [ ] **Step 4: Render database and activity views**

Show schema version, table row counts, database/cache sizes, reserved FFLogs tracking capacity, masked account counts, backup status, and paginated activity records. Deletion/clear-cache controls require a confirmation dialog and show completion/failure state.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: command from Step 2.

Expected: `1 passed`.

- [ ] **Step 6: Update release metadata and user documentation**

Bump `metadata.yaml` version, add a structured `CHANGELOG.md` entry, explain the Page views and the `risingstones_owner_curl` safety model in `README.md`, and add only any needed non-secret config schema fields.

- [ ] **Step 7: Run full verification**

Run:

```bash
uv run ruff format main.py tests scripts
uv run ruff check main.py tests scripts
uv run --with pytest --with PyYAML --with-requirements requirements.txt python -m pytest -q
uv run --with PyYAML python scripts/validate_plugin_layout.py
uv run --with-requirements requirements.txt python -m py_compile main.py
python -m json.tool _conf_schema.json > $null
git diff --check
```

Expected: Ruff clean, all tests pass, plugin layout succeeds, compilation succeeds, JSON validation succeeds, and no whitespace errors.

- [ ] **Step 8: Commit database, documentation, and release updates**

```bash
git add main.py tests/test_plugin_core.py pages/admin _conf_schema.json README.md CHANGELOG.md metadata.yaml docs/superpowers/plans/2026-06-22-tataru-admin-pages.md
git commit -m "feat: add Tataru plugin admin console"
```

## Review checklist

- [ ] Every requested sidebar view is implemented: overview, feature switches, tests, Rising Stones, database, activity log.
- [ ] Page endpoints are registered through AstrBot and work with the existing `astrbot.api.web`/Quart compatibility pattern.
- [ ] No page endpoint returns or logs Cookie, cURL, Token, password, or raw account IDs.
- [ ] Owner cURL accepts only `getUserInfo` cURL (bash); per-user credentials remain private-chat-only.
- [ ] Database UI has no arbitrary SQL executor and reserves FFLogs tracking storage without claiming tracking is implemented.
- [ ] Overview only shows real runtime state and recorded activity.
- [ ] Version, changelog, README, tests, Ruff, compilation, JSON, and plugin layout are current.
