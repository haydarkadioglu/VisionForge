const annotationState = {
  imageIndex: 0,
  images: [],
  classes: ['person', 'vehicle', 'bottle', 'traffic sign'],
  currentClass: 'person',
  currentBoxes: [],
  drawing: false,
  startX: 0,
  startY: 0,
  selectedBox: null,
  currentImage: null,
  draftBox: null,
};

function getCanvasCoordinates(event) {
  const canvas = document.getElementById('annotation-canvas');
  if (!canvas) return { x: 0, y: 0 };

  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (event.clientX - rect.left) * scaleX;
  const y = (event.clientY - rect.top) * scaleY;
  return { x, y };
}

function renderAnnotationCanvas() {
  const canvas = document.getElementById('annotation-canvas');
  const ctx = canvas?.getContext('2d');
  if (!canvas || !ctx) return;

  if (annotationState.currentImage) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(annotationState.currentImage, 0, 0, canvas.width, canvas.height);
  } else {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#020b13';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  const drawBox = (box, color, label = '') => {
    const normalized = [box.x, box.y, box.width || 0, box.height || 0];
    const x = normalized[0];
    const y = normalized[1];
    const width = normalized[2];
    const height = normalized[3];
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);
    ctx.fillStyle = color;
    ctx.font = '14px sans-serif';
    if (label) {
      ctx.fillText(label, x + 6, y + 18);
    }
  };

  annotationState.currentBoxes.forEach((box, index) => drawBox(box, '#61dafb', `${(box.className || annotationState.currentClass || 'obj')}`));
  if (annotationState.draftBox) {
    drawBox(annotationState.draftBox, '#b977ff', annotationState.currentClass);
  }
}

function setupAnnotationWorkspace() {
  const container = document.getElementById('annotation-workspace');
  if (!container) return;

  container.innerHTML = `
    <div class="annotation-shell">
      <aside class="annotation-sidebar">
        <div class="panel">
          <h3>Dataset project</h3>
          <label>
            Source folder
            <input id="dataset-source-folder" type="text" value="data/datasets/demo_dataset" />
          </label>
          <button class="primary-button" id="scan-dataset-button">Scan folder</button>
        </div>

        <div class="panel">
          <h3>Classes</h3>
          <div id="class-list" class="class-list"></div>
          <input id="new-class-name" type="text" placeholder="Add class" />
          <button class="primary-button" id="add-class-button">Add class</button>
        </div>
      </aside>

      <section class="annotation-canvas-panel">
        <div class="annotation-toolbar">
          <button class="primary-button" id="previous-image">Previous</button>
          <button class="primary-button" id="next-image">Next</button>
          <button class="primary-button" id="save-annotations">Save</button>
        </div>

        <div class="annotation-stage">
          <canvas id="annotation-canvas" width="900" height="560"></canvas>
        </div>
      </section>

      <aside class="annotation-summary">
        <div class="panel">
          <h3>Progress</h3>
          <div id="annotation-progress" class="annotation-progress"></div>
        </div>
        <div class="panel">
          <h3>Augmentation</h3>
          <label><input type="checkbox" checked /> Horizontal flip</label>
          <label><input type="checkbox" /> Vertical flip</label>
          <label>Rotation <input type="number" value="15" /></label>
          <button class="primary-button" id="apply-augmentation">Apply</button>
        </div>
      </aside>
    </div>
  `;

  bindAnnotationControls();
  renderClassList();
  scanDatasetFolder();
}

function bindAnnotationControls() {
  document.getElementById('scan-dataset-button')?.addEventListener('click', scanDatasetFolder);
  document.getElementById('add-class-button')?.addEventListener('click', addClass);
  document.getElementById('next-image')?.addEventListener('click', () => navigateAnnotation(1));
  document.getElementById('previous-image')?.addEventListener('click', () => navigateAnnotation(-1));
  document.getElementById('save-annotations')?.addEventListener('click', saveAnnotations);
  document.getElementById('apply-augmentation')?.addEventListener('click', applyAugmentation);

  const canvas = document.getElementById('annotation-canvas');
  canvas?.addEventListener('mousedown', handleCanvasMouseDown);
  canvas?.addEventListener('mousemove', handleCanvasMouseMove);
  canvas?.addEventListener('mouseup', handleCanvasMouseUp);
  canvas?.addEventListener('mouseleave', handleCanvasMouseUp);
}

async function scanDatasetFolder() {
  const folder = document.getElementById('dataset-source-folder')?.value || 'data/datasets/demo_dataset';
  try {
    const response = await API.post('/api/datasets/scan', { folder_path: folder });
    const images = response.images || [];
    const classNames = response.class_names || [];
    annotationState.images = images;
    annotationState.classes = classNames.length ? classNames : annotationState.classes;
    annotationState.currentClass = annotationState.classes[0] || 'person';
    annotationState.imageIndex = 0;
    renderClassList();
    renderProgress();
    loadImageForAnnotation();
  } catch (error) {
    console.error(error);
  }
}

