const state = {
  system: null,
  models: [],
  datasets: [],
  currentJobId: null,
};

function setStatusText(text) {
  const el = document.getElementById('device-status');
  if (el) {
    el.textContent = text;
  }
}

function renderCard(title, value, detail, tone = 'neutral') {
  const badgeClass = tone === 'good' ? 'good' : tone === 'warn' ? 'warn' : 'neutral';
  return `
    <div class="card">
      <div class="label">${title}</div>
      <div class="value">${value}</div>
      <div class="meta">
        <span>${detail}</span>
        <span class="badge ${badgeClass}">${tone}</span>
      </div>
    </div>
  `;
}

function renderDashboard(system) {
  const cards = document.getElementById('dashboard-cards');
  const device = system?.device || {};
  const datasetInfo = state.datasets?.items?.[0] || {};
  const trainingStatus = device.cuda_available ? 'GPU ready' : 'CPU fallback';
  cards.innerHTML = [
    renderCard('GPU / device', device.device_name || 'CPU', trainingStatus, device.cuda_available ? 'good' : 'warn'),
    renderCard('Model count', String(state.models.length || 0), 'Pretrained & efficient models', 'neutral'),
    renderCard('Dataset status', datasetInfo.status || 'No dataset', `${datasetInfo.image_count || 0} images`, 'good'),
    renderCard('Training mode', 'Fine-tune / From scratch', 'VisionForge pipeline', 'neutral'),
  ].join('');

  const trainingSummary = document.getElementById('training-summary');
  const activeEpoch = state.currentJobId ? 'Live mode' : 'Ready';
  trainingSummary.innerHTML = `
    <div class="metric-row"><span>Queue</span><strong>${state.currentJobId ? '1 active run' : 'Idle'}</strong></div>
    <div class="metric-row"><span>Epoch</span><strong>${activeEpoch}</strong></div>
    <div class="metric-row"><span>Loss</span><strong>${state.currentJobId ? 'tracking...' : 'n/a'}</strong></div>
    <div class="metric-row"><span>mAP</span><strong>${state.currentJobId ? 'tracking...' : 'n/a'}</strong></div>
  `;

  const systemOverview = document.getElementById('system-overview');
  systemOverview.innerHTML = `
    <div class="metric-row"><span>CUDA</span><strong>${device.cuda_available ? 'Enabled' : 'Disabled'}</strong></div>
    <div class="metric-row"><span>Device</span><strong>${device.device || 'cpu'}</strong></div>
    <div class="metric-row"><span>Driver</span><strong>${device.torch_version || 'unknown'}</strong></div>
    <div class="metric-row"><span>Workspace</span><strong>${system.workspace?.model_dir || 'n/a'}</strong></div>
  `;
}

