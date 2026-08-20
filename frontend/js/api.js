const API = {
  async get(path) {
    const response = await fetch(path, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  },

  async post(path, payload) {
    const response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const content = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(content.error || 'Request failed');
    }

    return response.json();
  },
};

async function fetchSystem() {
  return API.get('/api/system');
}

async function fetchModels() {
  return API.get('/api/models');
}

async function fetchDatasets() {
  return API.get('/api/datasets');
}

async function startTraining(config) {
  return API.post('/api/training/start', config);
}

async function getTrainingStatus(jobId) {
  const query = jobId ? `?job_id=${encodeURIComponent(jobId)}` : '';
  return API.get(`/api/training/status${query}`);
}

async function fetchExports() {
  return API.get('/api/export');
}

async function runInference(payload) {
  return API.post('/api/inference', payload);
}
