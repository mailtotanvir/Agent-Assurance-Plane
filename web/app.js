const scenario = document.querySelector('#scenario');
const liveJev = document.querySelector('#live-jev');
const runButton = document.querySelector('#run');
const status = document.querySelector('#status');
const goal = document.querySelector('#goal');
const summary = document.querySelector('#summary');
const timeline = document.querySelector('#timeline');
const disagreement = document.querySelector('#disagreement');

async function loadScenarios() {
  const data = await fetch('/api/scenarios').then(response => response.json());
  goal.textContent = `Goal: ${data.goal}`;
  data.scenarios.forEach(name => scenario.add(new Option(name, name)));
}

function eventView(event) {
  const node = document.querySelector('#event-template').content.cloneNode(true);
  const kind = node.querySelector('.kind');
  kind.textContent = event.event_type.replaceAll('_', ' ');
  kind.classList.add(event.event_type.toLowerCase());
  node.querySelector('strong').textContent = `Step ${event.step_id}`;
  node.querySelector('pre').textContent = JSON.stringify(event.payload, null, 2);
  return node;
}

function renderSummary(data) {
  const fields = [
    ['Events', data.events],
    ['Deterministic violations', data.deterministic_violations],
    ['Jev warnings', data.jev_warnings],
    ['Interventions', data.interventions],
    ['Final policy', data.final_policy],
  ];
  summary.replaceChildren(...fields.map(([label, value]) => {
    const item = document.createElement('div');
    item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    return item;
  }));
  summary.classList.remove('hidden');
}

function renderDisagreement(run) {
  const grouped = new Map();
  run.events.filter(event => event.event_type === 'JUDGMENT_EMITTED').forEach(event => {
    const judgment = event.payload;
    const key = event.step_id;
    grouped.set(key, [...(grouped.get(key) || []), judgment]);
  });
  const possible = [...grouped.values()].filter(group => group.some(j => j.judge === 'deterministic') && group.some(j => j.judge === 'jev'));
  if (!possible.length) {
    disagreement.classList.add('hidden');
    return;
  }
  disagreement.innerHTML = `<h2>Judge comparison</h2><p>Judges remain distinct; the policy does not collapse them into one score.</p>`;
  possible.slice(-3).forEach(group => {
    const row = document.createElement('p');
    row.textContent = group.map(j => `${j.judge}: ${j.dimension} = ${j.decision} (${j.probability.toFixed(2)})`).join(' · ');
    disagreement.append(row);
  });
  disagreement.classList.remove('hidden');
}

async function execute() {
  runButton.disabled = true;
  status.textContent = liveJev.checked ? 'Running with live Jev evidence…' : 'Running deterministic assurance…';
  try {
    const response = await fetch(`/api/demo/${encodeURIComponent(scenario.value)}?live_jev=${liveJev.checked}`, {method: 'POST'});
    if (!response.ok) throw new Error((await response.json()).detail || 'Demo failed');
    const data = await response.json();
    renderSummary(data.summary);
    timeline.replaceChildren(...data.run.events.map(eventView));
    renderDisagreement(data.run);
    status.textContent = `Completed run ${data.run.run_id}.`;
  } catch (error) {
    status.textContent = `Error: ${error.message}`;
  } finally {
    runButton.disabled = false;
  }
}

runButton.addEventListener('click', execute);
loadScenarios().catch(error => status.textContent = `Could not load scenarios: ${error.message}`);