function renderModels(models) {
  const modelList = document.getElementById('model-list');
  if (!modelList) return;

  modelList.innerHTML = models.map((model) => `
    <div class="item">
      <div class="item-text">
        <strong>${model.name}</strong>
        <span>${model.family} • ${model.size} • ${model.source}</span>
      </div>
      <div class="item-actions">
        <span class="badge ${model.state === 'downloaded' ? 'good' : 'neutral'}">${model.state}</span>
        <button class="primary-button" data-model-id="${model.id}">Download</button>
      </div>
    </div>
  `).join('');

  modelList.querySelectorAll('button[data-model-id]').forEach((button) => {
    button.addEventListener('click', async () => {
      const modelId = button.dataset.modelId;
      try {
        const response = await API.post('/api/models/download', { model_id: modelId });
        const result = response.result || {};
        alert(`Model ready: ${result.model_id} -> ${result.status}`);
        await refreshData();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

function renderDatasets(datasets) {
  const datasetList = document.getElementById('dataset-list');
  if (!datasetList) return;

  const items = datasets.items || [];
  if (!items.length) {
    datasetList.innerHTML = '<p>No datasets detected yet. Add a folder under the data/datasets workspace.</p>';
    return;
  }

  datasetList.innerHTML = items.map((dataset) => `
    <div class="item">
      <div class="item-text">
        <strong>${dataset.dataset_path.split('/').pop() || 'Dataset'}</strong>
        <span>${dataset.image_count} images • ${dataset.class_names.length} classes</span>
      </div>
      <span class="badge ${dataset.status === 'ready' ? 'good' : 'warn'}">${dataset.status}</span>
    </div>
  `).join('');
}

function populateModelSelect(models) {
  const select = document.getElementById('model-select');
  if (!select) return;

  select.innerHTML = models.map((model) => `<option value="${model.id}">${model.name}</option>`).join('');
}

function renderTrainingState(stateData) {
  const container = document.getElementById('training-state');
  if (!container) return;

  if (!stateData || stateData.status === 'not found') {
    container.innerHTML = '<p>No training job is active.</p>';
    return;
  }

  const progress = Number(stateData.progress || 0);
  container.innerHTML = `
    <div class="progress-wrap">
      <div class="metric-row"><span>Status</span><strong>${stateData.status || 'queued'}</strong></div>
      <div class="metric-row"><span>Epoch</span><strong>${stateData.epoch || 0} / ${stateData.total_epochs || 0}</strong></div>
      <div class="metric-row"><span>Train loss</span><strong>${stateData.train_loss || 0}</strong></div>
      <div class="metric-row"><span>val loss</span><strong>${stateData.val_loss || 0}</strong></div>
      <div class="metric-row"><span>mAP</span><strong>${stateData.mAP || 0}</strong></div>
      <div class="progress-bar"><span style="width: ${progress}%"></span></div>
      <div class="metric-row"><span>ETA</span><strong>${stateData.eta || '--'}</strong></div>
    </div>
  `;
}

async function startJob() {
  const model_id = document.getElementById('model-select').value;
  const datasetPath = document.getElementById('dataset-path').value || 'data/datasets';
  const payload = {
    model_id,
    dataset_path: datasetPath,
    mode: document.getElementById('training-mode').value,
    epochs: Number(document.getElementById('epochs').value),
    batch_size: Number(document.getElementById('batch-size').value),
    image_size: Number(document.getElementById('image-size').value),
    learning_rate: Number(document.getElementById('learning-rate').value),
    optimizer: document.getElementById('optimizer').value,
    device: state.system?.device?.device || 'cpu',
  };

  try {
    const response = await startTraining(payload);
    state.currentJobId = response.job_id;
    renderTrainingState(response);
    pollTrainingStatus();
  } catch (error) {
    alert(error.message);
  }
}

async function pollTrainingStatus() {
  if (!state.currentJobId) return;

  try {
    const response = await getTrainingStatus(state.currentJobId);
    renderTrainingState(response);
    if (response.status && response.status !== 'completed' && response.status !== 'failed') {
      setTimeout(pollTrainingStatus, 1200);
    }
  } catch (error) {
    console.error(error);
  }
}

function renderClassFilters() {
  const container = document.getElementById('class-filters');
  if (!container) return;

  const classes = state.datasets?.items?.[0]?.class_names?.length
    ? state.datasets.items[0].class_names
    : ['person', 'vehicle', 'traffic sign', 'face', 'bottle'];

  container.innerHTML = classes.map((label) => `
    <label>
      <span>${label}</span>
      <input type="checkbox" checked />
    </label>
  `).join('');
}

async function runDetection() {
  const selected = [...document.querySelectorAll('#class-filters input:checked')].map((input) => input.parentElement.querySelector('span').textContent);
  const response = await runInference({ classes: selected, confidence: 0.25 });
  const results = document.getElementById('inference-results');
  const detections = (response.result?.detections || []).map((item) => `
    <div class="detection-box">
      <strong>${item.label}</strong>
      <span>Confidence: ${(item.confidence * 100).toFixed(0)}%</span>
    </div>
  `).join('');
  results.innerHTML = detections || '<p>No detections for the selected classes.</p>';
}

async function renderExports() {
  const container = document.getElementById('export-list');
  if (!container) return;

  try {
    const response = await fetchExports();
    const exports = response.items || [];
    container.innerHTML = exports.length
      ? exports.map((item) => `
          <div class="item">
            <div class="item-text">
              <strong>${item.name}</strong>
              <span>${Math.round(item.size / 1024)} KB</span>
            </div>
            <span class="badge good">Saved</span>
          </div>
        `).join('')
      : '<p>No export artifacts yet.</p>';
  } catch (error) {
    container.innerHTML = '<p>Export directory is empty.</p>';
  }
}

async function initializeDatasetWorkspace() {
  if (typeof setupAnnotationWorkspace === 'function') {
    setupAnnotationWorkspace();
  }
}

async function refreshData() {
  try {
    const [systemResponse, modelResponse, datasetResponse] = await Promise.all([
      fetchSystem(),
      fetchModels(),
      fetchDatasets(),
    ]);

    state.system = systemResponse;
    state.models = modelResponse.items || [];
    state.datasets = datasetResponse;

    setStatusText(state.system.device?.status || 'Status ready');
    renderDashboard(state.system);
    renderModels(state.models);
    renderDatasets(state.datasets);
    populateModelSelect(state.models);
    renderClassFilters();

    if (state.currentJobId) {
      const jobStatus = await getTrainingStatus(state.currentJobId);
      renderTrainingState(jobStatus);
    }
  } catch (error) {
    console.error(error);
    setStatusText('API unavailable');
  }
}

function bindControls() {
  document.getElementById('refresh-button')?.addEventListener('click', refreshData);
  document.getElementById('start-training')?.addEventListener('click', startJob);
  document.getElementById('run-inference')?.addEventListener('click', runDetection);
}

async function initApp() {
  bindControls();
  renderExports();
  await refreshData();
}

initApp();
