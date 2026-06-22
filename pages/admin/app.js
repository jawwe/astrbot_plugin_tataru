const bridge = window.AstrBotPluginPage;
const titles = {
  overview: "运行状况",
  settings: "插件设置",
  features: "功能开关",
  tests: "功能测试",
  risingstones: "石之家",
  database: "数据库",
  activity: "活动日志",
};
const generalFeatures = {
  help: ["帮帮忙", "显示当前可用命令"],
  precious: ["选门", "藏宝洞左右门选择"],
  lottery: ["仙人彩", "仙人彩号码推荐"],
  calendar: ["日历", "国服与国际服活动日历"],
  nuannuan: ["暖暖", "时尚品鉴作业"],
  dungeon_note: ["攻略", "副本攻略查询"],
  party_finder: ["招募", "国服招募板与卡片渲染"],
  weibo: ["看看微博", "FF14 官方微博资讯"],
  item: ["物品", "物品信息与来源"],
  market: ["价格", "市场板价格查询"],
  house: ["房子 / 房屋", "空房查询"],
  logs_dps: ["输出", "FFLogs 输出分位"],
  character_logs: ["logs", "FFLogs 角色战绩"],
  tarot: ["抽卡", "FF14 塔罗牌"],
};
const risingstonesFeatures = {
  risingstones_content: ["帖子与攻略", "默认内容、帖子和攻略查询"],
  risingstones_recruit: ["公开招募", "副本、萌新、其他和 RP 招募"],
  risingstones_binding: ["账号绑定", "私聊绑定石之家账号"],
  risingstones_profile: ["个人信息", "我的、通知和统计"],
  risingstones_checkin: ["签到", "手动签到和自动签到"],
  risingstones_glamour: ["幻化", "幻化投稿与装备查询"],
  risingstones_guild: ["部队招待", "部队招待查询"],
};
const secretSettings = [
  "proxy_password",
  "weibo_cookie",
  "fflogs_client_id",
  "fflogs_client_secret",
];
const state = { features: {}, clearSecrets: new Set() };
const status = document.querySelector("#status");
const $ = (selector) => document.querySelector(selector);

function setStatus(message = "", error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}

function bytes(value) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function uptime(value) {
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  return hours ? `${hours} 小时 ${minutes} 分` : `${minutes} 分钟`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[char]);
}

function activityRows(items) {
  if (!items.length) return '<p class="subtle">暂无管理操作记录。</p>';
  return items.map((item) => `<div class="activity-row"><div><strong>${escapeHtml(item.source)}</strong><p>${escapeHtml(item.detail || item.status)}</p></div><time>${escapeHtml(item.created_at)}</time></div>`).join("");
}

function setView(view) {
  for (const section of document.querySelectorAll(".view")) {
    const active = section.id === view;
    section.hidden = !active;
    section.classList.toggle("active", active);
  }
  for (const item of document.querySelectorAll(".nav-item")) {
    item.classList.toggle("active", item.dataset.view === view);
  }
  $("#page-title").textContent = titles[view];
  void loadViewData(view);
}

function renderOverview(data) {
  $("#version-badge").textContent = `v${data.version}`;
  $("#uptime").textContent = uptime(data.uptime_seconds);
  $("#risingstones-count").textContent = data.risingstones_accounts;
  $("#auto-checkin-count").textContent = `${data.auto_checkin_accounts} 个自动签到`;
  $("#cache-size").textContent = bytes(data.cache_size);
  $("#proxy-status").textContent = data.network.proxy_enabled ? "已启用" : "直连";
  $("#proxy-detail").textContent = data.network.proxy_error || (data.network.proxy_enabled ? "代理配置有效" : "未使用代理");

  const taskNames = { calendar: "日历更新", risingstones_checkin: "石之家自动签到" };
  $("#task-list").innerHTML = Object.entries(taskNames).map(([key, label]) => `<div class="status-row"><span class="row-label">${label}</span><span class="state ${data.tasks[key] ? "" : "offline"}">${data.tasks[key] ? "运行中" : "未运行"}</span></div>`).join("");

  const sourceNames = { fflogs_configured: "FFLogs API", risingstones_owner_configured: "石之家主人登录态", weibo_cookie_configured: "微博 Cookie" };
  $("#source-list").innerHTML = Object.entries(sourceNames).map(([key, label]) => `<div class="status-row"><span class="row-label">${label}</span><span class="state ${data.sources[key] ? "" : "offline"}">${data.sources[key] ? "已配置" : "未配置"}</span></div>`).join("");
  $("#overview-activity").innerHTML = activityRows(data.activity);
  renderFeatures(data.feature_flags);
}

