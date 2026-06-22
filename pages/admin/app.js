const bridge = window.AstrBotPluginPage;
const titles = { overview: "运行状况", features: "功能开关", tests: "功能测试", risingstones: "石之家", database: "数据库", activity: "活动日志" };
const featureNames = {
  core: ["核心功能", "日历、暖暖、攻略、抽卡和随机工具"],
  party_finder: ["招募板", "招募查询与卡片渲染"],
  market: ["物品与市场", "物品、价格和房屋查询"],
  fflogs: ["FFLogs", "输出分位与角色战绩"],
  risingstones: ["石之家", "帖子、攻略、账号和签到功能"],
  weibo: ["微博", "FF14 官方微博资讯"],
};
const state = { overview: null, features: {} };
const status = document.querySelector("#status");
const $ = (selector) => document.querySelector(selector);

function setStatus(message = "", error = false) { status.textContent = message; status.classList.toggle("error", error); }
function bytes(value) { if (!value) return "0 B"; const units = ["B", "KB", "MB", "GB"]; const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1); return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`; }
function uptime(value) { const hours = Math.floor(value / 3600); const minutes = Math.floor((value % 3600) / 60); return hours ? `${hours} 小时 ${minutes} 分` : `${minutes} 分钟`; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]); }
function activityRows(items) { return items.length ? items.map((item) => `<div class="activity-row"><div><strong>${escapeHtml(item.source)}</strong><p>${escapeHtml(item.detail || item.status)}</p></div><time>${escapeHtml(item.created_at)}</time></div>`).join("") : "<p class=\"subtle\">暂无管理操作记录。</p>"; }

function setView(view) {
  for (const section of document.querySelectorAll(".view")) { const active = section.id === view; section.hidden = !active; section.classList.toggle("active", active); }
  for (const item of document.querySelectorAll(".nav-item")) item.classList.toggle("active", item.dataset.view === view);
  $("#page-title").textContent = titles[view];
  void loadViewData(view);
}

function renderOverview(data) {
  state.overview = data;
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

function renderFeatures(features) {
  state.features = { ...features };
  $("#feature-list").innerHTML = Object.entries(featureNames).map(([key, [title, description]]) => `<article class="feature"><div><strong>${title}</strong><p>${description}</p></div><label class="switch" aria-label="${title}"><input data-feature="${key}" type="checkbox" ${features[key] ? "checked" : ""}/><span></span></label></article>`).join("");
}

async function loadOverview() { const data = await bridge.apiGet("admin/overview"); renderOverview(data); }
async function loadRisingstones() {
  const [owner, accounts] = await Promise.all([bridge.apiGet("admin/risingstones/owner-curl"), bridge.apiGet("admin/risingstones/accounts")]);
  $("#owner-curl-status").textContent = owner.configured ? `已配置 ${owner.summary}` : "未配置";
  $("#owner-curl").value = "";
  $("#risingstones-accounts").innerHTML = accounts.accounts.length ? accounts.accounts.map((row) => `<tr><td>${escapeHtml(row.account)}</td><td>${row.auto_checkin ? "开启" : "关闭"}</td><td>${escapeHtml(row.last_checkin_date || "--")}</td><td>${escapeHtml(row.last_attempt_date || "--")}</td><td>${escapeHtml(row.updated_at)}</td></tr>`).join("") : "<tr><td colspan=\"5\" class=\"subtle\">暂无私聊绑定账号。</td></tr>";
}
async function loadDatabase() { const data = await bridge.apiGet("admin/database/summary"); $("#admin-db-size").textContent = bytes(data.admin.size); $("#admin-db-tables").textContent = `${data.admin.tables.length} 张表`; $("#risingstones-db-size").textContent = bytes(data.risingstones.size); $("#risingstones-db-summary").textContent = `${data.risingstones.accounts} 个账号`; $("#fflogs-tracking-count").textContent = data.fflogs_tracking.count; }
async function loadActivity() { const data = await bridge.apiGet("admin/activity"); $("#activity-list").innerHTML = activityRows(data.activity); }
async function loadViewData(view) {
  const loaders = { risingstones: loadRisingstones, database: loadDatabase, activity: loadActivity };
  const loader = loaders[view];
  if (!loader) return;
  try { await loader(); } catch (error) { setStatus(`${titles[view]}加载失败：${error.message}`, true); }
}

async function runTest(target, button) {
  const output = document.querySelector(`[data-result="${target}"]`); button.disabled = true; output.textContent = "测试中..."; output.classList.remove("error");
  try { const result = await bridge.apiPost(`admin/tests/${target}`, {}); output.textContent = `${result.success ? "成功" : "失败"} | ${result.latency_ms ?? "--"} ms | ${result.message}`; output.classList.toggle("error", !result.success); await loadOverview(); } catch (error) { output.textContent = `测试失败：${error.message}`; output.classList.add("error"); } finally { button.disabled = false; }
}

for (const button of document.querySelectorAll(".nav-item")) button.addEventListener("click", () => setView(button.dataset.view));
for (const button of document.querySelectorAll("[data-goto]")) button.addEventListener("click", () => setView(button.dataset.goto));
$("#refresh").addEventListener("click", async () => { setStatus("正在刷新..."); try { await loadOverview(); setStatus("已刷新。") } catch (error) { setStatus(`刷新失败：${error.message}`, true); } });
$("#save-features").addEventListener("click", async () => { const features = {}; for (const input of document.querySelectorAll("[data-feature]")) features[input.dataset.feature] = input.checked; try { const result = await bridge.apiPost("admin/features", { features }); renderFeatures(result.features); setStatus("功能开关已保存。"); await loadOverview(); } catch (error) { setStatus(`保存失败：${error.message}`, true); } });
for (const button of document.querySelectorAll("[data-test]")) button.addEventListener("click", () => runTest(button.dataset.test, button));
$("#save-owner-curl").addEventListener("click", async () => { const curl = $("#owner-curl").value.trim(); if (!curl) { setStatus("请输入完整 getUserInfo cURL（bash）。", true); return; } try { await bridge.apiPost("admin/risingstones/owner-curl", { curl }); setStatus("主人石之家凭据已保存。", false); await loadRisingstones(); await loadOverview(); } catch (error) { setStatus(`保存失败：${error.message}`, true); } });
$("#backup-db").addEventListener("click", async () => { try { const result = await bridge.apiPost("admin/database/backup", {}); $("#database-result").textContent = `已创建备份：${result.created}`; $("#database-result").classList.remove("error"); await loadActivity(); } catch (error) { $("#database-result").textContent = `备份失败：${error.message}`; $("#database-result").classList.add("error"); } });
$("#clear-cache").addEventListener("click", async () => { if (!window.confirm("确认清理插件图片与响应缓存？此操作不会删除数据库。")) return; try { const result = await bridge.apiPost("admin/database/clear-cache", { confirmed: true }); $("#database-result").textContent = `已清理 ${result.removed} 个缓存文件。`; $("#database-result").classList.remove("error"); await loadOverview(); } catch (error) { $("#database-result").textContent = `清理失败：${error.message}`; $("#database-result").classList.add("error"); } });

await bridge.ready();
try { await loadOverview(); } catch (error) { setStatus(`管理台加载失败：${error.message}`, true); }
