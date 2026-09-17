const scenario = document.querySelector('#scenario');
const liveJev = document.querySelector('#live-jev');
const runButton = document.querySelector('#run');
const status = document.querySelector('#status');
const goal = document.querySelector('#goal');
const scenarioDescription = document.querySelector('#scenario-description');
const outcome = document.querySelector('#outcome');
const summary = document.querySelector('#summary');
const timeline = document.querySelector('#timeline');
const disagreement = document.querySelector('#disagreement');
let scenarios = [];

const pretty = value => String(value).replaceAll('_', ' ');
const title = value => pretty(value).replace(/\b\w/g, letter => letter.toUpperCase());

function scenarioChanged() {
  const selected = scenarios.find(item => item.id === scenario.value);
  scenarioDescription.textContent = selected?.description || '';
}

async function loadScenarios() {
  const data = await fetch('/api/scenarios').then(response => response.json());
  scenarios = data.scenarios;
  goal.textContent = `Agent goal: ${data.goal}`;
  scenarios.forEach(item => scenario.add(new Option(title(item.id), item.id)));
  const parameters = new URLSearchParams(window.location.search);
  const requestedScenario = parameters.get('scenario');
  scenario.value = scenarios.some(item => item.id === requestedScenario) ? requestedScenario : 'loop';
  liveJev.checked = parameters.get('assurance') === 'live';
  scenarioChanged();
  if (parameters.get('run') === 'true') execute();
}

function describeOutcome(data) {
  const stopped = data.final_policy === 'interrupt';
  const warned = data.final_policy === 'warn';
  const headline = stopped ? 'Agent interrupted' : warned ? 'Agent warning issued' : 'Agent allowed to continue';
  let explanation;
  if (data.deterministic_violations) {
    explanation = `A non-negotiable safety rule was violated. The policy stopped the agent after ${data.events} recorded events.`;
  } else if (data.jev_warnings) {
    explanation = 'No hard rule fired. Agentic Assurance supplied evidence worth surfacing, and the policy applied its configured threshold.';
  } else {
    explanation = 'The agent remained within the configured deterministic safeguards. No intervention was necessary.';
  }
  outcome.className = `outcome ${data.final_policy}`;
  outcome.innerHTML = `<span class="outcome-label">Policy decision</span><h2>${headline}</h2><p>${explanation}</p>`;
  outcome.classList.remove('hidden');
}

function renderSummary(data) {
  const fields = [
    ['Hard-rule violations', data.deterministic_violations, 'A violation always interrupts the agent.'],
    ['Agentic Assurance concerns', data.jev_warnings, 'Signals requiring human attention.'],
    ['Interventions', data.interventions, 'Times the agent was stopped.'],
    ['Events observed', data.events, 'Actions, results, judgments, and decisions.'],
  ];
  summary.replaceChildren(...fields.map(([label, value, help]) => {
    const item = document.createElement('div');
    item.innerHTML = `<span>${label}</span><strong>${value}</strong><small>${help}</small>`;
    return item;
  }));
  summary.classList.remove('hidden');
}

function judgmentLine(judgment) {
  const row = document.createElement('li');
  const confidence = Math.round(judgment.probability * 100);
  row.className = `${judgment.judge} ${judgment.severity}`;
  const source = judgment.judge === 'deterministic' ? 'Hard safeguard' : 'Agentic Assurance';
  const detail = judgment.evidence?.[0] || '';
  row.innerHTML = `<strong>${source}: ${title(judgment.dimension)}</strong><span>${title(judgment.decision)}${judgment.judge === 'jev' ? ` · ${confidence}% confidence` : ''}</span><small>${detail}</small>`;
  return row;
}

function policyExplanation(policy) {
  if (policy.action === 'interrupt') return `The policy stopped the agent because: ${pretty(policy.reason)}.`;
  if (policy.action === 'warn') return `The policy allowed work to continue, but raised a warning: ${pretty(policy.reason)}.`;
  return 'The policy found no configured reason to stop or warn the agent.';
}

