const state = { agents: [], scenarios: [], runs: [], activeRun: null };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options });
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(payload.detail || payload || `Request failed (${response.status})`);
  return payload;
}
function toast(message) { const el = $('#toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 2800); }
function dateLabel(value) { if (!value) return '—'; return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)); }
function safe(value) { return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char])); }
function severityClass(value) { return ['critical','high','medium','low'].includes(value) ? value : 'low'; }

function navigate(view) {
  $$('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
  $$('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.view === view));
  const labels = { dashboard: 'Overview', agents: 'Agent registry', scenarios: 'Attack scenarios', runs: 'Evaluations' };
  $('#breadcrumb-current').textContent = labels[view] || 'Overview';
  history.replaceState(null, '', `#${view}`);
}
$$('.nav-item').forEach(button => button.addEventListener('click', () => navigate(button.dataset.view)));
$$('[data-navigate]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.navigate)));

async function loadAll() {
  const [overview, scenarios, runs] = await Promise.all([api('/api/overview'), api('/api/scenarios'), api('/api/runs')]);
  state.agents = overview.agents; state.scenarios = scenarios; state.runs = runs;
  $('#stat-agents').textContent = overview.agent_count;
  $('#stat-runs').textContent = overview.run_count;
  $('#stat-score').innerHTML = overview.average_score === null ? '—' : `${overview.average_score}<small>/100</small>`;
  $('#stat-scenarios').textContent = overview.scenario_count;
  renderAgentSelects(); renderAgents(); renderScenarios(); renderRuns(); renderChart(overview.recent_runs);
}
function renderAgentSelects() {
  const options = state.agents.map(agent => `<option value="${agent.id}">${safe(agent.name)} · ${agent.mode}</option>`).join('');
  ['#quick-agent','#modal-agent'].forEach(selector => { const el = $(selector); const previous = el.value; el.innerHTML = options || '<option value="">Create an agent first</option>'; if ([...el.options].some(option => option.value === previous)) el.value = previous; });
}
function renderAgents() {
  const root = $('#agent-grid');
  if (!state.agents.length) { root.innerHTML = '<div class="empty-state">No agent profiles. Create one to begin.</div>'; return; }
  root.innerHTML = state.agents.map(agent => `<article class="agent-card"><div class="agent-card-top"><div class="agent-icon">⌘</div><span class="mode-badge ${agent.mode === 'vulnerable' ? 'vulnerable' : ''}">${agent.mode.toUpperCase()}</span></div><h3>${safe(agent.name)}</h3><p>${safe(agent.description || 'No description provided.')}</p><div class="agent-meta"><span>${safe(agent.provider)}</span><span>${agent.allow_tools ? 'MOCK TOOLS ON' : 'NO TOOLS'}</span></div><div class="card-actions"><button class="button secondary" data-agent-run="${agent.id}">Run assessment →</button></div></article>`).join('');
  $$('[data-agent-run]').forEach(button => button.addEventListener('click', () => { $('#modal-agent').value = button.dataset.agentRun; openRunModal(); }));
}
function renderScenarios() {
  const counts = state.scenarios.reduce((acc, scenario) => (acc[scenario.severity] = (acc[scenario.severity] || 0) + 1, acc), {});
  $('#scenario-summary').innerHTML = `<div class="summary-chip"><strong>${state.scenarios.length}</strong><small>TOTAL SCENARIOS</small></div><div class="summary-chip"><strong>${counts.critical || 0}</strong><small>CRITICAL SEVERITY</small></div><div class="summary-chip"><strong>${counts.high || 0}</strong><small>HIGH SEVERITY</small></div>`;
  $('#scenario-grid').innerHTML = state.scenarios.map(s => `<article class="scenario-card"><div class="scenario-top"><span class="severity ${severityClass(s.severity)}">${safe(s.severity)} severity</span><span class="panel-chip">${safe(s.id.toUpperCase().replaceAll('_',' '))}</span></div><h3>${safe(s.name)}</h3><p>${safe(s.description)}</p><div class="scenario-category">${safe(s.category)}</div></article>`).join('');
  $('#scenario-checks').innerHTML = state.scenarios.map(s => `<label class="scenario-check"><input type="checkbox" name="scenario" value="${safe(s.id)}" checked><span>${safe(s.name)}<small>${safe(s.severity.toUpperCase())} · ${safe(s.category)}</small></span></label>`).join('');
}
function runRow(run, history = false) {
  const scoreClass = run.score < 60 ? 'low' : '';
  return `<tr><td><span class="mono">#${run.id}</span></td><td>${safe(run.agent_name)}</td><td><span class="score-pill ${scoreClass}">${run.score.toFixed(1)} / 100</span></td>${history ? `<td class="blocked">${run.blocked}</td><td class="rate">${run.vulnerable}</td>` : `<td class="rate">${run.attack_success_rate.toFixed(1)}%</td>`}<td>${dateLabel(run.created_at)}</td><td><button class="run-link" data-open-run="${run.id}">DETAILS ↗</button></td></tr>`;
}
function bindRunButtons() { $$('[data-open-run]').forEach(button => button.addEventListener('click', () => openRunResult(Number(button.dataset.openRun)))); }
function renderRuns() {
  $('#recent-runs').innerHTML = state.runs.length ? state.runs.slice(0, 6).map(run => runRow(run)).join('') : '<tr><td colspan="6" class="empty-cell">No evaluations yet. Launch your first assessment.</td></tr>';
  $('#all-runs').innerHTML = state.runs.length ? state.runs.map(run => runRow(run, true)).join('') : '<tr><td colspan="7" class="empty-cell">No evaluations yet.</td></tr>';
  bindRunButtons();
}
function renderChart(runs) {
  const rows = [...runs].reverse();
  if (!rows.length) { $('#score-chart').innerHTML = '<div class="empty-state">Run an evaluation to populate the trend.</div>'; return; }
  const width = 660, height = 152, left = 28, right = 12, top = 12, bottom = 24;
  const x = i => left + (rows.length === 1 ? (width-left-right)/2 : i*(width-left-right)/(rows.length-1));
  const y = score => top + (100-score)*(height-top-bottom)/100;
  const points = rows.map((run,i) => `${x(i)},${y(run.score)}`).join(' ');
  const circles = rows.map((run,i) => `<circle cx="${x(i)}" cy="${y(run.score)}" r="4" fill="#58d6e6" stroke="#0d1726" stroke-width="2"><title>Run #${run.id}: ${run.score}</title></circle>`).join('');
  const labels = rows.map((run,i) => `<text x="${x(i)}" y="${height-4}" fill="#71839d" font-size="9" text-anchor="middle">#${run.id}</text>`).join('');
  const grid = [0,25,50,75,100].map(value => `<line x1="${left}" x2="${width-right}" y1="${y(value)}" y2="${y(value)}" stroke="#23334a" stroke-dasharray="3 5"/><text x="0" y="${y(value)+3}" fill="#657792" font-size="9">${value}</text>`).join('');
  $('#score-chart').innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Security score trend line chart">${grid}<polyline points="${points}" fill="none" stroke="#57d2e4" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>${circles}${labels}</svg>`;
}
function openRunModal() {
  if (!state.agents.length) { toast('Create an agent profile before running an assessment.'); navigate('agents'); return; }
  $('#scenario-checks').querySelectorAll('input').forEach(input => input.checked = true);
  $('#run-modal').classList.remove('hidden');
}
function closeRunModal() { $('#run-modal').classList.add('hidden'); }
$('#quick-run').addEventListener('click', openRunModal); $('#history-run').addEventListener('click', openRunModal);
$('#launch-assessment').addEventListener('click', () => { $('#modal-agent').value = $('#quick-agent').value; openRunModal(); });
$('#close-run').addEventListener('click', closeRunModal); $('#cancel-run').addEventListener('click', closeRunModal);
$('#run-modal').addEventListener('click', e => { if (e.target === $('#run-modal')) closeRunModal(); });
$('#run-form').addEventListener('submit', async event => {
  event.preventDefault();
  const agentId = Number($('#modal-agent').value);
  const scenarioIds = $$('#scenario-checks input:checked').map(input => input.value);
  if (!scenarioIds.length) { toast('Select at least one scenario.'); return; }
  const submit = $('#run-form button[type="submit"]'); submit.disabled = true; submit.textContent = 'Running simulation…';
  try {
    const result = await api('/api/runs', { method: 'POST', body: JSON.stringify({ agent_id: agentId, scenario_ids: scenarioIds }) });
    closeRunModal(); await loadAll(); showResult(result); toast('Evaluation completed and saved.');
  } catch (error) { toast(error.message); }
  finally { submit.disabled = false; submit.innerHTML = 'Execute assessment <span>→</span>'; }
});

function showResult(run) {
  state.activeRun = run;
  const metrics = run.metrics;
  $('#result-title').textContent = `Run #${run.id} · ${run.agent_name}`;
  $('#result-content').innerHTML = `<div class="result-score"><div class="score-number">${run.score.toFixed(1)}<small> / 100</small></div><div><strong>Internal security score</strong><p>${run.vulnerable === 0 ? 'No simulated attack succeeded in this run.' : `${run.vulnerable} simulated attack(s) succeeded. Review remediation guidance below.`}</p></div></div><div class="result-metrics"><div class="result-metric"><small>ATTACK SUCCESS RATE</small><strong>${metrics.attack_success_rate}%</strong></div><div class="result-metric"><small>DEFENSE PASS RATE</small><strong>${metrics.defense_pass_rate}%</strong></div><div class="result-metric"><small>DATA LEAKAGE RATE</small><strong>${metrics.data_leakage_rate}%</strong></div></div><div class="result-list">${run.results.map(r => `<article class="result-item"><div class="result-item-top"><strong>${safe(r.name)} <span style="color:#8293ab;font-weight:400">· ${safe(r.severity)}</span></strong><span class="outcome ${r.outcome.toLowerCase()}">${safe(r.outcome)}</span></div><p>${safe(r.observed_behavior)}</p><p><b>Remediation:</b> ${safe(r.remediation)}</p></article>`).join('')}</div><p style="font-size:9px;color:#71839a;line-height:1.6;margin:12px 0 0">Synthetic simulator result. The score is an internal comparative metric, not an industry certification or proof of real-world security.</p>`;
  $('#result-modal').classList.remove('hidden');
}
async function openRunResult(id) { try { const run = await api(`/api/runs/${id}`); showResult(run); } catch (error) { toast(error.message); } }
$('#close-result').addEventListener('click', () => $('#result-modal').classList.add('hidden'));
$('#done-result').addEventListener('click', () => $('#result-modal').classList.add('hidden'));
$('#result-modal').addEventListener('click', e => { if (e.target === $('#result-modal')) $('#result-modal').classList.add('hidden'); });
$('#download-report').addEventListener('click', async () => {
  if (!state.activeRun) return;
  try { const response = await fetch(`/api/runs/${state.activeRun.id}/report`); if (!response.ok) throw new Error('Could not download report'); const blob = await response.blob(); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `aegis-run-${state.activeRun.id}-report.md`; a.click(); URL.revokeObjectURL(url); }
  catch (error) { toast(error.message); }
});

function showAgentForm(show) { $('#agent-form-wrap').classList.toggle('hidden', !show); if (show) $('#agent-form-wrap').scrollIntoView({ behavior: 'smooth', block: 'center' }); }
$('#show-agent-form').addEventListener('click', () => showAgentForm(true)); $('#hide-agent-form').addEventListener('click', () => showAgentForm(false)); $('#cancel-agent').addEventListener('click', () => showAgentForm(false));
$('#agent-form').addEventListener('submit', async event => {
  event.preventDefault(); const form = new FormData(event.currentTarget);
  const payload = { name: form.get('name'), provider: form.get('provider'), description: form.get('description'), mode: form.get('mode'), allow_tools: form.get('allow_tools') === 'on' };
  try { await api('/api/agents', { method: 'POST', body: JSON.stringify(payload) }); event.currentTarget.reset(); showAgentForm(false); await loadAll(); toast('Agent profile created.'); }
  catch (error) { toast(error.message); }
});

(async function init() {
  try { await loadAll(); const requested = location.hash.replace('#',''); if (['dashboard','agents','scenarios','runs'].includes(requested)) navigate(requested); }
  catch (error) { toast(`Could not load AEGIS: ${error.message}`); console.error(error); }
})();