function renderFeatureList(container, definitions, flags) {
  $(container).innerHTML = Object.entries(definitions).map(([key, [title, description]]) => `<article class="feature"><div><strong>${title}</strong><p>${description}</p></div><label class="switch" aria-label="${title}"><input data-feature="${key}" type="checkbox" ${flags[key] ? "checked" : ""}/><span></span></label></article>`).join("");
}

function renderFeatures(flags) {
  state.features = { ...flags };
  renderFeatureList("#feature-list", generalFeatures, flags);
  renderFeatureList("#risingstones-feature-list", risingstonesFeatures, flags);
}

function setSecretStatus(key, configured) {
  const statusNode = $(`#config-${key.replaceAll("_", "-")}-status`);
  if (statusNode) statusNode.textContent = configured ? "已配置，留空将保持不变" : "未配置";
}

function renderClearSecretButton(button) {
  const pending = state.clearSecrets.has(button.dataset.secret);
  button.textContent = pending ? "将于保存时清除" : `清除已保存${button.dataset.secret === "proxy_password" ? "密码" : "凭据"}`;
  button.classList.toggle("pending-clear", pending);
}

function renderSettings(settings) {
  $("#config-debug-mode").checked = settings.debug_mode;
  $("#config-proxy-enabled").checked = settings.proxy_enabled;
  $("#config-global-calendar").checked = settings.use_global_calendar;
  $("#config-global-fflogs").checked = settings.use_global_fflogs;
  $("#config-proxy-host").value = settings.proxy_host;
  $("#config-proxy-port").value = settings.proxy_port;
  $("#config-proxy-username").value = settings.proxy_username;
  $("#config-font-path").value = settings.font_path;
  $("#config-ffxiv-icon-font-path").value = settings.ffxiv_icon_font_path;
  $("#config-risingstones-checkin-hour").value = settings.risingstones_checkin_hour;
  for (const key of secretSettings) setSecretStatus(key, settings[`${key}_set`]);
  for (const button of document.querySelectorAll(".clear-secret")) renderClearSecretButton(button);
}

async function loadOverview() {
  renderOverview(await bridge.apiGet("admin/overview"));
}

async function loadSettings() {
  const data = await bridge.apiGet("admin/settings");
  renderSettings(data.settings);
}

async function loadRisingstones() {
  const [owner, accounts] = await Promise.all([bridge.apiGet("admin/risingstones/owner-curl"), bridge.apiGet("admin/risingstones/accounts")]);
  $("#owner-curl-status").textContent = owner.configured ? `已配置 ${owner.summary}` : "未配置";
  $("#owner-curl").value = "";
  $("#risingstones-accounts").innerHTML = accounts.accounts.length ? accounts.accounts.map((row) => `<tr><td>${escapeHtml(row.account)}</td><td>${row.auto_checkin ? "开启" : "关闭"}</td><td>${escapeHtml(row.last_checkin_date || "--")}</td><td>${escapeHtml(row.last_attempt_date || "--")}</td><td>${escapeHtml(row.updated_at)}</td></tr>`).join("") : '<tr><td colspan="5" class="subtle">暂无私聊绑定账号。</td></tr>';
}

async function loadDatabase() {
  const data = await bridge.apiGet("admin/database/summary");
  $("#admin-db-size").textContent = bytes(data.admin.size);
  $("#admin-db-tables").textContent = `${data.admin.tables.length} 张表`;
  $("#risingstones-db-size").textContent = bytes(data.risingstones.size);
  $("#risingstones-db-summary").textContent = `${data.risingstones.accounts} 个账号`;
  $("#fflogs-tracking-count").textContent = data.fflogs_tracking.count;
}

async function loadActivity() {
  const data = await bridge.apiGet("admin/activity");
  $("#activity-list").innerHTML = activityRows(data.activity);
}

async function loadViewData(view) {
  const loaders = {
    settings: loadSettings,
    risingstones: async () => Promise.all([loadSettings(), loadRisingstones()]),
    database: loadDatabase,
    activity: loadActivity,
  };
  const loader = loaders[view];
  if (!loader) return;
  try {
    await loader();
  } catch (error) {
    setStatus(`${titles[view]}加载失败：${error.message}`, true);
  }
}

function collectFeatureFlags(container) {
  return Object.fromEntries(Array.from($(container).querySelectorAll("[data-feature]")).map((input) => [input.dataset.feature, input.checked]));
}

async function saveFeatureFlags(container, successMessage) {
  try {
    const result = await bridge.apiPost("admin/features", { features: collectFeatureFlags(container) });
    renderFeatures(result.features);
    setStatus(successMessage);
    await loadOverview();
  } catch (error) {
    setStatus(`保存失败：${error.message}`, true);
  }
}

