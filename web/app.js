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
  scenario.value = 'loop';
  scenarioChanged();
}

function describeOutcome(data) {
  const stopped = data.final_policy === 'interrupt';
  const warned = data.final_policy === 'warn';
  const headline = stopped ? 'Agent interrupted' : warned ? 'Agent warning issued' : 'Agent allowed to continue';
  let explanation;
  if (data.deterministic_violations) {
    explanation = `A non-negotiable safety rule was violated. The policy stopped the agent after ${data.events} recorded events.`;
  } else if (data.jev_warnings) {
    explanation = 'No hard rule fired. Jev supplied contextual evidence worth surfacing, and the policy applied its configured threshold.';
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
    ['Jev concerns', data.jev_warnings, 'Contextual signals requiring attention.'],
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
  const source = judgment.judge === 'deterministic' ? 'Hard rule' : 'Jev';
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
      const heading = document.createElement('h4');
      heading.textContent = 'Assurance findings';
      const list = document.createElement('ul');
      judgments.forEach(judgment => list.append(judgmentLine(judgment)));
      card.append(heading, list);
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
  disagreement.innerHTML = '<h2>How the judges compare</h2><p>Hard rules answer whether a known guardrail was broken. Jev answers whether the behavior appears contextually useful. A green hard rule does not erase a Jev concern.</p>';
  groupsWithBoth.forEach(([step, findings]) => {
    const row = document.createElement('p');
    const hard = findings.filter(j => j.judge === 'deterministic' && j.decision === 'violation').length;
    const jev = findings.filter(j => j.judge === 'jev' && j.severity === 'warning').length;
    row.innerHTML = `<strong>Step ${step}:</strong> ${hard ? `${hard} hard-rule violation${hard > 1 ? 's' : ''}` : 'hard rules passed'}; ${jev ? `${jev} Jev concern${jev > 1 ? 's' : ''}` : 'no Jev concerns'}.`;
    disagreement.append(row);
  });
  disagreement.classList.remove('hidden');
}

async function execute() {
  runButton.disabled = true;
  status.textContent = liveJev.checked ? 'Asking Jev for contextual evidence…' : 'Running deterministic assurance…';
  try {
    const response = await fetch(`/api/demo/${encodeURIComponent(scenario.value)}?live_jev=${liveJev.checked}`, {method: 'POST'});
    if (!response.ok) throw new Error((await response.json()).detail || 'Demo failed');
    const data = await response.json();
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