function renderTimeline(run) {
  const steps = new Map();
  run.events.forEach(event => {
    if (event.step_id === 0 || event.event_type === 'TASK_COMPLETED') return;
    steps.set(event.step_id, [...(steps.get(event.step_id) || []), event]);
  });
  timeline.replaceChildren(...[...steps.entries()].map(([stepId, events]) => {
    const card = document.createElement('article');
    card.className = 'step-card';
    const call = events.find(event => event.event_type === 'TOOL_CALL');
    const result = events.find(event => event.event_type === 'TOOL_RESULT');
    const judgments = events.filter(event => event.event_type === 'JUDGMENT_EMITTED').map(event => event.payload);
    const policy = events.find(event => event.event_type === 'POLICY_DECIDED')?.payload;
    const interrupted = events.find(event => event.event_type === 'AGENT_INTERRUPTED');
    card.innerHTML = `<p class="step-number">Step ${stepId}</p><h3>${call ? `Agent used ${title(call.payload.tool)}` : 'Run update'}</h3>${result ? `<p class="result"><strong>What it learned:</strong> ${result.payload.result}</p>` : ''}`;
    if (judgments.length) {
      const comparison = document.createElement('section');
      comparison.className = 'comparison';
      const safeguards = judgments.filter(judgment => judgment.judge === 'deterministic');
      const contextual = judgments.filter(judgment => judgment.judge !== 'deterministic');
      comparison.innerHTML = '<div class="comparison-heading"><h4>Hard safeguards</h4><p>Known rules: always enforced.</p></div><div class="comparison-heading"><h4>Agentic Assurance</h4><p>Is this still useful work?</p></div>';
      const safeguardList = document.createElement('ul');
      const contextualList = document.createElement('ul');
      safeguards.filter(judgment => judgment.decision === 'violation').forEach(judgment => safeguardList.append(judgmentLine(judgment)));
      if (!safeguardList.children.length) safeguardList.innerHTML = '<li class="all-clear"><strong>All hard safeguards passed</strong><small>No known limit was broken at this step.</small></li>';
      if (contextual.length) contextual.forEach(judgment => contextualList.append(judgmentLine(judgment)));
      else contextualList.innerHTML = '<li class="all-clear"><strong>Not evaluated in this run</strong><small>Enable live Agentic Assurance to add this signal.</small></li>';
      comparison.append(safeguardList, contextualList);
      card.append(comparison);
    }
    if (policy) {
      const decision = document.createElement('p');
      decision.className = `decision ${policy.action}`;
      decision.innerHTML = `<strong>Decision: ${title(policy.action)}</strong> ${policyExplanation(policy)}`;
      card.append(decision);
    }
    if (interrupted) {
      const note = document.createElement('p');
      note.className = 'interrupted';
      note.textContent = 'The run ended here. The agent cannot continue until an operator intervenes.';
      card.append(note);
    }
    return card;
  }));
}

function renderDisagreement(run) {
  const groups = new Map();
  run.events.filter(event => event.event_type === 'JUDGMENT_EMITTED').forEach(event => {
    groups.set(event.step_id, [...(groups.get(event.step_id) || []), event.payload]);
  });
  const groupsWithBoth = [...groups.entries()].filter(([, findings]) => findings.some(j => j.judge === 'deterministic') && findings.some(j => j.judge === 'jev'));
  if (!groupsWithBoth.length) {
    disagreement.classList.add('hidden');
    return;
  }
  disagreement.innerHTML = '<h2>How the assurance signals compare</h2><p>Hard safeguards answer whether a known guardrail was broken. Agentic Assurance answers whether the behavior appears useful for the goal. A green safeguard does not erase an Agentic Assurance concern.</p>';
  groupsWithBoth.forEach(([step, findings]) => {
    const row = document.createElement('p');
    const hard = findings.filter(j => j.judge === 'deterministic' && j.decision === 'violation').length;
    const jev = findings.filter(j => j.judge === 'jev' && j.severity === 'warning').length;
    row.innerHTML = `<strong>Step ${step}:</strong> ${hard ? `${hard} hard-safeguard violation${hard > 1 ? 's' : ''}` : 'hard safeguards passed'}; ${jev ? `${jev} Agentic Assurance concern${jev > 1 ? 's' : ''}` : 'no Agentic Assurance concerns'}.`;
    disagreement.append(row);
  });
  disagreement.classList.remove('hidden');
}

async function execute() {
  runButton.disabled = true;
  status.textContent = liveJev.checked ? 'Running Agentic Assurance…' : 'Running deterministic assurance…';
  try {
    const response = await fetch(`/api/demo/${encodeURIComponent(scenario.value)}?live_jev=${liveJev.checked}`, {method: 'POST'});
    const body = await response.text();
    const data = body ? JSON.parse(body) : {};
    if (!response.ok) throw new Error(data.detail || `Demo failed (HTTP ${response.status}).`);
    describeOutcome(data.summary);
    renderSummary(data.summary);
    renderTimeline(data.run);
    renderDisagreement(data.run);
    status.textContent = 'Run complete. Start with the policy decision, then read each step for the evidence behind it.';
  } catch (error) {
    status.textContent = `Could not run the demo: ${error.message}`;
  } finally {
    runButton.disabled = false;
  }
}

scenario.addEventListener('change', scenarioChanged);
runButton.addEventListener('click', execute);
loadScenarios().catch(error => status.textContent = `Could not load scenarios: ${error.message}`);