function renderClassList() {
  const classList = document.getElementById('class-list');
  if (!classList) return;

  classList.innerHTML = annotationState.classes.map((label) => `
    <div class="class-pill ${annotationState.currentClass === label ? 'active' : ''}" data-class="${label}">
      ${label}
    </div>
  `).join('');

  classList.querySelectorAll('.class-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      annotationState.currentClass = pill.dataset.class;
      renderClassList();
    });
  });
}

function addClass() {
  const input = document.getElementById('new-class-name');
  const value = input?.value.trim();
  if (!value) return;
  annotationState.classes.push(value);
  annotationState.currentClass = value;
  input.value = '';
  renderClassList();
}

function renderProgress() {
  const progress = document.getElementById('annotation-progress');
  if (!progress) return;

  const total = annotationState.images.length || 1;
  const current = Math.min(annotationState.imageIndex + 1, total);
  progress.innerHTML = `
    <div class="metric-row"><span>Image</span><strong>${current} / ${total}</strong></div>
    <div class="metric-row"><span>Annotated</span><strong>${annotationState.currentBoxes.length}</strong></div>
    <div class="metric-row"><span>Current class</span><strong>${annotationState.currentClass}</strong></div>
  `;
}

function navigateAnnotation(direction) {
  if (!annotationState.images.length) return;
  annotationState.imageIndex = Math.max(0, Math.min(annotationState.images.length - 1, annotationState.imageIndex + direction));
  annotationState.currentBoxes = [];
  renderProgress();
  loadImageForAnnotation();
}

function loadImageForAnnotation() {
  const canvas = document.getElementById('annotation-canvas');
  if (!canvas || !annotationState.images.length) {
    const ctx = canvas?.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#020b13';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    return;
  }

  const imagePath = annotationState.images[annotationState.imageIndex];
  const img = new Image();
  img.onload = () => {
    annotationState.currentImage = img;
    const maxWidth = 920;
    const maxHeight = 620;
    const ratio = Math.min(maxWidth / img.width, maxHeight / img.height, 1);
    canvas.width = Math.max(320, Math.round(img.width * ratio));
    canvas.height = Math.max(220, Math.round(img.height * ratio));
    annotationState.draftBox = null;
    renderAnnotationCanvas();
    renderProgress();
  };
  img.src = imagePath;
}

function handleCanvasMouseDown(event) {
  if (!annotationState.currentImage) return;
  const { x, y } = getCanvasCoordinates(event);
  annotationState.drawing = true;
  annotationState.startX = x;
  annotationState.startY = y;
  annotationState.draftBox = { x, y, width: 0, height: 0, className: annotationState.currentClass };
  annotationState.selectedBox = null;
}

function handleCanvasMouseMove(event) {
  if (!annotationState.drawing) return;
  const { x, y } = getCanvasCoordinates(event);
  annotationState.draftBox = {
    x: Math.min(annotationState.startX, x),
    y: Math.min(annotationState.startY, y),
    width: Math.abs(x - annotationState.startX),
    height: Math.abs(y - annotationState.startY),
    className: annotationState.currentClass,
  };
  renderAnnotationCanvas();
}

function handleCanvasMouseUp(event) {
  if (!annotationState.drawing) return;
  annotationState.drawing = false;

  const { x, y } = getCanvasCoordinates(event || { clientX: annotationState.startX, clientY: annotationState.startY });
  const box = {
    x: Math.min(annotationState.startX, x),
    y: Math.min(annotationState.startY, y),
    width: Math.abs(x - annotationState.startX),
    height: Math.abs(y - annotationState.startY),
    className: annotationState.currentClass,
  };

  if (box.width > 4 && box.height > 4) {
    annotationState.currentBoxes.push(box);
  }
  annotationState.draftBox = null;
  renderProgress();
  renderAnnotationCanvas();
}

async function saveAnnotations() {
  if (!annotationState.images.length) return;
  const imageName = annotationState.images[annotationState.imageIndex].split('/').pop();
  const response = await API.post('/api/annotations/save', {
    project_dir: 'data/datasets/demo_dataset',
    image_name: imageName,
    annotations: annotationState.currentBoxes,
  });
  alert(response.status || 'Annotations saved');
}

async function applyAugmentation() {
  const payload = {
    horizontal_flip: true,
    vertical_flip: false,
    rotation: 15,
    brightness: 0.1,
    contrast: 0.1,
    noise: 0.02,
    scale: 0.1,
  };
  const response = await API.post('/api/datasets/augment', payload);
  alert(response.status || 'Augmentation configured');
}

window.addEventListener('load', () => {
  setupAnnotationWorkspace();
});