function collectPluginSettings() {
  const settings = {
    debug_mode: $("#config-debug-mode").checked,
    proxy_enabled: $("#config-proxy-enabled").checked,
    use_global_calendar: $("#config-global-calendar").checked,
    use_global_fflogs: $("#config-global-fflogs").checked,
    proxy_host: $("#config-proxy-host").value.trim(),
    proxy_port: Number($("#config-proxy-port").value || 0),
    proxy_username: $("#config-proxy-username").value.trim(),
    font_path: $("#config-font-path").value.trim(),
    ffxiv_icon_font_path: $("#config-ffxiv-icon-font-path").value.trim(),
  };
  for (const key of secretSettings) {
    const input = $(`#config-${key.replaceAll("_", "-")}`);
    settings[key] = input.value;
  }
  return settings;
}

async function savePluginSettings(settings, successMessage) {
  const result = await bridge.apiPost("admin/settings", {
    settings,
    clear_secrets: [...state.clearSecrets],
  });
  state.clearSecrets.clear();
  renderSettings(result.settings);
  setStatus(successMessage);
  await loadOverview();
}

async function runTest(target, button) {
  const output = document.querySelector(`[data-result="${target}"]`);
  button.disabled = true;
  output.textContent = "测试中...";
  output.classList.remove("error");
  try {
    const result = await bridge.apiPost(`admin/tests/${target}`, {});
    output.textContent = `${result.success ? "成功" : "失败"} | ${result.latency_ms ?? "--"} ms | ${result.message}`;
    output.classList.toggle("error", !result.success);
    await loadOverview();
  } catch (error) {
    output.textContent = `测试失败：${error.message}`;
    output.classList.add("error");
  } finally {
    button.disabled = false;
  }
}

for (const button of document.querySelectorAll(".nav-item")) button.addEventListener("click", () => setView(button.dataset.view));
for (const button of document.querySelectorAll("[data-goto]")) button.addEventListener("click", () => setView(button.dataset.goto));
$("#refresh").addEventListener("click", async () => {
  setStatus("正在刷新...");
  try { await loadOverview(); setStatus("已刷新。"); } catch (error) { setStatus(`刷新失败：${error.message}`, true); }
});
$("#settings-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await savePluginSettings(collectPluginSettings(), "插件设置已保存。"); } catch (error) { $("#settings-result").textContent = `保存失败：${error.message}`; $("#settings-result").classList.add("error"); }
});
for (const button of document.querySelectorAll(".clear-secret")) button.addEventListener("click", () => {
  const key = button.dataset.secret;
  if (state.clearSecrets.has(key)) state.clearSecrets.delete(key); else state.clearSecrets.add(key);
  renderClearSecretButton(button);
});
$("#save-features").addEventListener("click", () => saveFeatureFlags("#feature-list", "功能开关已保存。"));
$("#save-risingstones-features").addEventListener("click", () => saveFeatureFlags("#risingstones-feature-list", "石之家开关已保存。"));
$("#save-risingstones-hour").addEventListener("click", async () => {
  try { await savePluginSettings({ risingstones_checkin_hour: Number($("#config-risingstones-checkin-hour").value) }, "石之家自动签到时点已保存。"); } catch (error) { setStatus(`保存失败：${error.message}`, true); }
});
for (const button of document.querySelectorAll("[data-test]")) button.addEventListener("click", () => runTest(button.dataset.test, button));
$("#save-owner-curl").addEventListener("click", async () => {
  const curl = $("#owner-curl").value.trim();
  if (!curl) { setStatus("请输入完整 getUserInfo cURL（bash）。", true); return; }
  try { await bridge.apiPost("admin/risingstones/owner-curl", { curl }); setStatus("主人石之家凭据已保存。"); await loadRisingstones(); await loadOverview(); } catch (error) { setStatus(`保存失败：${error.message}`, true); }
});
$("#backup-db").addEventListener("click", async () => {
  try { const result = await bridge.apiPost("admin/database/backup", {}); $("#database-result").textContent = `已创建备份：${result.created}`; $("#database-result").classList.remove("error"); await loadActivity(); } catch (error) { $("#database-result").textContent = `备份失败：${error.message}`; $("#database-result").classList.add("error"); }
});
$("#clear-cache").addEventListener("click", async () => {
  if (!window.confirm("确认清理插件图片与响应缓存？此操作不会删除数据库。")) return;
  try { const result = await bridge.apiPost("admin/database/clear-cache", { confirmed: true }); $("#database-result").textContent = `已清理 ${result.removed} 个缓存文件。`; $("#database-result").classList.remove("error"); await loadOverview(); } catch (error) { $("#database-result").textContent = `清理失败：${error.message}`; $("#database-result").classList.add("error"); }
});

await bridge.ready();
try { await loadOverview(); } catch (error) { setStatus(`管理台加载失败：${error.message}`, true); }
