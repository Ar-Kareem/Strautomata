// ─── Globals ───
const ANIMATION_NODES_PER_SECOND = 10;
const ANIMATION_INTERVAL = 1000 / ANIMATION_NODES_PER_SECOND;
let rankTopK = 20;
let rankThinkingFilter = 'all'; // 'all' | 'thinking' | 'non-thinking'

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function initPillToggle(container) {
  if (!container) return;
  const slider = container.querySelector('.pill-toggle-slider');
  const btns = container.querySelectorAll('.pill-toggle-btn');
  function positionSlider(activeBtn) {
    slider.style.left = activeBtn.offsetLeft + 'px';
    slider.style.width = activeBtn.offsetWidth + 'px';
  }
  // Initial position (no transition on load)
  const initial = container.querySelector('.pill-toggle-btn.active');
  if (initial) requestAnimationFrame(() => positionSlider(initial));
  container.addEventListener('click', e => {
    const btn = e.target.closest('.pill-toggle-btn');
    if (!btn || btn.classList.contains('active')) return;
    btns.forEach(b => b.classList.toggle('active', b === btn));
    positionSlider(btn);
    container.dispatchEvent(new CustomEvent('pill-change', { detail: btn }));
  });
  // Reposition on resize
  new ResizeObserver(() => {
    const active = container.querySelector('.pill-toggle-btn.active');
    if (active) positionSlider(active);
  }).observe(container);
}

// Lazy-load Three.js + OrbitControls on first 3D toggle
let threeLoaded = (typeof THREE !== 'undefined');
let threeLoadPromise = null;
function ensureThreeJS() {
  if (threeLoaded) return Promise.resolve();
  if (threeLoadPromise) return threeLoadPromise;
  threeLoadPromise = new Promise((resolve, reject) => {
    const moduleScript = document.createElement('script');
    moduleScript.type = 'module';
    moduleScript.src = 'vendor/three/three-global.r183.js';
    moduleScript.onload = () => {
      if (typeof THREE === 'undefined' || typeof THREE.OrbitControls === 'undefined') {
        threeLoadPromise = null;
        reject(new Error('Three.js failed to initialize.'));
        return;
      }
      threeLoaded = true;
      resolve();
    };
    moduleScript.onerror = () => {
      threeLoadPromise = null;
      reject(new Error('Failed to load Three.js assets.'));
    };
    document.head.appendChild(moduleScript);
  });
  return threeLoadPromise;
}

// Graph data cache for lazy-loaded per-word 3D graph payloads
const graphCache = {};    // word -> {nodes, edges, positions_3d, ...}
const graphPromises = {}; // word -> Promise<graph>
let explorerPrefetchToken = 0;
const TAB_ORDER = ['leaderboard', 'explorer', 'failures', 'patterns', 'about'];
const TAB_SET = new Set(TAB_ORDER);
const DEFAULT_TAB = 'leaderboard';
const PAYLOAD_REQUIREMENTS = {
  core: ['metadata', 'models', 'aggregated', 'release_dates'],
  rankings: ['per_word', 'stop_reasons'],
  analysis: ['efficiency'],
  trajectories: [
    'trajectories',
    'sparsity_trajectories',
  ],
  chains: ['chains'],
};
const PAYLOAD_URLS = {
  core: ['data/core'],
  rankings: ['data/rankings'],
  analysis: ['data/analysis'],
  trajectories: ['data/trajectories'],
  chains: ['data/chains'],
};
const loadedPayloads = new Set();
const payloadPromises = {};

let DATA = {};
let modelMap = {};
let activeTab = DEFAULT_TAB;
let isApplyingHistoryState = false;
const METRIC_LABELS = {
  sum_chain_avg: 'Path Length',
  sum_chain_max: 'Path Length (best)',
  sum_sparse_chain_avg: 'Difficulty-Weighted',
};
const SCATTER_LABEL_FONT_SIZE = 9;
const SCATTER_LABEL_FONT_FAMILY = 'Inter, sans-serif';
const SCATTER_LABEL_MARKER_RADIUS = 5;
const SCATTER_LABEL_PADDING = 2;
const SCATTER_LABEL_COLLISION_GAP = 3;
const SCATTER_LABEL_PRIORITY_WEIGHTS = Object.freeze({
  rank: 0.5,
  frontier: 0.3,
  recency: 0.2,
});
const LOG_SCORE_METRICS = new Set(['sum_chain_avg', 'sum_sparse_chain_avg']);
const SCORE_AXIS_SCALE_STATE = {};
let scatterLabelMeasureContext = null;

function isLogScoreMetric(metricKey) {
  return LOG_SCORE_METRICS.has(metricKey);
}

function getScoreAxisScale(divId) {
  return SCORE_AXIS_SCALE_STATE[divId] === 'log' ? 'log' : 'linear';
}

function setScoreAxisScale(divId, scale) {
  SCORE_AXIS_SCALE_STATE[divId] = scale === 'log' ? 'log' : 'linear';
}

function buildAxisConfig(baseAxis, titleText) {
  return {
    ...baseAxis,
    title: { text: titleText, font: { size: 12 } },
  };
}

function applyScoreAxisType(divId, axisConfig, axisKey, scoreAxisKeys) {
  if (scoreAxisKeys.includes(axisKey) && getScoreAxisScale(divId) === 'log') {
    return { ...axisConfig, type: 'log' };
  }
  return axisConfig;
}

function syncPillToggleState(container, activeValue) {
  if (!container) return;
  const buttons = container.querySelectorAll('.pill-toggle-btn');
  buttons.forEach(button => {
    button.classList.toggle('active', button.dataset.scale === activeValue);
  });
  const slider = container.querySelector('.pill-toggle-slider');
  const activeButton = container.querySelector('.pill-toggle-btn.active');
  if (slider && activeButton) {
    requestAnimationFrame(() => {
      slider.style.left = `${activeButton.offsetLeft}px`;
      slider.style.width = `${activeButton.offsetWidth}px`;
    });
  }
}

function applyExternalScoreAxisScale(divId) {
  const plot = document.getElementById(divId);
  const controls = document.getElementById(`${divId}-scale-toggle`);
  if (!plot || !controls) return;
  const axisKeys = JSON.parse(controls.dataset.axisKeys || '[]');
  const updates = {};
  const scale = getScoreAxisScale(divId);
  axisKeys.forEach(axisKey => {
    updates[`${axisKey}.type`] = scale;
  });
  Plotly.relayout(plot, updates);
}

function ensureScoreAxisToggle(divId, axisKeys) {
  const plot = document.getElementById(divId);
  if (!plot) return;

  let controls = document.getElementById(`${divId}-scale-toggle`);
  if (!axisKeys.length) {
    controls?.remove();
    return;
  }

  if (!controls) {
    controls = document.createElement('div');
    controls.id = `${divId}-scale-toggle`;
    controls.className = 'plot-scale-toggle';
    controls.innerHTML = `
      <span class="plot-scale-toggle-label">Score axis</span>
      <div class="pill-toggle" role="group" aria-label="Score axis scale toggle">
        <span class="pill-toggle-slider"></span>
        <button class="pill-toggle-btn" data-scale="linear" type="button">Linear</button>
        <button class="pill-toggle-btn" data-scale="log" type="button">Log</button>
      </div>
    `;
    plot.insertAdjacentElement('afterend', controls);

    const toggle = controls.querySelector('.pill-toggle');
    initPillToggle(toggle);
    toggle?.addEventListener('pill-change', event => {
      setScoreAxisScale(divId, event.detail.dataset.scale);
      syncPillToggleState(toggle, getScoreAxisScale(divId));
      applyExternalScoreAxisScale(divId);
    });
  }

  controls.dataset.axisKeys = JSON.stringify(axisKeys);
  syncPillToggleState(controls.querySelector('.pill-toggle'), getScoreAxisScale(divId));
}

const LEGACY_TAB_MAP = { rankings: 'leaderboard', analysis: 'failures', directional: 'patterns' };
function readURLState() {
  const params = new URLSearchParams(window.location.search);
  const urlWord = params.get('word');
  const rawTab = params.get('tab');
  const tabParam = LEGACY_TAB_MAP[rawTab] || rawTab;
  const tab = urlWord ? 'explorer' : (TAB_SET.has(tabParam) ? tabParam : DEFAULT_TAB);
  const models = (params.get('models') || '')
    .split(',')
    .map(model => model.trim())
    .filter(Boolean);
  return {
    tab,
    models,
    word: urlWord || null,
    view: params.get('view') === '3d' ? '3d' : '2d',
  };
}

const initialURLState = readURLState();

async function fetchJSONAsset(basePath) {
  try {
    const response = await fetch(`${basePath}.json`);
    if (!response.ok) return null;
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function rebuildModelMap() {
  modelMap = {};
  (DATA.models || []).forEach(model => {
    modelMap[model.id] = model;
  });
}

function hasPayloadData(name) {
  const keys = PAYLOAD_REQUIREMENTS[name] || [];
  return keys.every(key => Object.prototype.hasOwnProperty.call(DATA, key));
}

function markLoadedPayloads() {
  Object.keys(PAYLOAD_REQUIREMENTS).forEach(name => {
    if (hasPayloadData(name)) loadedPayloads.add(name);
  });
  if (loadedPayloads.has('core')) rebuildModelMap();
}

function mergeDataPayload(payload) {
  if (!payload) return DATA;
  DATA = { ...DATA, ...payload };
  markLoadedPayloads();
  return DATA;
}

async function ensurePayload(name) {
  if (hasPayloadData(name)) {
    loadedPayloads.add(name);
    return DATA;
  }
  if (payloadPromises[name]) return payloadPromises[name];
  payloadPromises[name] = (async () => {
    const bases = PAYLOAD_URLS[name] || [];
    for (const base of bases) {
      const payload = await fetchJSONAsset(base);
      if (payload) {
        mergeDataPayload(payload);
        return DATA;
      }
    }
    throw new Error(`Failed to load ${name} data.`);
  })().finally(() => {
    delete payloadPromises[name];
  });
  return payloadPromises[name];
}

function getGraph(word) {
  if (graphCache[word]) return Promise.resolve(graphCache[word]);
  if (DATA?.graphs?.[word]) {
    graphCache[word] = DATA.graphs[word];
    return Promise.resolve(DATA.graphs[word]);
  }
  if (graphPromises[word]) return graphPromises[word];
  graphPromises[word] = fetchJSONAsset(`graphs/${word}_3d`)
    .then(graph => {
      if (graph) graphCache[word] = graph;
      return graph;
    })
    .finally(() => {
      delete graphPromises[word];
    });
  return graphPromises[word];
}

function getGraphSync(word) {
  if (graphCache[word]) return graphCache[word];
  if (DATA?.graphs?.[word]) return DATA.graphs[word];
  return null;
}

function getGraph3d(word) {
  const graph = getGraphSync(word);
  if (graph?.positions_3d) {
    return Promise.resolve(graph.positions_3d);
  }
  return getGraph(word).then(loadedGraph => loadedGraph?.positions_3d || null);
}

function buildURLParams() {
  const params = new URLSearchParams();
  params.set('tab', modalState ? 'explorer' : activeTab);
  if (Array.isArray(sharedSelectedModels) && sharedSelectedModels.length) {
    params.set('models', sharedSelectedModels.join(','));
  }
  if (modalState) {
    params.set('word', modalState.word);
    params.set('view', modalState.is3D ? '3d' : '2d');
  }
  return params;
}

function syncURLState(options = {}) {
  if (isApplyingHistoryState) return;
  const query = buildURLParams().toString();
  const nextURL = query ? `${window.location.pathname}?${query}${window.location.hash}` : `${window.location.pathname}${window.location.hash}`;
  history[options.replace ? 'replaceState' : 'pushState'](null, '', nextURL);
}

function createSvgElement(name, attrs = {}) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function createPlayIcon() {
  const svg = createSvgElement('svg', { viewBox: '0 0 24 24', fill: 'currentColor', 'aria-hidden': 'true' });
  svg.appendChild(createSvgElement('polygon', { points: '6,4 20,12 6,20' }));
  return svg;
}

function createPauseIcon() {
  const svg = createSvgElement('svg', { viewBox: '0 0 24 24', fill: 'currentColor', 'aria-hidden': 'true' });
  svg.appendChild(createSvgElement('rect', { x: '6', y: '4', width: '4', height: '16' }));
  svg.appendChild(createSvgElement('rect', { x: '14', y: '4', width: '4', height: '16' }));
  return svg;
}

function createMaximizeIcon() {
  const svg = createSvgElement('svg', {
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': '2',
    'stroke-linecap': 'round',
    'aria-hidden': 'true',
  });
  svg.appendChild(createSvgElement('polyline', { points: '15 3 21 3 21 9' }));
  svg.appendChild(createSvgElement('polyline', { points: '9 21 3 21 3 15' }));
  svg.appendChild(createSvgElement('line', { x1: '21', y1: '3', x2: '14', y2: '10' }));
  svg.appendChild(createSvgElement('line', { x1: '3', y1: '21', x2: '10', y2: '14' }));
  return svg;
}

function setButtonIcon(button, iconFactory) {
  if (!button) return;
  button.replaceChildren(iconFactory());
}

function renderPlotPlaceholder(divId, message, height = 450) {
  const plot = document.getElementById(divId);
  if (!plot) return;
  delete plot._scatterLabelState;
  Plotly.react(plot, [], {
    ...plotlyLayout(),
    height,
    title: {
      text: message,
      font: { size: 14, family: 'Newsreader, Georgia, serif', color: TC.textDim },
    },
  }, PLOTLY_CONFIG);
}

function setExplorerLoadingState(message) {
  const container = document.getElementById('explorer-grid-container');
  if (!container) return;
  const loading = document.createElement('div');
  loading.className = 'loading';
  loading.textContent = message;
  container.replaceChildren(loading);
}

function preloadExplorerCell(word) {
  return Promise.all([
    ensureThreeJS(),
    getGraph(word),
  ]).then(([, graph]) => ({ graph }));
}

function startExplorerPrefetch(words) {
  explorerPrefetchToken += 1;
  const token = explorerPrefetchToken;
  const queue = words.filter(word => !graphCache[word]);
  const concurrency = 3;

  async function worker() {
    while (token === explorerPrefetchToken && queue.length) {
      const word = queue.shift();
      try {
        await preloadExplorerCell(word);
      } catch (_error) {
        // Ignore per-cell prefetch failures; on-demand loading can still retry.
      }
    }
  }

  for (let i = 0; i < concurrency; i += 1) {
    worker();
  }
}

// ─── Theme ───
const LIGHT_COLORS = {
  bg: '#F4F2EC', bgCard: '#ECEAE3', text: '#1A1A1A', textDim: '#6B6560',
  border: '#D4D0C8', canvasBg: '#F4F2EC', canvasEdge: 'rgba(180,175,165,0.3)',
  canvasEdgeModal: 'rgba(180,175,165,0.25)', nodeColor: '#6B9FBF',
  headBorder: '#F4F2EC', labelColor: 'rgba(100,95,85,0.7)',
  hoverStroke: '#1A1A1A', hoverText: '#1A1A1A',
  plotPaper: '#ECEAE3', plotBg: '#F4F2EC', plotGrid: '#D4D0C8', plotFont: '#1A1A1A',
  markerLine: '#F4F2EC', frontierLine: '#B0A898',
  heatScale: [[0, '#EEF3F8'], [0.25, '#A8C8DC'], [0.5, '#5A90B0'], [0.75, '#2E6080'], [1, '#0E3050']],
  threeBg: 0xF4F2EC, threeEdge: 0xB4AFA5,
};
const DARK_COLORS = {
  bg: '#1A1B20', bgCard: '#22232A', text: '#D8D4CC', textDim: '#8A8580',
  border: '#35363E', canvasBg: '#1A1B20', canvasEdge: 'rgba(80,78,90,0.3)',
  canvasEdgeModal: 'rgba(80,78,90,0.25)', nodeColor: '#6B9FBF',
  headBorder: '#1A1B20', labelColor: 'rgba(170,165,155,0.7)',
  hoverStroke: '#D8D4CC', hoverText: '#D8D4CC',
  plotPaper: '#22232A', plotBg: '#1A1B20', plotGrid: '#35363E', plotFont: '#D8D4CC',
  markerLine: '#1A1B20', frontierLine: '#8A7E6E',
  heatScale: [[0, '#1A1B20'], [0.25, '#1E4060'], [0.5, '#2E7898'], [0.75, '#5AACC8'], [1, '#A0D4E8']],
  threeBg: 0x1A1B20, threeEdge: 0x505060,
};
let TC = document.documentElement.dataset.theme === 'dark' ? DARK_COLORS : LIGHT_COLORS;

function isDarkMode() { return document.documentElement.dataset.theme === 'dark'; }
function toggleTheme() {
  const dark = !isDarkMode();
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  TC = dark ? DARK_COLORS : LIGHT_COLORS;
  localStorage.setItem('lisanbench-theme', dark ? 'dark' : 'light');
  if (loadedPayloads.size) refreshAll();
}
function refreshAll() {
  if (hasPayloadData('core')) {
    renderRankings();
    renderLeaderboard();
    renderScoreVsCost();
    renderTimeline();
    renderAnalysisScatters();
  }
  if (hasPayloadData('rankings')) {
    renderStopReasons();
  }
  if (hasPayloadData('analysis')) {
    renderReasoningEfficiency();
  }
  if (hasPayloadData('chains')) {
    renderDrift();
    if (activeTab === 'explorer') renderExplorerGrid();
    if (activeTab === 'patterns') renderDirectionalAnalysis();
  }
  if (modalState) {
    const snapshot = { word: modalState.word };
    closeExplorerModal({ updateHistory: false, restoreFocus: false });
    openExplorerModal(snapshot.word, { view: '3d', updateHistory: false });
  }
  scheduleVisiblePlotlyResize();
}

// ─── Dirty-tab tracking ───
function setActiveTabUI(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.panel').forEach(panel => {
    const isActive = panel.id === `panel-${tabName}`;
    panel.classList.toggle('active', isActive);
    panel.hidden = !isActive;
  });
  syncHeroNavActive(tabName);
}

async function renderTab(tabName) {
  if (tabName === 'leaderboard') return renderLeaderboardTab();
  if (tabName === 'failures') return renderFailuresTab();
  if (tabName === 'patterns') return renderPatternsTab();
  if (tabName === 'explorer') return renderExplorerTab();
  return Promise.resolve();
}

async function activateTab(tabName, options = {}) {
  const normalizedTab = TAB_SET.has(tabName) ? tabName : DEFAULT_TAB;
  setActiveTabUI(normalizedTab);
  if (!options.skipHistory) {
    syncURLState({ replace: options.replaceHistory });
  }
  await renderTab(normalizedTab);
  scheduleVisiblePlotlyResize();
}

function bindApplicationEventListeners() {
  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  window.addEventListener('popstate', () => {
    applyURLState(readURLState(), { replaceHistory: false });
  });
  window.addEventListener('resize', debounce(scheduleVisiblePlotlyResize, 80));
  initModalHandlers();
  initHeroNav();
  // Leaderboard table/chart toggle
  const viewToggle = document.getElementById('leaderboard-view-toggle');
  initPillToggle(viewToggle);
  viewToggle?.addEventListener('pill-change', e => {
    const view = e.detail.dataset.view;
    document.getElementById('leaderboard-view-table').style.display = view === 'table' ? '' : 'none';
    document.getElementById('leaderboard-view-chart').style.display = view === 'chart' ? '' : 'none';
    scheduleVisiblePlotlyResize();
  });
}

function renderLoadError(error) {
  const content = document.querySelector('.content');
  if (!content) return;
  content.textContent = '';
  const msg = document.createElement('div');
  msg.className = 'loading';
  msg.textContent = `Error loading data: ${error}`;
  const btn = document.createElement('button');
  btn.textContent = 'Retry';
  btn.style.cssText = 'margin-top:12px;padding:8px 20px;cursor:pointer;border-radius:6px;border:1px solid var(--border);background:var(--card-bg);color:var(--text);font-size:14px';
  btn.addEventListener('click', () => location.reload());
  msg.appendChild(document.createElement('br'));
  msg.appendChild(btn);
  content.appendChild(msg);
}

async function bootstrap() {
  try {
    await ensurePayload('core');
    init();
  } catch (error) {
    renderLoadError(error);
  }
}

function plotlyLayout() {
  return {
    paper_bgcolor: TC.plotPaper,
    plot_bgcolor: TC.plotBg,
    font: { color: TC.plotFont, family: 'Inter, sans-serif', size: 13 },
    margin: { t: 50, b: 60, l: 60, r: 30 },
    xaxis: { gridcolor: TC.plotGrid, zerolinecolor: TC.plotGrid, gridwidth: 1 },
    yaxis: { gridcolor: TC.plotGrid, zerolinecolor: TC.plotGrid, gridwidth: 1 },
  };
}
const PLOTLY_CONFIG = { responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['lasso2d', 'select2d'] };
let plotlyResizeFrame = null;

function isElementVisible(el) {
  if (!el || el.closest('[hidden]')) return false;
  let node = el;
  while (node && node !== document.body) {
    const style = window.getComputedStyle(node);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    node = node.parentElement;
  }
  return el.offsetWidth > 0 && el.offsetHeight > 0;
}

function resizeVisiblePlotlyPlots() {
  if (typeof Plotly === 'undefined') return;
  const scope = document.querySelector('.panel.active') || document;
  scope.querySelectorAll('[id^="plot-"]').forEach(el => {
    if (!el.data || !isElementVisible(el)) return;
    try {
      Promise.resolve(Plotly.Plots.resize(el)).then(() => {
        if (el._scatterLabelState) scheduleScatterLabelLayout(el);
      });
    } catch (_error) {
      // Ignore transient resize races while plots are re-rendering.
    }
  });
}

function scheduleVisiblePlotlyResize() {
  if (plotlyResizeFrame != null) cancelAnimationFrame(plotlyResizeFrame);
  plotlyResizeFrame = requestAnimationFrame(() => {
    plotlyResizeFrame = requestAnimationFrame(() => {
      plotlyResizeFrame = null;
      resizeVisiblePlotlyPlots();
    });
  });
}

// ─── Searchable Selector Builder ───
function buildSearchableSelector(containerId, items, opts = {}) {
  const container = document.getElementById(containerId);
  if (!container) return null;
  const placeholder = opts.placeholder || 'Search...';
  const compact = opts.compact || false;
  const selector = document.createElement('div');
  selector.className = 'searchable-selector';

  const searchBar = document.createElement('div');
  searchBar.className = 'search-bar';

  const searchIcon = createSvgElement('svg', {
    width: '14',
    height: '14',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': '2',
    'aria-hidden': 'true',
  });
  searchIcon.appendChild(createSvgElement('circle', { cx: '11', cy: '11', r: '8' }));
  searchIcon.appendChild(createSvgElement('path', { d: 'M21 21l-4.35-4.35' }));
  searchBar.appendChild(searchIcon);

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'search-input';
  input.placeholder = placeholder;
  input.setAttribute('aria-label', placeholder);
  input.dataset.for = containerId;
  searchBar.appendChild(input);

  const countEl = document.createElement('span');
  countEl.className = 'search-count';
  countEl.id = `${containerId}-count`;
  searchBar.appendChild(countEl);
  selector.appendChild(searchBar);

  const list = document.createElement('div');
  list.className = `selector-list${compact ? ' compact' : ''}`;
  list.id = `${containerId}-list`;

  items.forEach(item => {
    const label = document.createElement('label');
    label.className = 'selector-item';
    label.dataset.search = (item.label + (item.searchExtra ? ' ' + item.searchExtra : '')).toLowerCase();

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'sel-cb';
    checkbox.value = item.value;
    checkbox.checked = Boolean(item.checked);
    checkbox.dataset.group = containerId;
    label.appendChild(checkbox);

    if (item.color) {
      const swatch = document.createElement('span');
      swatch.className = 'swatch';
      swatch.style.background = item.color;
      label.appendChild(swatch);
    }

    const labelText = document.createElement('span');
    labelText.textContent = item.label;
    label.appendChild(labelText);

    if (item.extra) {
      const extra = document.createElement('span');
      extra.style.color = 'var(--text-light)';
      extra.style.fontSize = '10px';
      extra.textContent = item.extra;
      label.appendChild(extra);
    }

    list.appendChild(label);
  });

  selector.appendChild(list);

  // Collapsible: show chips bar, list hidden by default
  let expanded = false;
  list.classList.add('selector-list-collapsed');

  const chipsBar = document.createElement('div');
  chipsBar.className = 'selector-chips-bar';
  selector.insertBefore(chipsBar, list);

  // Clear all button inside chips bar
  const clearBtn = document.createElement('button');
  clearBtn.className = 'selector-chips-clear';
  clearBtn.type = 'button';
  clearBtn.textContent = 'Clear';
  chipsBar.appendChild(clearBtn);
  clearBtn.addEventListener('click', e => {
    e.stopPropagation();
    container.querySelectorAll('.sel-cb:checked').forEach(cb => cb.checked = false);
    updateCount();
    updateChips();
    if (opts.onchange) opts.onchange(getSearchableSelectorValues(containerId));
  });

  // Expand toggle in search bar
  const expandBtn = document.createElement('button');
  expandBtn.className = 'selector-expand-btn';
  expandBtn.type = 'button';
  expandBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>';
  searchBar.appendChild(expandBtn);

  function setExpanded(state) {
    expanded = state;
    list.classList.toggle('selector-list-collapsed', !expanded);
    expandBtn.classList.toggle('expanded', expanded);
  }
  expandBtn.addEventListener('click', () => setExpanded(!expanded));
  // Expand on search focus, collapse on click outside
  input.addEventListener('focus', () => setExpanded(true));
  document.addEventListener('mousedown', e => {
    if (expanded && !selector.contains(e.target)) setExpanded(false);
  });

  container.replaceChildren(selector);

  const listItems = list.querySelectorAll('.selector-item');

  function updateChips() {
    // Remove old chips (keep clear button)
    chipsBar.querySelectorAll('.selector-chip').forEach(c => c.remove());
    const checked = container.querySelectorAll('.sel-cb:checked');
    const clearBtn = chipsBar.querySelector('.selector-chips-clear');
    clearBtn.style.display = checked.length ? '' : 'none';
    checked.forEach(cb => {
      const item = items.find(i => i.value === cb.value);
      if (!item) return;
      const chip = document.createElement('span');
      chip.className = 'selector-chip';
      if (item.color) chip.style.borderColor = item.color;
      chip.innerHTML = `${item.color ? `<span class="swatch" style="background:${item.color}"></span>` : ''}${item.label}<button type="button" class="selector-chip-x" data-val="${item.value}">&times;</button>`;
      chipsBar.insertBefore(chip, clearBtn);
    });
    // Chip remove handlers
    chipsBar.querySelectorAll('.selector-chip-x').forEach(x => {
      x.addEventListener('click', e => {
        e.stopPropagation();
        const val = x.dataset.val;
        const cb = container.querySelector(`.sel-cb[value="${CSS.escape(val)}"]`);
        if (cb) cb.checked = false;
        updateCount();
        updateChips();
        if (opts.onchange) opts.onchange(getSearchableSelectorValues(containerId));
      });
    });
  }

  function updateCount() {
    const checked = container.querySelectorAll('.sel-cb:checked').length;
    countEl.textContent = `${checked} selected`;
  }
  updateCount();
  updateChips();

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    listItems.forEach(el => {
      el.classList.toggle('hidden', q && !el.dataset.search.includes(q));
    });
  });

  list.addEventListener('change', event => {
    const cb = event.target.closest('.sel-cb');
    if (!cb) return;
      if (opts.maxChecked) {
        const checked = container.querySelectorAll('.sel-cb:checked');
        if (checked.length > opts.maxChecked) { cb.checked = false; return; }
      }
      updateCount();
      updateChips();
      if (opts.onchange) opts.onchange(getSearchableSelectorValues(containerId));
  });
  list.addEventListener('sync', () => { updateCount(); updateChips(); });

  return { updateCount, updateChips };
}

function getSearchableSelectorValues(containerId) {
  return [...document.querySelectorAll(`[data-group="${containerId}"]:checked`)].map(cb => cb.value);
}


function init() {
  if (initialURLState.models.length) {
    sharedSelectedModels = initialURLState.models;
  }


  const topScore = Math.max(...DATA.aggregated.map(d => d.sum_chain_avg));

  const heroModels = document.getElementById('hero-stat-models');
  const heroWords = document.getElementById('hero-stat-words');
  const heroTop = document.getElementById('hero-stat-top');
  if (heroModels) heroModels.textContent = DATA.metadata.num_models;
  if (heroWords) heroWords.textContent = DATA.metadata.num_words;
  if (heroTop) heroTop.textContent = topScore.toFixed(1);

  // Top-K quick-pick buttons (uses module-level rankTopK)

  bindApplicationEventListeners();
  buildTrajectorySelector();
  initExplorer();
  initDirectionalAnalysis();

  // Unified metric toggle: all Average/Weighted toggles on the leaderboard tab stay in sync
  document.querySelectorAll('.leaderboard-metric-toggle').forEach(toggle => {
    initPillToggle(toggle);
    toggle.addEventListener('pill-change', (e) => {
      const metric = e.detail.dataset.metric;
      document.querySelectorAll('.leaderboard-metric-toggle').forEach(other => {
        if (other === toggle) return;
        other.querySelectorAll('.pill-toggle-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.metric === metric);
        });
        const slider = other.querySelector('.pill-toggle-slider');
        const activeBtn = other.querySelector('.pill-toggle-btn.active');
        if (slider && activeBtn) {
          slider.style.left = activeBtn.offsetLeft + 'px';
          slider.style.width = activeBtn.offsetWidth + 'px';
        }
      });
      // Sync leaderboard sort to the selected metric column
      leaderboardSortKey = metric === 'sum_sparse_chain_avg' ? 'weighted' : 'avg';
      leaderboardSortAsc = false;
      renderRankings();
      renderLeaderboard();
      renderScoreVsCost();
      renderTimeline();
      renderAnalysisScatters();
      renderReasoningEfficiency();
    });
  });
  const topkToggle = document.getElementById('rank-topk-toggle');
  initPillToggle(topkToggle);
  topkToggle?.addEventListener('pill-change', e => {
    rankTopK = e.detail.dataset.topk === 'all' ? Infinity : parseInt(e.detail.dataset.topk);
    renderRankings();
    renderLeaderboard();
    renderScoreVsCost();
  });
  const thinkingToggle = document.getElementById('rank-thinking-toggle');
  initPillToggle(thinkingToggle);
  thinkingToggle?.addEventListener('pill-change', e => {
    rankThinkingFilter = e.detail.dataset.thinking;
    renderRankings();
    renderLeaderboard();
    renderScoreVsCost();
    renderTimeline();
    renderAnalysisScatters();
    renderReasoningEfficiency();
  });
  const leaderboardFilter = document.getElementById('leaderboard-filter');
  if (leaderboardFilter) {
    leaderboardFilter.addEventListener('input', debounce(() => { renderLeaderboard(); renderRankings(); renderScoreVsCost(); }, 150));
  }
  const stopSortToggle = document.getElementById('stop-sort-toggle');
  initPillToggle(stopSortToggle);
  stopSortToggle?.addEventListener('pill-change', renderStopReasons);
  const stopTopkToggle = document.getElementById('stop-topk-toggle');
  initPillToggle(stopTopkToggle);
  stopTopkToggle?.addEventListener('pill-change', renderStopReasons);
  const stopViewToggle = document.getElementById('stop-view-toggle');
  initPillToggle(stopViewToggle);
  stopViewToggle?.addEventListener('pill-change', (e) => {
    const view = e.detail.dataset.view;
    document.getElementById('stop-view-table').style.display = view === 'table' ? '' : 'none';
    document.getElementById('stop-view-chart').style.display = view === 'chart' ? '' : 'none';
    renderStopReasons();
    scheduleVisiblePlotlyResize();
  });
  const stopFilter = document.getElementById('stop-filter');
  if (stopFilter) {
    stopFilter.addEventListener('input', debounce(() => { renderStopReasons(); }, 150));
  }
  applyURLState(initialURLState, { replaceHistory: true });
}

bootstrap();

// ─── Leaderboard Table ───
let leaderboardSortKey = 'avg';
let leaderboardSortAsc = false;
const FIXED_TABLE_INDEX_COLUMN_WIDTH = 72;
const FIXED_TABLE_MIN_COLUMN_WIDTH = 140;

function syncFixedTableColumns(table, columnCount) {
  if (!table || !columnCount) return;
  let colgroup = table.querySelector('colgroup');
  if (!colgroup) {
    colgroup = document.createElement('colgroup');
    table.prepend(colgroup);
  }
  if (columnCount === 1) {
    colgroup.innerHTML = '<col style="width:100%">';
    table.style.minWidth = `${FIXED_TABLE_MIN_COLUMN_WIDTH}px`;
    return;
  }
  const remainingColumns = columnCount - 1;
  const remainingColumnWidth = `calc((100% - ${FIXED_TABLE_INDEX_COLUMN_WIDTH}px) / ${remainingColumns})`;
  colgroup.innerHTML = `<col style="width:${FIXED_TABLE_INDEX_COLUMN_WIDTH}px">` +
    Array.from({ length: remainingColumns }, () => `<col style="width:${remainingColumnWidth}">`).join('');
  table.style.minWidth = `${FIXED_TABLE_INDEX_COLUMN_WIDTH + remainingColumns * FIXED_TABLE_MIN_COLUMN_WIDTH}px`;
}

function getFilteredAggregated() {
  if (!DATA.aggregated) return [];
  if (rankThinkingFilter === 'all') return DATA.aggregated;
  const wantThinking = rankThinkingFilter === 'thinking';
  return DATA.aggregated.filter(d => !!(modelMap[d.model]?.thinking) === wantThinking);
}

function renderLeaderboard() {
  const tbody = document.getElementById('leaderboard-body');
  if (!tbody || !DATA.aggregated) return;
  syncFixedTableColumns(document.getElementById('leaderboard-table'), 5);

  const metric = (document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg');
  const topk = rankTopK;
  const filterText = (document.getElementById('leaderboard-filter')?.value || '').toLowerCase();

  // Build the full ranked list — rank based on selected metric, both columns always shown
  const rankedRows = [...getFilteredAggregated()]
    .sort((a, b) => b[metric] - a[metric])
    .map((d, i) => {
      const m = modelMap[d.model] || {};
      return { rank: i + 1, model: d.model, label: m.label || d.model, company: m.company || 'Other', color: m.color || '#8B7355', avg: d.sum_chain_avg, weighted: d.sum_sparse_chain_avg };
    });

  // Filter
  const filtered = filterText
    ? rankedRows.filter(r =>
      r.label.toLowerCase().includes(filterText) ||
      r.company.toLowerCase().includes(filterText) ||
      r.model.toLowerCase().includes(filterText)
    )
    : rankedRows.slice();

  // Sort the full filtered set, then display only the requested window.
  filtered.sort((a, b) => {
    let va, vb;
    if (leaderboardSortKey === 'model') {
      va = a.label.toLowerCase();
      vb = b.label.toLowerCase();
    } else {
      va = a[leaderboardSortKey];
      vb = b[leaderboardSortKey];
    }
    if (leaderboardSortKey === 'rank' || leaderboardSortKey === 'avg' || leaderboardSortKey === 'weighted') {
      return leaderboardSortAsc ? va - vb : vb - va;
    }
    va = String(va).toLowerCase();
    vb = String(vb).toLowerCase();
    return leaderboardSortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
  });

  const visibleRows = filtered.slice(0, topk);

  tbody.innerHTML = '';
  visibleRows.forEach(r => {
    const tr = document.createElement('tr');
    tr.dataset.model = r.model;

    const rankClass = r.rank <= 3 ? ` leaderboard-rank-${r.rank}` : '';
    tr.innerHTML = `
      <td><span class="leaderboard-rank${rankClass}">${r.rank}</span></td>
      <td><span class="leaderboard-model">${r.label}</span></td>
      <td><span class="leaderboard-company"><span class="leaderboard-company-swatch" style="background:${r.color}"></span>${r.company}</span></td>
      <td><span class="leaderboard-score">${r.avg.toFixed(2)}</span></td>
      <td><span class="leaderboard-score">${r.weighted.toFixed(2)}</span></td>
    `;
    tbody.appendChild(tr);
  });

  // Update header sort indicators
  document.querySelectorAll('#leaderboard-table th[data-sort]').forEach(th => {
    th.classList.remove('sorted', 'asc', 'desc');
    if (th.dataset.sort === leaderboardSortKey) {
      th.classList.add('sorted', leaderboardSortAsc ? 'asc' : 'desc');
    }
  });
}

// Leaderboard sort click handler
document.getElementById('leaderboard-table')?.addEventListener('click', e => {
  const th = e.target.closest('th[data-sort]');
  if (th) {
    const key = th.dataset.sort;
    if (leaderboardSortKey === key) {
      leaderboardSortAsc = !leaderboardSortAsc;
    } else {
      leaderboardSortKey = key;
      leaderboardSortAsc = key === 'model' || key === 'company'; // alpha ascending by default
    }
    renderLeaderboard();
    return;
  }

});

// ─── Hero Nav ───
function syncHeroNavActive(tabName) {
  document.querySelectorAll('.hero-nav-card').forEach(card => {
    card.classList.toggle('active', card.dataset.tab === tabName);
  });
}

function initHeroNav() {
  const nav = document.getElementById('hero-nav');
  if (!nav) return;

  nav.addEventListener('click', e => {
    const card = e.target.closest('.hero-nav-card');
    if (!card) return;
    const tab = card.dataset.tab;
    activateTab(tab);
    // Scroll content into view
    const content = document.querySelector('.content');
    if (content) content.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

function getDefaultSharedModelSelection() {
  const sorted = [...(DATA.aggregated || [])].sort((a, b) => b.sum_chain_avg - a.sum_chain_avg);
  const picked = [];
  const seenCompanies = new Set();
  for (const entry of sorted) {
    const company = modelMap[entry.model]?.company || 'Other';
    if (!seenCompanies.has(company)) {
      seenCompanies.add(company);
      picked.push(entry.model);
      if (picked.length >= 3) break;
    }
  }
  return picked;
}

function applySharedModelSelection(values) {
  sharedSelectedModels = values.slice();
  explorerModels = values.slice();
  dirModels = values.slice();
  ['traj-model-selector', 'explorer-model-selector', 'dir-model-selector'].forEach(containerId => {
    if (document.getElementById(containerId)) {
      syncModelSelector(containerId, sharedSelectedModels);
    }
  });
}

function refreshPatternPlots() {
  renderDrift();
  renderDirectionalAnalysis();
}

async function applyURLState(state, options = {}) {
  const nextState = state || readURLState();
  isApplyingHistoryState = true;
  const requestedModels = nextState.models.length ? nextState.models : getDefaultSharedModelSelection();
  applySharedModelSelection(requestedModels);

  const targetTab = nextState.word ? 'explorer' : nextState.tab;
  await activateTab(targetTab, { skipHistory: true, replaceHistory: options.replaceHistory });

  if (nextState.word) {
    try {
      await ensurePayload('chains');
      openExplorerModal(nextState.word, { view: nextState.view, updateHistory: false });
    } catch (_error) {
      setExplorerLoadingState('Unable to restore the requested explorer state.');
    }
  } else if (modalState) {
    closeExplorerModal({ updateHistory: false });
  }

  isApplyingHistoryState = false;
  if (options.replaceHistory) {
    syncURLState({ replace: true });
  }
}

async function renderLeaderboardTab() {
  renderRankings();
  renderLeaderboard();
  renderScoreVsCost();
  renderTimeline();
  renderAnalysisScatters();

  if (hasPayloadData('analysis')) {
    renderReasoningEfficiency();
  } else {
    renderPlotPlaceholder('plot-reasoning-eff', 'Loading reasoning efficiency data...', 550);
    try {
      await ensurePayload('analysis');
      if (activeTab === 'leaderboard') {
        renderReasoningEfficiency();
      }
    } catch (_error) {
      renderPlotPlaceholder('plot-reasoning-eff', 'Unable to load reasoning efficiency data.', 550);
    }
  }
}

async function renderFailuresTab() {
  if (hasPayloadData('rankings')) {
    renderStopReasons();
  } else {
    renderPlotPlaceholder('plot-stop-reasons', 'Loading chain termination data...', 420);
  }

  try {
    if (!hasPayloadData('rankings')) await ensurePayload('rankings');
    if (activeTab === 'failures') renderStopReasons();
  } catch (_error) {
    if (!hasPayloadData('rankings')) {
      renderPlotPlaceholder('plot-stop-reasons', 'Unable to load chain termination data.', 420);
    }
  }
}

async function renderPatternsTab() {
  if (!hasPayloadData('chains')) {
    renderPlotPlaceholder('plot-drift', 'Loading drift data...', 700);
    renderDirectionalLoading('Loading directional chain data...');
  }

  try {
    if (!hasPayloadData('chains')) await ensurePayload('chains');
  } catch (_error) {
    renderPlotPlaceholder('plot-drift', 'Unable to load drift data.', 700);
    renderDirectionalLoading('Unable to load directional analysis data.');
  }

  try {
    if (!hasPayloadData('trajectories')) await ensurePayload('trajectories');
  } catch (_error) {
    // Trajectory payloads are optional for deferred graph-metric experiments.
  }

  if (activeTab === 'patterns' && hasPayloadData('chains')) {
    renderDrift();
    renderDirectionalAnalysis();
  }
}

async function renderExplorerTab() {
  if (!hasPayloadData('chains')) {
    setExplorerLoadingState('Loading explorer chains...');
  }
  try {
    await ensurePayload('chains');
    if (activeTab === 'explorer') {
      renderExplorerGrid();
    }
  } catch (_error) {
    setExplorerLoadingState('Unable to load explorer chains.');
  }
}


// ─── Sparse label helper ───
// The subset-prediction experiment uses this lightweight normalized helper.
// allPoints: [{nx, ny, text, forceLabel?}] where nx/ny are already normalized to [0,1]
// Returns empty strings only for non-priority points too close to a placed label.
function sparseLabels(allPoints, threshold = 0.06) {
  // Place required labels first, then greedily add the highest-scoring remaining points.
  const indexed = allPoints.map((p, i) => ({ i, p }));
  indexed.sort((a, b) => Number(Boolean(b.p.forceLabel)) - Number(Boolean(a.p.forceLabel))
    || (b.p.y ?? 0) - (a.p.y ?? 0));

  const placed = []; // nx, ny of placed labels
  const result = new Array(allPoints.length).fill('');
  const t2 = threshold * threshold;

  for (const { i, p } of indexed) {
    if (p.forceLabel) {
      result[i] = p.text;
      placed.push(p);
      continue;
    }

    let tooClose = false;
    for (const q of placed) {
      const dx = p.nx - q.nx;
      const dy = p.ny - q.ny;
      if (dx * dx + dy * dy < t2) { tooClose = true; break; }
    }
    if (!tooClose) {
      result[i] = p.text;
      placed.push(p);
    }
  }
  return result;
}

function normalizePoints(points) {
  const xs = points.map(p => p.x), ys = points.map(p => p.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const xRange = xMax - xMin || 1, yRange = yMax - yMin || 1;
  return points.map(p => ({ ...p, nx: (p.x - xMin) / xRange, ny: (p.y - yMin) / yRange }));
}

function measureScatterLabel(text) {
  if (!scatterLabelMeasureContext) {
    const canvas = document.createElement('canvas');
    scatterLabelMeasureContext = canvas.getContext('2d');
  }
  if (scatterLabelMeasureContext) {
    scatterLabelMeasureContext.font = `${SCATTER_LABEL_FONT_SIZE}px ${SCATTER_LABEL_FONT_FAMILY}`;
  }
  const metrics = scatterLabelMeasureContext?.measureText(text);
  const measuredWidth = metrics?.width ?? String(text).length * SCATTER_LABEL_FONT_SIZE * 0.55;
  const measuredAscent = metrics?.actualBoundingBoxAscent || SCATTER_LABEL_FONT_SIZE * 0.8;
  const measuredDescent = metrics?.actualBoundingBoxDescent || SCATTER_LABEL_FONT_SIZE * 0.25;
  return {
    width: Math.ceil(measuredWidth) + SCATTER_LABEL_PADDING * 2,
    ascent: Math.ceil(measuredAscent) + SCATTER_LABEL_PADDING,
    descent: Math.ceil(measuredDescent) + SCATTER_LABEL_PADDING,
  };
}

function scatterLabelBox(position, x, y, size) {
  // Mirrors Plotly's scatter text offsets so collision boxes line up with the
  // rendered SVG text instead of relying on a point-distance approximation.
  const markerOffset = SCATTER_LABEL_MARKER_RADIUS / 0.8 + 1;
  const horizontalSign = position.endsWith('left') ? -1 : position.endsWith('right') ? 1 : 0;
  const verticalSign = position.startsWith('top') ? -1 : position.startsWith('bottom') ? 1 : 0;
  const anchorX = x + horizontalSign * markerOffset;
  const baselineY = y
    + SCATTER_LABEL_FONT_SIZE * 0.75
    + verticalSign * markerOffset
    + ((verticalSign - 1) * SCATTER_LABEL_FONT_SIZE) / 2;
  const horizontal = horizontalSign < 0
    ? anchorX - size.width + SCATTER_LABEL_PADDING
    : horizontalSign > 0
      ? anchorX - SCATTER_LABEL_PADDING
      : anchorX - size.width / 2;
  return {
    left: horizontal,
    right: horizontal + size.width,
    top: baselineY - size.ascent,
    bottom: baselineY + size.descent,
  };
}

function scatterBoxesOverlap(left, right, gap = SCATTER_LABEL_COLLISION_GAP) {
  return left.left < right.right + gap
    && left.right + gap > right.left
    && left.top < right.bottom + gap
    && left.bottom + gap > right.top;
}

function scatterBoxTouchesMarker(box, marker) {
  const nearestX = Math.max(box.left, Math.min(marker.x, box.right));
  const nearestY = Math.max(box.top, Math.min(marker.y, box.bottom));
  const dx = marker.x - nearestX;
  const dy = marker.y - nearestY;
  const clearance = SCATTER_LABEL_MARKER_RADIUS + 1;
  return dx * dx + dy * dy < clearance * clearance;
}

function getScatterLabelPositions(point, plotWidth, plotHeight) {
  const preferredVertical = point.y < plotHeight * 0.22 ? 'bottom' : 'top';
  const alternateVertical = preferredVertical === 'top' ? 'bottom' : 'top';
  const preferredHorizontal = point.x < plotWidth / 2 ? 'right' : 'left';
  const alternateHorizontal = preferredHorizontal === 'right' ? 'left' : 'right';
  return [
    `${preferredVertical} center`,
    `middle ${preferredHorizontal}`,
    `${preferredVertical} ${preferredHorizontal}`,
    `${alternateVertical} center`,
    `middle ${alternateHorizontal}`,
    `${alternateVertical} ${preferredHorizontal}`,
    `${preferredVertical} ${alternateHorizontal}`,
    `${alternateVertical} ${alternateHorizontal}`,
  ];
}

function scheduleScatterLabelLayout(plot, retriesRemaining = 3) {
  if (!plot?._scatterLabelState) return;
  if (plot._scatterLabelFrame != null) cancelAnimationFrame(plot._scatterLabelFrame);
  if (plot._scatterLabelRetryTimer != null) {
    clearTimeout(plot._scatterLabelRetryTimer);
    plot._scatterLabelRetryTimer = null;
  }
  plot._scatterLabelFrame = requestAnimationFrame(() => {
    plot._scatterLabelFrame = null;
    const applied = applyScatterLabelLayout(plot);
    if (!applied && retriesRemaining > 0 && plot._scatterLabelState) {
      plot._scatterLabelRetryTimer = setTimeout(() => {
        plot._scatterLabelRetryTimer = null;
        scheduleScatterLabelLayout(plot, retriesRemaining - 1);
      }, 16);
    }
  });
}

function applyScatterLabelLayout(plot) {
  const state = plot?._scatterLabelState;
  const xAxis = plot?._fullLayout?.xaxis;
  const yAxis = plot?._fullLayout?.yaxis;
  if (!state || !xAxis || !yAxis || typeof xAxis.d2p !== 'function' || typeof yAxis.d2p !== 'function') return false;
  if (state.updating) {
    state.pending = true;
    return true;
  }

  const plotWidth = Number(xAxis._length);
  const plotHeight = Number(yAxis._length);
  if (!(plotWidth > 0) || !(plotHeight > 0)) return false;

  const labelsByTrace = state.groups.map(group => new Array(group.points.length).fill(''));
  const positionsByTrace = state.groups.map(group => new Array(group.points.length).fill('top center'));
  const visiblePoints = [];

  state.groups.forEach((group, groupIndex) => {
    const trace = plot.data?.[group.traceIndex];
    if (!trace || trace.visible === false || trace.visible === 'legendonly') return;
    group.points.forEach((point, pointIndex) => {
      let x;
      let y;
      try {
        x = xAxis.d2p(point.x);
        y = yAxis.d2p(point.y);
      } catch (_error) {
        return;
      }
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      if (x < 0 || x > plotWidth || y < 0 || y > plotHeight) return;
      visiblePoints.push({
        ...point,
        x,
        y,
        groupIndex,
        pointIndex,
      });
    });
  });

  const markerPoints = visiblePoints.map(point => ({ x: point.x, y: point.y }));
  const placedBoxes = [];
  visiblePoints
    .sort((left, right) => {
      const leftPriority = Number.isFinite(Number(left.priority)) ? Number(left.priority) : -Infinity;
      const rightPriority = Number.isFinite(Number(right.priority)) ? Number(right.priority) : -Infinity;
      const priorityDifference = rightPriority - leftPriority;
      if (priorityDifference) return priorityDifference;
      return String(left.label).localeCompare(String(right.label));
    })
    .forEach(point => {
      const label = String(point.label || '').trim();
      if (!label) return;
      const size = measureScatterLabel(label);
      const positions = getScatterLabelPositions(point, plotWidth, plotHeight);
      const position = positions.find(candidate => {
        const box = scatterLabelBox(candidate, point.x, point.y, size);
        const fitsPlot = box.left >= 0
          && box.right <= plotWidth
          && box.top >= 0
          && box.bottom <= plotHeight;
        if (!fitsPlot || placedBoxes.some(placed => scatterBoxesOverlap(box, placed))) return false;
        if (markerPoints.some(marker => {
          const isSameMarkerCluster = Math.abs(marker.x - point.x) < 0.5
            && Math.abs(marker.y - point.y) < 0.5;
          return !isSameMarkerCluster && scatterBoxTouchesMarker(box, marker);
        })) return false;
        point._labelBox = box;
        return true;
      });
      if (!position) return;
      labelsByTrace[point.groupIndex][point.pointIndex] = label;
      positionsByTrace[point.groupIndex][point.pointIndex] = position;
      placedBoxes.push(point._labelBox);
    });

  const signature = JSON.stringify([labelsByTrace, positionsByTrace]);
  if (signature === state.signature) return true;
  state.signature = signature;
  state.updating = true;
  Promise.resolve(Plotly.restyle(plot, {
    text: labelsByTrace,
    textposition: positionsByTrace,
  }, state.traceIndexes))
    .then(() => {
      // A full redraw is needed when the initial traces contained only empty
      // text: Plotly updates the data on restyle, but may not create text nodes
      // until the next resize otherwise.
      if (plot._scatterLabelState === state && typeof Plotly.redraw === 'function') {
        return Plotly.redraw(plot);
      }
    })
    .catch(() => {
      state.signature = null;
    })
    .finally(() => {
      if (plot._scatterLabelState !== state) return;
      state.updating = false;
      if (state.pending) {
        state.pending = false;
        scheduleScatterLabelLayout(plot);
      }
    });
  return true;
}

function renderCollisionAwareScatter(divId, traces, layout, groups) {
  const plot = document.getElementById(divId);
  if (!plot) return Promise.resolve();
  const traceIndexes = groups.map(group => group.traceIndex);
  groups.forEach(group => {
    const trace = traces[group.traceIndex];
    trace.text = new Array(group.points.length).fill('');
    trace.textposition = new Array(group.points.length).fill('top center');
    trace.textfont = {
      size: SCATTER_LABEL_FONT_SIZE,
      color: TC.textDim,
      family: SCATTER_LABEL_FONT_FAMILY,
    };
    trace.cliponaxis = false;
  });

  const state = {
    groups,
    traceIndexes,
    signature: null,
    updating: false,
    pending: false,
  };
  plot._scatterLabelState = state;
  return Promise.resolve(Plotly.react(plot, traces, layout, PLOTLY_CONFIG)).then(() => {
    if (plot._scatterLabelState !== state) return;
    if (!plot._scatterLabelEventsBound && typeof plot.on === 'function') {
      plot.on('plotly_relayout', () => scheduleScatterLabelLayout(plot));
      plot.on('plotly_restyle', () => scheduleScatterLabelLayout(plot));
      plot.on('plotly_afterplot', () => scheduleScatterLabelLayout(plot));
      plot._scatterLabelEventsBound = true;
    }
    scheduleScatterLabelLayout(plot);
  });
}

function getParetoFrontier(points, xGoal = 'max', yGoal = 'max') {
  const valid = points.filter(point => Number.isFinite(point.x) && Number.isFinite(point.y));
  const xIsBetter = xGoal === 'min'
    ? (left, right) => left < right
    : (left, right) => left > right;
  const yIsBetter = yGoal === 'min'
    ? (left, right) => left < right
    : (left, right) => left > right;
  const xIsAtLeastAsGood = (left, right) => left === right || xIsBetter(left, right);
  const yIsAtLeastAsGood = (left, right) => left === right || yIsBetter(left, right);

  return valid.filter((point, pointIndex) => !valid.some((candidate, candidateIndex) => (
    candidateIndex !== pointIndex
    && xIsAtLeastAsGood(candidate.x, point.x)
    && yIsAtLeastAsGood(candidate.y, point.y)
    && (xIsBetter(candidate.x, point.x) || yIsBetter(candidate.y, point.y))
  )));
}

function prioritizeScatterLabels(points, frontier = []) {
  const rankPriorities = new Array(points.length).fill(0);
  const ranked = points
    .map((point, index) => ({ index, score: Number(point.rankScore) }))
    .filter(item => Number.isFinite(item.score))
    .sort((left, right) => right.score - left.score);

  for (let start = 0; start < ranked.length;) {
    let end = start + 1;
    while (end < ranked.length && ranked[end].score === ranked[start].score) end += 1;
    const averageRank = (start + end - 1) / 2;
    const percentile = ranked.length > 1 ? 1 - averageRank / (ranked.length - 1) : 1;
    for (let index = start; index < end; index += 1) {
      rankPriorities[ranked[index].index] = percentile;
    }
    start = end;
  }

  const releaseTimes = points.map(point => {
    const date = point.releaseDate || DATA.release_dates?.[point.model];
    const timestamp = date ? new Date(date).getTime() : NaN;
    return Number.isFinite(timestamp) ? timestamp : NaN;
  });
  const validReleaseTimes = releaseTimes.filter(Number.isFinite);
  const oldestRelease = validReleaseTimes.length ? Math.min(...validReleaseTimes) : 0;
  const newestRelease = validReleaseTimes.length ? Math.max(...validReleaseTimes) : 0;
  const releaseRange = newestRelease - oldestRelease;
  const frontierPoints = new Set(frontier);
  const frontierModels = new Set(frontier.map(point => point.model).filter(Boolean));

  points.forEach((point, index) => {
    const recency = Number.isFinite(releaseTimes[index])
      ? (releaseRange > 0 ? (releaseTimes[index] - oldestRelease) / releaseRange : 1)
      : 0;
    const isFrontier = frontierPoints.has(point) || frontierModels.has(point.model);
    point.priority = rankPriorities[index] * SCATTER_LABEL_PRIORITY_WEIGHTS.rank
      + Number(isFrontier) * SCATTER_LABEL_PRIORITY_WEIGHTS.frontier
      + recency * SCATTER_LABEL_PRIORITY_WEIGHTS.recency;
  });
  return points;
}

function getTimelineFrontier(points) {
  // Collapse models released on the same day to that day's best score so the
  // frontier is independent of the source-data ordering.
  const bestByDate = new Map();
  points.forEach(point => {
    if (!point.dateStr || !Number.isFinite(point.y)) return;
    const current = bestByDate.get(point.dateStr);
    if (!current || point.y > current.y) bestByDate.set(point.dateStr, point);
  });

  const chronological = [...bestByDate.values()]
    .sort((a, b) => a.dateStr.localeCompare(b.dateStr));
  const frontier = [];
  let bestScore = -Infinity;
  chronological.forEach(point => {
    if (point.y > bestScore) {
      bestScore = point.y;
      frontier.push(point);
    }
  });
  return frontier;
}

// ─── Rankings ───
function renderRankings() {
  const metric = (document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg');
  const topk = rankTopK;
  const filterText = (document.getElementById('leaderboard-filter')?.value || '').toLowerCase();
  const metricLabel = METRIC_LABELS[metric] || metric;
  const scoreAxisKeys = ['xaxis'];

  let ranked = [...getFilteredAggregated()].sort((a, b) => b[metric] - a[metric]);
  if (filterText) {
    ranked = ranked.filter(d => {
      const m = modelMap[d.model] || {};
      const label = (m.label || d.model).toLowerCase();
      const company = (m.company || '').toLowerCase();
      return label.includes(filterText) || company.includes(filterText) || d.model.toLowerCase().includes(filterText);
    });
  }
  const sorted = ranked.slice(0, topk);

  // Reverse for Plotly bottom-to-top ordering
  const items = [...sorted].reverse();

  const labels = [];
  const values = [];
  const colors = [];
  const companies = [];
  const labelSeen = {};
  items.forEach(d => {
    const m = modelMap[d.model];
    const rawLabel = m?.label || d.model;
    // Plotly merges bars with identical y-labels — append invisible chars to deduplicate
    const count = labelSeen[rawLabel] || 0;
    labelSeen[rawLabel] = count + 1;
    labels.push(count > 0 ? rawLabel + '\u200b'.repeat(count) : rawLabel);
    values.push(d[metric]);
    colors.push(m?.color || '#8B7355');
    companies.push(m?.company || 'Other');
  });

  // Build legend traces (invisible bars, one per company for the legend)
  const seenCompanies = new Map();
  items.forEach(d => {
    const m = modelMap[d.model];
    const company = m?.company || 'Other';
    if (!seenCompanies.has(company)) seenCompanies.set(company, m?.color || '#8B7355');
  });

  const plotHeight = Math.max(500, sorted.length * 26);
  document.getElementById('plot-ranking').style.height = plotHeight + 'px';

  const mainTrace = {
    type: 'bar', orientation: 'h',
    y: labels, x: values,
    marker: { color: colors },
    text: values.map(v => v.toFixed(2)),
    textposition: 'outside', textfont: { size: 11, color: TC.text, family: 'JetBrains Mono, monospace' },
    hovertext: companies,
    hovertemplate: '%{y}<br>%{x:.2f}<br>%{hovertext}<extra></extra>',
    showlegend: false,
  };

  const legendTraces = [...seenCompanies.entries()].map(([company, color]) => ({
    type: 'bar', orientation: 'h',
    y: [null], x: [null],
    name: company,
    marker: { color },
    showlegend: true,
  }));

  Plotly.react('plot-ranking', [mainTrace, ...legendTraces], {
    ...plotlyLayout(),
    title: { text: 'LisanBench Rankings', font: { size: 18, family: 'Newsreader, Georgia, serif' } },
    xaxis: applyScoreAxisType('plot-ranking', buildAxisConfig(plotlyLayout().xaxis, metricLabel), 'xaxis', scoreAxisKeys),
    yaxis: { ...plotlyLayout().yaxis, automargin: true, tickfont: { size: 11 } },
    height: plotHeight,
    margin: { ...plotlyLayout().margin, l: 200 },
    showlegend: true, legend: { font: { size: 11 } },
    barmode: 'overlay',
  }, PLOTLY_CONFIG);
  ensureScoreAxisToggle('plot-ranking', scoreAxisKeys);
}

function formatUsd(value) {
  if (!Number.isFinite(value)) return 'n/a';
  if (value >= 100) return `$${value.toFixed(0)}`;
  if (value >= 10) return `$${value.toFixed(1)}`;
  if (value >= 1) return `$${value.toFixed(2)}`;
  return `$${value.toFixed(3)}`;
}

function renderScoreVsCost() {
  const divId = 'plot-score-vs-cost';
  const container = document.getElementById(divId);
  if (!container || !DATA.aggregated) return;

  const metric = document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg';
  const metricLabel = METRIC_LABELS[metric] || metric;
  const filterText = (document.getElementById('leaderboard-filter')?.value || '').toLowerCase();
  const scoreAxisKeys = ['xaxis'];

  const points = getFilteredAggregated()
    .map(row => {
      const meta = modelMap[row.model] || {};
      const cost = Number(row.estimated_cost_usd ?? meta.estimated_cost_usd);
      const score = Number(row[metric]);
      const inputTokens = Number(row.input_tokens ?? meta.input_tokens ?? 0);
      const outputTokens = Number(row.output_tokens ?? meta.output_tokens ?? 0);
      return {
        x: cost,
        y: score,
        text: meta.label || row.model,
        model: row.model,
        company: meta.company || row.company || 'Other',
        color: meta.color || '#8B7355',
        inputTokens,
        outputTokens,
        score,
        rankScore: score,
        cost,
        costPerKScore: Number.isFinite(cost) && Number.isFinite(score) && score > 0 ? cost / score * 1000 : null,
      };
    })
    .filter(point => {
      if (!Number.isFinite(point.x) || !Number.isFinite(point.y) || point.y <= 0) return false;
      if (!filterText) return true;
      return point.text.toLowerCase().includes(filterText)
        || point.company.toLowerCase().includes(filterText)
        || point.model.toLowerCase().includes(filterText);
    });

  if (!points.length) {
    renderPlotPlaceholder(divId, 'No cost data available for the current filters.', 520);
    return;
  }

  prioritizeScatterLabels(points, getParetoFrontier(points, 'min', 'max'));

  const byCompany = {};
  points.forEach(point => {
    if (!byCompany[point.company]) {
      byCompany[point.company] = {
        x: [],
        y: [],
        text: [],
        labelText: [],
        priorities: [],
        color: point.color,
      };
    }
    byCompany[point.company].x.push(point.x);
    byCompany[point.company].y.push(point.y);
    byCompany[point.company].labelText.push(point.text);
    byCompany[point.company].priorities.push(point.priority);
    byCompany[point.company].text.push(
      `${point.text}<br>${metricLabel}: ${point.score.toFixed(2)}<br>Total cost: ${formatUsd(point.cost)}<br>` +
      `Input tokens: ${point.inputTokens.toLocaleString()}<br>Output tokens: ${point.outputTokens.toLocaleString()}<br>` +
      `Cost / 1k score: ${formatUsd(point.costPerKScore)}`
    );
  });

  const companyEntries = Object.entries(byCompany);
  const traces = companyEntries.map(([name, group]) => ({
    type: 'scatter',
    mode: 'markers+text',
    x: group.x,
    y: group.y,
    name,
    customdata: group.text,
    marker: { color: group.color, size: 10, line: { color: TC.markerLine, width: 1.5 } },
    hovertemplate: '%{customdata}<extra></extra>',
  }));
  const labelGroups = companyEntries.map(([, group], traceIndex) => ({
    traceIndex,
    points: group.x.map((x, pointIndex) => ({
      x,
      y: group.y[pointIndex],
      label: group.labelText[pointIndex],
      priority: group.priorities[pointIndex],
    })),
  }));

  renderCollisionAwareScatter(divId, traces, {
    ...plotlyLayout(),
    title: { text: 'Score vs Total Benchmark Cost', font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: { ...buildAxisConfig(plotlyLayout().xaxis, 'Total benchmark cost (USD)'), type: 'log', tickprefix: '$' },
    yaxis: applyScoreAxisType(divId, buildAxisConfig(plotlyLayout().yaxis, metricLabel), 'yaxis', ['yaxis']),
    showlegend: true,
    legend: { font: { size: 10 } },
    height: 520,
  }, labelGroups);
  ensureScoreAxisToggle(divId, ['yaxis']);
}

// ─── Timeline ───
function renderTimeline() {
  const metric = (document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg');
  const metricLabel = METRIC_LABELS[metric] || metric;
  const scoreAxisKeys = ['yaxis'];

  const agg = getFilteredAggregated();
  const flatTimeline = [];
  agg.forEach(d => {
    const m = modelMap[d.model];
    if (!m) return;
    const dateStr = DATA.release_dates[d.model];
    if (!dateStr) return;
    flatTimeline.push({
      x: new Date(dateStr).getTime(),
      y: d[metric],
      rankScore: Number(d[metric]),
      text: m.label,
      model: d.model,
      dateStr,
      releaseDate: dateStr,
      company: m.company,
      color: m.color,
    });
  });

  const frontier = getTimelineFrontier(flatTimeline);
  const frontierCoordinates = new Set(frontier.map(point => `${point.dateStr}\u0000${point.y}`));
  const timelineFrontierPoints = flatTimeline.filter(point => (
    frontierCoordinates.has(`${point.dateStr}\u0000${point.y}`)
  ));
  prioritizeScatterLabels(flatTimeline, timelineFrontierPoints);

  const byCompany = {};
  flatTimeline.forEach(p => {
    if (!byCompany[p.company]) {
      byCompany[p.company] = {
        x: [],
        y: [],
        text: [],
        labelText: [],
        priorities: [],
        color: p.color,
      };
    }
    byCompany[p.company].x.push(p.dateStr);
    byCompany[p.company].y.push(p.y);
    byCompany[p.company].text.push(p.text);
    byCompany[p.company].labelText.push(p.text);
    byCompany[p.company].priorities.push(p.priority);
  });

  const companyEntries = Object.entries(byCompany);
  const traces = companyEntries.map(([name, d]) => ({
    type: 'scatter', mode: 'markers+text',
    x: d.x, y: d.y,
    name,
    customdata: d.text,
    marker: { color: d.color, size: 10, line: { color: TC.markerLine, width: 1.5 } },
    hovertemplate: `%{customdata}<br>%{x}<br>${metricLabel}: %{y:.2f}<extra></extra>`,
  }));
  const labelGroups = companyEntries.map(([, group], traceIndex) => ({
    traceIndex,
    points: group.x.map((x, pointIndex) => ({
      x,
      y: group.y[pointIndex],
      label: group.labelText[pointIndex],
      priority: group.priorities[pointIndex],
    })),
  }));

  if (frontier.length >= 2) {
    const fx = [], fy = [];
    frontier.forEach((p, i) => {
      fx.push(p.dateStr); fy.push(p.y);
      if (i < frontier.length - 1) { fx.push(frontier[i + 1].dateStr); fy.push(p.y); }
    });
    traces.push({
      type: 'scatter', mode: 'lines', x: fx, y: fy,
      line: { color: TC.frontierLine, dash: 'dash', width: 1.5 },
      showlegend: false, hoverinfo: 'skip',
    });
  }

  renderCollisionAwareScatter('plot-timeline', traces, {
    ...plotlyLayout(),
    title: { text: `${metricLabel} Over Time`, font: { size: 16, family: 'Newsreader, Georgia, serif' } },
    xaxis: { ...plotlyLayout().xaxis, title: { text: 'Release Date', font: { size: 12 } } },
    yaxis: applyScoreAxisType('plot-timeline', buildAxisConfig(plotlyLayout().yaxis, metricLabel), 'yaxis', scoreAxisKeys),
    showlegend: true, legend: { font: { size: 11 } },
  }, labelGroups);
  ensureScoreAxisToggle('plot-timeline', scoreAxisKeys);
}

// ─── Analysis ───
function renderAnalysisScatters() {
  const metric = document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg';
  const mLabel = METRIC_LABELS[metric];
  const agg = getFilteredAggregated();

  if (metric === 'sum_sparse_chain_avg') {
    scatterPlot('plot-score-vs-sparse', agg, metric, 'sum_chain_avg',
      mLabel, 'Path Length', `${mLabel} vs Path Length`);
  } else {
    scatterPlot('plot-score-vs-sparse', agg, metric, 'sum_sparse_chain_avg',
      mLabel, 'Difficulty-Weighted', `${mLabel} vs Difficulty-Weighted`);
  }
  scatterPlot('plot-score-vs-validity', agg, metric, 'avg_validity',
    mLabel, 'Avg Validity Ratio', `${mLabel} vs Validity`);
}

function scatterPlot(divId, data, xKey, yKey, xLabel, yLabel, title) {
  const scoreAxisKeys = [];
  if (isLogScoreMetric(xKey)) scoreAxisKeys.push('xaxis');
  if (isLogScoreMetric(yKey)) scoreAxisKeys.push('yaxis');
  const flat = [];
  data.forEach(d => {
    const m = modelMap[d.model];
    if (!m || d[xKey] == null || d[yKey] == null) return;
    flat.push({
      x: d[xKey],
      y: d[yKey],
      text: m.label,
      model: d.model,
      company: m.company,
      color: m.color,
      rankScore: Number(d[xKey]),
    });
  });
  prioritizeScatterLabels(flat, getParetoFrontier(flat, 'max', 'max'));

  const byCompany = {};
  flat.forEach(p => {
    if (!byCompany[p.company]) {
      byCompany[p.company] = {
        x: [],
        y: [],
        text: [],
        labelText: [],
        priorities: [],
        color: p.color,
      };
    }
    byCompany[p.company].x.push(p.x);
    byCompany[p.company].y.push(p.y);
    byCompany[p.company].text.push(p.text);
    byCompany[p.company].labelText.push(p.text);
    byCompany[p.company].priorities.push(p.priority);
  });

  const companyEntries = Object.entries(byCompany);
  const traces = companyEntries.map(([name, d]) => ({
    type: 'scatter', mode: 'markers+text',
    x: d.x, y: d.y, name,
    customdata: d.text,
    marker: { color: d.color, size: 10, line: { color: TC.markerLine, width: 1.5 } },
    hovertemplate: '%{customdata}<br>' + xLabel + ': %{x:.2f}<br>' + yLabel + ': %{y:.4f}<extra></extra>',
  }));
  const labelGroups = companyEntries.map(([, group], traceIndex) => ({
    traceIndex,
    points: group.x.map((x, pointIndex) => ({
      x,
      y: group.y[pointIndex],
      label: group.labelText[pointIndex],
      priority: group.priorities[pointIndex],
    })),
  }));

  renderCollisionAwareScatter(divId, traces, {
    ...plotlyLayout(),
    title: { text: title, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: applyScoreAxisType(divId, buildAxisConfig(plotlyLayout().xaxis, xLabel), 'xaxis', scoreAxisKeys),
    yaxis: applyScoreAxisType(divId, buildAxisConfig(plotlyLayout().yaxis, yLabel), 'yaxis', scoreAxisKeys),
    showlegend: true, legend: { font: { size: 10 } },
  }, labelGroups);
  ensureScoreAxisToggle(divId, scoreAxisKeys);
}

function formatSubsetMetric(value, digits = 3) {
  return Number.isFinite(value) ? value.toFixed(digits) : '—';
}

function setSubsetPredictionMessage(message) {
  const container = document.getElementById('subset-predictor-summary');
  if (!container) return;
  container.innerHTML = `<div class="subset-predictor-empty">${message}</div>`;
}

function buildSubsetPredictionCard(kicker, title, subset, monteCarlo = null) {
  if (!subset) return '';
  const words = (subset.selected_words || [])
    .map(word => `<span class="subset-predictor-word">${word}</span>`)
    .join('');
  const mcLine = monteCarlo && Number.isFinite(monteCarlo.correlation_mean)
    ? `<div class="subset-predictor-stat"><strong>1-trial MC r ${formatSubsetMetric(monteCarlo.correlation_mean)}</strong>${Number.isFinite(monteCarlo.correlation_std) ? ` +/- ${formatSubsetMetric(monteCarlo.correlation_std)}` : ''} · ${monteCarlo.resamples} resamples</div>`
    : '';
  return `
    <div class="subset-predictor-card">
      <span class="subset-predictor-kicker">${kicker}</span>
      <div class="subset-predictor-title">${title}</div>
      ${mcLine}
      <div class="subset-predictor-stat"><strong>Full-average LOO R² ${formatSubsetMetric(subset.loo_r2)}</strong> · train R² ${formatSubsetMetric(subset.train_r2)}</div>
      <div class="subset-predictor-stat">Full-average LOO r ${formatSubsetMetric(subset.loo_pearson)} · LOO MAE ${formatSubsetMetric(subset.loo_mae)}</div>
      <div class="subset-predictor-word-list">${words}</div>
    </div>
  `;
}

function renderSubsetPrediction() {
  const metric = document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg';
  const analysis = DATA.subset_predictions?.[metric];
  if (!analysis) {
    setSubsetPredictionMessage('Subset score analysis is unavailable for the current build.');
    renderPlotPlaceholder('plot-subset-performance', 'Subset score analysis unavailable.', 420);
    renderPlotPlaceholder('plot-subset-prediction', 'Subset score analysis unavailable.', 420);
    return;
  }

  const summaryContainer = document.getElementById('subset-predictor-summary');
  const bestSubset = analysis.best_subset;
  const highlightCards = [];
  const highlightedSizes = new Set();
  [5, 10, 20].forEach(size => {
    const subset = analysis.highlights?.[String(size)];
    if (!subset) return;
    const cardMonteCarlo = size === 20 ? analysis.one_trial_monte_carlo : null;
    highlightCards.push(buildSubsetPredictionCard(`${size} words`, `${size}-word subset`, subset, cardMonteCarlo));
    highlightedSizes.add(size);
  });
  if (bestSubset && !highlightedSizes.has(bestSubset.size)) {
    highlightCards.unshift(
      buildSubsetPredictionCard(
        `Best ≤ ${analysis.max_subset_size} words`,
        `${bestSubset.size}-word subset`,
        bestSubset,
      )
    );
  }
  if (summaryContainer) {
    const mc = analysis.one_trial_monte_carlo;
    const mcText = mc
      ? ` The scatter uses ${mc.resamples} random one-trial resamples with per-model error bars.`
      : ' The scatter uses leave-one-out predictions from the best subset.';
    summaryContainer.innerHTML = `
      <div class="subset-predictor-note">
        Computed across ${analysis.n_models} models. The fit curve shows how predictive the subset is as it grows;
        ${mcText}
      </div>
      <div class="subset-predictor-grid">${highlightCards.join('')}</div>
    `;
  }

  const curve = analysis.curve || [];
  Plotly.react('plot-subset-performance', [
    {
      type: 'scatter',
      mode: 'lines+markers',
      x: curve.map(row => row.size),
      y: curve.map(row => row.loo_r2),
      name: 'Leave-one-out R²',
      line: { color: '#2E6080', width: 2.5 },
      marker: { color: '#2E6080', size: 7 },
      hovertemplate: 'Subset size: %{x}<br>LOO R²: %{y:.3f}<extra></extra>',
    },
    {
      type: 'scatter',
      mode: 'lines+markers',
      x: curve.map(row => row.size),
      y: curve.map(row => row.train_r2),
      name: 'Train R²',
      line: { color: TC.textDim, width: 2, dash: 'dot' },
      marker: { color: TC.textDim, size: 6 },
      hovertemplate: 'Subset size: %{x}<br>Train R²: %{y:.3f}<extra></extra>',
    },
  ], {
    ...plotlyLayout(),
    title: { text: `${analysis.metric_label}: subset size vs predictive power`, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: buildAxisConfig(plotlyLayout().xaxis, 'Subset size'),
    yaxis: buildAxisConfig(plotlyLayout().yaxis, 'R²'),
    showlegend: true,
    legend: { font: { size: 10 } },
  }, PLOTLY_CONFIG);
  ensureScoreAxisToggle('plot-subset-performance', []);

  const scoreAxisKeys = isLogScoreMetric(metric) ? ['xaxis', 'yaxis'] : [];
  const mc = analysis.one_trial_monte_carlo;
  const scatterPredictions = mc?.predictions || analysis.predictions || [];
  const flat = scatterPredictions
    .map(point => {
      const meta = modelMap[point.model] || {};
      return {
        x: mc ? point.actual_mean : point.actual,
        y: mc ? point.predicted_mean : point.predicted,
        xStd: mc ? point.actual_std : null,
        yStd: mc ? point.predicted_std : null,
        text: meta.label || point.model,
        company: meta.company || 'Other',
        color: meta.color || '#8B7355',
      };
    })
    .filter(point => Number.isFinite(point.x) && Number.isFinite(point.y));

  if (!flat.length) {
    renderPlotPlaceholder('plot-subset-prediction', 'No subset prediction points available.', 420);
    return;
  }

  const labels = sparseLabels(normalizePoints(flat));
  const byCompany = {};
  flat.forEach((point, idx) => {
    if (!byCompany[point.company]) {
      byCompany[point.company] = { x: [], y: [], xStd: [], yStd: [], text: [], sparseText: [], color: point.color };
    }
    byCompany[point.company].x.push(point.x);
    byCompany[point.company].y.push(point.y);
    byCompany[point.company].xStd.push(point.xStd);
    byCompany[point.company].yStd.push(point.yStd);
    byCompany[point.company].text.push(point.text);
    byCompany[point.company].sparseText.push(labels[idx]);
  });

  const allValues = flat.flatMap(point => [point.x, point.y]);
  const diagonalMin = Math.min(...allValues);
  const diagonalMax = Math.max(...allValues);
  const traces = [{
    type: 'scatter',
    mode: 'lines',
    x: [diagonalMin, diagonalMax],
    y: [diagonalMin, diagonalMax],
    line: { color: TC.textDim, width: 1.5, dash: 'dash' },
    name: 'Ideal',
    hoverinfo: 'skip',
  }];

  Object.entries(byCompany).forEach(([name, group]) => {
    traces.push({
      type: 'scatter',
      mode: 'markers+text',
      x: group.x,
      y: group.y,
      text: group.sparseText,
      name,
      customdata: group.text,
      textposition: 'top center',
      textfont: { size: 9, color: TC.textDim },
      marker: { color: group.color, size: 10, line: { color: TC.markerLine, width: 1.5 } },
      ...(mc ? {
        error_x: { type: 'data', array: group.xStd, visible: true, color: group.color, thickness: 1, width: 3 },
        error_y: { type: 'data', array: group.yStd, visible: true, color: group.color, thickness: 1, width: 3 },
      } : {}),
      hovertemplate: mc
        ? `%{customdata}<br>Actual mean: %{x:.2f}<br>Predicted mean: %{y:.2f}<br>${mc.resamples} one-trial resamples<extra></extra>`
        : '%{customdata}<br>Actual: %{x:.2f}<br>Predicted: %{y:.2f}<extra></extra>',
    });
  });

  const corrText = mc && Number.isFinite(mc.correlation_mean)
    ? `; MC r=${mc.correlation_mean.toFixed(3)}${Number.isFinite(mc.correlation_std) ? ` ± ${mc.correlation_std.toFixed(3)}` : ''}`
    : '';
  Plotly.react('plot-subset-prediction', traces, {
    ...plotlyLayout(),
    title: {
      text: mc
        ? `${analysis.metric_label}: one-trial actual vs predicted (${mc.subset_size} words${corrText})`
        : `${analysis.metric_label}: actual vs predicted (${bestSubset?.size || analysis.best_size} words)`,
      font: { size: 15, family: 'Newsreader, Georgia, serif' },
    },
    xaxis: applyScoreAxisType('plot-subset-prediction', buildAxisConfig(plotlyLayout().xaxis, mc ? 'Actual score, one-trial mean' : 'Actual score'), 'xaxis', scoreAxisKeys),
    yaxis: applyScoreAxisType('plot-subset-prediction', buildAxisConfig(plotlyLayout().yaxis, mc ? 'Predicted score, one-trial mean' : 'Leave-one-out predicted score'), 'yaxis', scoreAxisKeys),
    showlegend: true,
    legend: { font: { size: 10 } },
  }, PLOTLY_CONFIG);
  ensureScoreAxisToggle('plot-subset-prediction', scoreAxisKeys);
}

function renderReasoningEfficiency() {
  if (!DATA.efficiency) {
    renderPlotPlaceholder('plot-reasoning-eff', 'Loading reasoning efficiency data...', 550);
    return;
  }
  const metric = document.querySelector('.leaderboard-metric-toggle .pill-toggle-btn.active')?.dataset.metric || 'sum_chain_avg';
  const mLabel = METRIC_LABELS[metric];
  const scoreAxisKeys = ['yaxis'];

  const effAgg = getFilteredAggregated();
  const modelScores = {};
  effAgg.forEach(d => { modelScores[d.model] = d[metric]; });

  const byModel = {};
  DATA.efficiency.forEach(d => {
    if (!byModel[d.model]) byModel[d.model] = { tokens: [] };
    byModel[d.model].tokens.push(d.avg_output_tokens);
  });

  const flatEff = [];
  Object.entries(byModel).forEach(([mid, d]) => {
    const m = modelMap[mid];
    if (!m) return;
    const avgT = d.tokens.reduce((a, b) => a + b, 0) / d.tokens.length;
    const score = modelScores[mid];
    if (score == null) return;
    flatEff.push({
      x: avgT,
      y: score,
      text: m.label,
      model: mid,
      company: m.company,
      color: m.color,
      rankScore: Number(score),
    });
  });

  if (!flatEff.length) {
    renderPlotPlaceholder('plot-reasoning-eff', 'No reasoning efficiency points match the current filters.', 550);
    ensureScoreAxisToggle('plot-reasoning-eff', []);
    return;
  }

  prioritizeScatterLabels(flatEff, getParetoFrontier(flatEff, 'min', 'max'));

  const byCompany = {};
  flatEff.forEach(p => {
    if (!byCompany[p.company]) {
      byCompany[p.company] = {
        x: [],
        y: [],
        text: [],
        labelText: [],
        priorities: [],
        color: p.color,
      };
    }
    byCompany[p.company].x.push(p.x);
    byCompany[p.company].y.push(p.y);
    byCompany[p.company].text.push(p.text);
    byCompany[p.company].labelText.push(p.text);
    byCompany[p.company].priorities.push(p.priority);
  });

  const companyEntries = Object.entries(byCompany);
  const traces = companyEntries.map(([name, d]) => ({
    type: 'scatter', mode: 'markers+text', x: d.x, y: d.y, name,
    customdata: d.text,
    marker: { color: d.color, size: 10, line: { color: TC.markerLine, width: 1.5 } },
    hovertemplate: `%{customdata}<br>Output tokens: %{x:.0f}<br>${mLabel}: %{y:.2f}<extra></extra>`,
  }));
  const labelGroups = companyEntries.map(([, group], traceIndex) => ({
    traceIndex,
    points: group.x.map((x, pointIndex) => ({
      x,
      y: group.y[pointIndex],
      label: group.labelText[pointIndex],
      priority: group.priorities[pointIndex],
    })),
  }));

  renderCollisionAwareScatter('plot-reasoning-eff', traces, {
    ...plotlyLayout(),
    title: { text: 'Reasoning Efficiency', font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: buildAxisConfig(plotlyLayout().xaxis, 'Avg Output Tokens'),
    yaxis: applyScoreAxisType('plot-reasoning-eff', buildAxisConfig(plotlyLayout().yaxis, mLabel), 'yaxis', scoreAxisKeys),
    showlegend: true, legend: { font: { size: 10 } },
  }, labelGroups);
  ensureScoreAxisToggle('plot-reasoning-eff', scoreAxisKeys);
}

// ─── Trajectory ───
function buildTrajectorySelector() {
  const sorted = [...DATA.aggregated].sort((a, b) => b.sum_chain_avg - a.sum_chain_avg);
  const trajModels = sorted.filter(d => modelMap[d.model]);
  const sharedSet = sharedSelectedModels ? new Set(sharedSelectedModels) : null;
  const modelItems = trajModels.map((d, i) => {
    const m = modelMap[d.model];
    const defaultSet = sharedSet || new Set(getDefaultSharedModelSelection());
    const checked = defaultSet.has(d.model);
    return { value: d.model, label: m.label, color: m.color, checked, searchExtra: m.company };
  });

  // Initialise sharedSelectedModels from defaults if not yet set
  if (!sharedSelectedModels) {
    sharedSelectedModels = modelItems.filter(m => m.checked).map(m => m.value);
  }

  buildSearchableSelector('traj-model-selector', modelItems, {
    placeholder: 'Search models or companies...',
    onchange: () => {
      const vals = getSearchableSelectorValues('traj-model-selector');
      applySharedModelSelection(vals);
      syncURLState({ replace: true });
      if (activeTab === 'patterns') refreshPatternPlots();
    },
  });
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ─── Per-model colour variation ───
// Slightly shift hue + lightness so same-company models are distinguishable.
function varyColor(hex, index, total) {
  if (total <= 1) return hex;
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) { h = s = 0; }
  else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
    else if (max === g) h = ((b - r) / d + 2) / 6;
    else h = ((r - g) / d + 4) / 6;
  }
  const spread = (index - (total - 1) / 2) / Math.max((total - 1) / 2, 1);
  h = ((h + spread * 0.04) % 1 + 1) % 1;
  l = Math.max(0.15, Math.min(0.85, l + spread * 0.06));
  // HSL → RGB
  let r2, g2, b2;
  if (s === 0) { r2 = g2 = b2 = l; }
  else {
    const hue2rgb = (p, q, t) => { t = ((t % 1) + 1) % 1; if (t < 1/6) return p + (q-p)*6*t; if (t < 1/2) return q; if (t < 2/3) return p + (q-p)*(2/3-t)*6; return p; };
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r2 = hue2rgb(p, q, h + 1/3); g2 = hue2rgb(p, q, h); b2 = hue2rgb(p, q, h - 1/3);
  }
  return `#${Math.round(r2*255).toString(16).padStart(2,'0')}${Math.round(g2*255).toString(16).padStart(2,'0')}${Math.round(b2*255).toString(16).padStart(2,'0')}`;
}

/** Return a colour for model `mid` that is slightly shifted when other
 *  models from the same company appear in `modelList`. */
function getModelColor(mid, modelList) {
  const m = modelMap[mid];
  const base = m?.color || '#8B7355';
  const company = m?.company;
  if (!company || !modelList || modelList.length <= 1) return base;
  const sameCompany = modelList.filter(id => modelMap[id]?.company === company);
  if (sameCompany.length <= 1) return base;
  const idx = sameCompany.indexOf(mid);
  return varyColor(base, idx < 0 ? 0 : idx, sameCompany.length);
}


// ─── Exploration Drift ───
function levenshtein(a, b) {
  if (a === b) return 0;
  const m = a.length, n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  let prev = Array.from({ length: n + 1 }, (_, i) => i);
  let curr = new Array(n + 1);
  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    for (let j = 1; j <= n; j++) {
      curr[j] = a[i - 1] === b[j - 1]
        ? prev[j - 1]
        : 1 + Math.min(prev[j - 1], prev[j], curr[j - 1]);
    }
    [prev, curr] = [curr, prev];
  }
  return prev[n];
}

function computeDrift(chain, k) {
  const drifts = [];
  for (let i = 0; i < chain.length; i++) {
    const start = Math.max(0, i - k);
    if (start === i) { drifts.push(0); continue; }
    let sum = 0;
    for (let j = start; j < i; j++) sum += levenshtein(chain[i], chain[j]);
    drifts.push(sum / (i - start));
  }
  return drifts;
}

function getDriftForModel(mid, selectedWords, k) {
  const allWords = DATA.metadata.starting_words;
  const useWords = selectedWords.length === 0 || selectedWords.length === allWords.length
    ? allWords : selectedWords;
  const wordDrifts = [];
  for (const w of useWords) {
    const chain = DATA.chains[w]?.[mid];
    if (!chain || chain.length < 2) continue;
    wordDrifts.push(computeDrift(chain, k));
  }
  if (!wordDrifts.length) return { avg: [], std: [] };
  const maxLen = Math.max(...wordDrifts.map(d => d.length));
  const avg = [], std = [];
  for (let i = 0; i < maxLen; i++) {
    const vals = wordDrifts.filter(d => i < d.length).map(d => d[i]);
    if (vals.length < 1) break;
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    const variance = vals.reduce((a, v) => a + (v - mean) ** 2, 0) / vals.length;
    avg.push(mean);
    std.push(Math.sqrt(variance));
  }
  return { avg, std };
}

function renderDrift() {
  if (!DATA.chains) {
    renderPlotPlaceholder('plot-drift', 'Loading drift data...', 700);
    return;
  }
  const selected = getSearchableSelectorValues('traj-model-selector');
  const selectedWords = DATA.metadata.starting_words;
  const k = 20;

  if (!selected.length) {
    Plotly.react('plot-drift', [], { ...plotlyLayout(), title: { text: 'Select models above', font: { size: 14, family: 'Newsreader, Georgia, serif', color: TC.textDim } } }, PLOTLY_CONFIG);
    scheduleVisiblePlotlyResize();
    return;
  }

  const wordLabel = selectedWords.length === DATA.metadata.starting_words.length ? 'All Words' :
    selectedWords.length === 0 ? 'No Words Selected' :
      selectedWords.length <= 3 ? selectedWords.join(', ') : `${selectedWords.length} words`;

  const traces = [];
  selected.forEach(mid => {
    const m = modelMap[mid];
    const { avg: traj, std: trajStd } = getDriftForModel(mid, selectedWords, k);
    if (!traj.length) return;
    const color = getModelColor(mid, selected);
    const xs = traj.map((_, i) => i + 1);

    if (trajStd && trajStd.length === traj.length) {
      const upper = traj.map((v, i) => v + trajStd[i]);
      const lower = traj.map((v, i) => Math.max(0, v - trajStd[i]));
      const bandColor = hexToRgba(color, 0.15);
      traces.push({ type: 'scatter', mode: 'lines', x: xs, y: upper, line: { width: 0 }, showlegend: false, hoverinfo: 'skip', legendgroup: mid });
      traces.push({ type: 'scatter', mode: 'lines', x: xs, y: lower, line: { width: 0 }, fill: 'tonexty', fillcolor: bandColor, showlegend: false, hoverinfo: 'skip', legendgroup: mid });
    }

    traces.push({
      type: 'scatter', mode: 'lines+markers',
      x: xs, y: traj,
      name: m?.label || mid,
      legendgroup: mid,
      line: { color, width: 2 },
      marker: { size: 4 },
      hovertemplate: `${m?.label || mid}<br>Move %{x}<br>Drift (k=${k}) = %{y:.3f}<extra></extra>`,
    });
  });

  Plotly.react('plot-drift', traces, {
    ...plotlyLayout(),
    title: { text: `Exploration Drift (k=${k}) — ${wordLabel}`, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: { ...plotlyLayout().xaxis, title: { text: 'Move Index', font: { size: 12 } } },
    yaxis: { ...plotlyLayout().yaxis, title: { text: `Avg Edit Distance to Previous ${k} Words`, font: { size: 12 } } },
    showlegend: true, legend: { font: { size: 11 } },
  }, PLOTLY_CONFIG);
  scheduleVisiblePlotlyResize();
}

// ─── Stop Reasons ───
const STOP_REASON_COLORS = {
  clean_stop: '#4A9F6E',
  dead_end: '#2E86AB',
  repeated_word: '#C4883C',
  invalid_word: '#C44E52',
  wrong_edit_distance: '#7B6BB5',
  no_output: '#888888',
};
const STOP_REASON_LABELS = {
  clean_stop: 'Clean Stop / Token Limit',
  dead_end: 'Dead End (no legal moves left)',
  repeated_word: 'Repeated Word',
  invalid_word: 'Invalid Word',
  wrong_edit_distance: 'Wrong Edit Distance',
  no_output: 'No Valid Output',
};
const CHAIN_PATTERN_COLORS = {
  I: STOP_REASON_COLORS.clean_stop,
  D: STOP_REASON_COLORS.invalid_word,
  S: STOP_REASON_COLORS.wrong_edit_distance,
  bridge: STOP_REASON_COLORS.dead_end,
};

let stopSortKey = 'clean_stop';
let stopSortAsc = false;

document.getElementById('stop-table')?.addEventListener('click', e => {
  const th = e.target.closest('th[data-sort]');
  if (!th) return;
  const key = th.dataset.sort;
  if (stopSortKey === key) {
    stopSortAsc = !stopSortAsc;
  } else {
    stopSortKey = key;
    stopSortAsc = key === 'model' || key === 'company';
  }
  // Sync the pill toggle if sorting by a reason
  const pillBtn = document.querySelector(`#stop-sort-toggle .pill-toggle-btn[data-sort="${key}"]`);
  if (pillBtn && !pillBtn.classList.contains('active')) {
    document.querySelectorAll('#stop-sort-toggle .pill-toggle-btn').forEach(b => b.classList.remove('active'));
    pillBtn.classList.add('active');
    const slider = document.querySelector('#stop-sort-toggle .pill-toggle-slider');
    if (slider) { slider.style.left = pillBtn.offsetLeft + 'px'; slider.style.width = pillBtn.offsetWidth + 'px'; }
  }
  renderStopReasons();
});

function getStopReasonData() {
  const allReasons = Object.keys(STOP_REASON_COLORS);
  const allModels = DATA.aggregated.map(d => d.model);
  const reasonCounts = {};
  const totalTrials = {};
  allModels.forEach(mid => {
    const counts = {};
    allReasons.forEach(r => counts[r] = 0);
    let total = 0;
    for (const word of DATA.metadata.starting_words) {
      const reasons = DATA.stop_reasons[word]?.[mid];
      if (reasons && Array.isArray(reasons)) {
        reasons.forEach(r => { if (counts[r] != null) counts[r]++; total++; });
      }
    }
    reasonCounts[mid] = counts;
    totalTrials[mid] = total;
  });
  return { allReasons, allModels, reasonCounts, totalTrials };
}

const STOP_SHORT_LABELS = {
  clean_stop: 'Clean Stop', dead_end: 'Dead End', repeated_word: 'Repeated',
  invalid_word: 'Invalid', wrong_edit_distance: 'Wrong Dist', no_output: 'No Output',
};

function renderStopReasons() {
  if (!DATA.stop_reasons) {
    renderPlotPlaceholder('plot-stop-reasons', 'Loading chain termination data...', 420);
    return;
  }
  const topkBtn = document.querySelector('#stop-topk-toggle .pill-toggle-btn.active');
  const topk = topkBtn?.dataset.topk === 'all' ? Infinity : parseInt(topkBtn?.dataset.topk || '20');
  const pillSort = document.querySelector('#stop-sort-toggle .pill-toggle-btn.active')?.dataset.sort || 'clean_stop';

  // Sync stopSortKey with pill toggle if user clicked a pill (not a table header)
  const isNonReasonSort = stopSortKey === 'model' || stopSortKey === 'company' || stopSortKey === 'rank';
  if (!isNonReasonSort && stopSortKey !== pillSort && Object.keys(STOP_REASON_COLORS).includes(pillSort)) {
    stopSortKey = pillSort;
    stopSortAsc = false;
  }

  const { allReasons, allModels, reasonCounts, totalTrials } = getStopReasonData();

  // Pre-compute each model's rank based on the active pill metric (unaffected by display sort)
  const rankMap = {};
  [...allModels]
    .sort((a, b) => (reasonCounts[b][pillSort] / (totalTrials[b] || 1)) - (reasonCounts[a][pillSort] / (totalTrials[a] || 1)))
    .forEach((mid, i) => { rankMap[mid] = i + 1; });

  const stopFilterText = (document.getElementById('stop-filter')?.value || '').toLowerCase();
  const filtered = stopFilterText
    ? allModels.filter(mid => {
        const m = modelMap[mid];
        return (m?.label || mid).toLowerCase().includes(stopFilterText) || (m?.company || '').toLowerCase().includes(stopFilterText);
      })
    : allModels;

  const sorted = [...filtered]
    .sort((a, b) => {
      let cmp;
      if (stopSortKey === 'rank') {
        cmp = rankMap[a] - rankMap[b];
      } else if (stopSortKey === 'model') {
        cmp = (modelMap[a]?.label || a).localeCompare(modelMap[b]?.label || b);
      } else if (stopSortKey === 'company') {
        cmp = (modelMap[a]?.company || '').localeCompare(modelMap[b]?.company || '');
      } else {
        const aTotal = totalTrials[a] || 1;
        const bTotal = totalTrials[b] || 1;
        cmp = (reasonCounts[a][stopSortKey] / aTotal) - (reasonCounts[b][stopSortKey] / bTotal);
      }
      return stopSortAsc ? cmp : -cmp;
    })
    .slice(0, topk);

  const view = document.querySelector('#stop-view-toggle .pill-toggle-btn.active')?.dataset.view || 'table';

  // ─── Table view ───
  const thead = document.getElementById('stop-table-head');
  const tbody = document.getElementById('stop-table-body');
  if (thead && tbody) {
    function sortClass(key) {
      if (key !== stopSortKey) return '';
      return ` class="sorted ${stopSortAsc ? 'asc' : 'desc'}"`;
    }
    syncFixedTableColumns(thead.closest('table'), allReasons.length + 3);
    thead.innerHTML = `<th data-sort="rank"${sortClass('rank')}>#</th><th data-sort="model"${sortClass('model')}>Model</th><th data-sort="company"${sortClass('company')}>Company</th>` +
      allReasons.map(r => `<th data-sort="${r}"${sortClass(r)}>${STOP_SHORT_LABELS[r]}</th>`).join('');
    tbody.innerHTML = '';
    sorted.forEach((mid) => {
      const m = modelMap[mid];
      const t = totalTrials[mid] || 1;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><span class="leaderboard-rank">${rankMap[mid]}</span></td><td><span class="leaderboard-model">${m?.label || mid}</span></td>` +
        `<td><span class="leaderboard-company"><span class="leaderboard-company-swatch" style="background:${m?.color || '#888'}"></span>${m?.company || ''}</span></td>` +
        allReasons.map(r => {
          const pct = (reasonCounts[mid][r] / t * 100).toFixed(1);
          return `<td><span class="leaderboard-score">${pct}%</span></td>`;
        }).join('');
      tbody.appendChild(tr);
    });
  }

  // ─── Chart view ───
  if (view === 'chart') {
    const chartSorted = [...sorted].reverse();
    const chartSortKey = allReasons.includes(stopSortKey) ? stopSortKey : 'clean_stop';
    const orderedReasons = [chartSortKey, ...allReasons.filter(r => r !== chartSortKey)];
    const traces = orderedReasons.map(reason => ({
      type: 'bar',
      orientation: 'h',
      name: STOP_REASON_LABELS[reason],
      y: chartSorted.map(mid => modelMap[mid]?.label || mid),
      x: chartSorted.map(mid => {
        const t = totalTrials[mid] || 1;
        return Math.round(reasonCounts[mid][reason] / t * 100 * 100) / 100;
      }),
      marker: { color: STOP_REASON_COLORS[reason] },
      customdata: chartSorted.map(mid => reasonCounts[mid][reason]),
      hovertemplate: '%{y}<br>' + STOP_REASON_LABELS[reason] + ': %{customdata} (%{x:.1f}%)<extra></extra>',
    }));

    const plotHeight = Math.max(300, chartSorted.length * 26 + 100);
    document.getElementById('plot-stop-reasons').style.height = plotHeight + 'px';

    const stopDiv = document.getElementById('plot-stop-reasons');
    Plotly.purge(stopDiv);
    Plotly.newPlot(stopDiv, traces, {
      ...plotlyLayout(),
      barmode: 'stack',
      title: { text: `Chain Termination (sorted by % ${STOP_REASON_LABELS[chartSortKey]})`, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
      xaxis: { ...plotlyLayout().xaxis, title: { text: '% of Trials', font: { size: 12 } }, range: [0, 100] },
      yaxis: { ...plotlyLayout().yaxis, automargin: true, tickfont: { size: 11 }, categoryorder: 'array', categoryarray: chartSorted.map(mid => modelMap[mid]?.label || mid) },
      height: plotHeight,
      margin: { ...plotlyLayout().margin, l: 200 },
      legend: { font: { size: 11 } },
    }, PLOTLY_CONFIG);
  }
}

// ─── Directional Analysis ───
let dirModels = [];
const CHAIN_METRIC_SCORECARD_HEIGHT = 520;
const CHAIN_METRIC_PLOT_HEIGHT = 450;
const GRAPH_METRIC_PLOT_HEIGHTS = {
  'plot-exploration-scorecard': CHAIN_METRIC_SCORECARD_HEIGHT,
  'plot-neighborhood-novelty': CHAIN_METRIC_PLOT_HEIGHT,
  'plot-core-bias': CHAIN_METRIC_PLOT_HEIGHT,
  'plot-graph-spread': CHAIN_METRIC_PLOT_HEIGHT,
  'plot-exploration-scorecard-li': CHAIN_METRIC_SCORECARD_HEIGHT,
  'plot-li-neighborhood-novelty': CHAIN_METRIC_PLOT_HEIGHT,
  'plot-li-core-bias': CHAIN_METRIC_PLOT_HEIGHT,
  'plot-li-graph-spread': CHAIN_METRIC_PLOT_HEIGHT,
};
const GRAPH_METRIC_PLOT_IDS = Object.keys(GRAPH_METRIC_PLOT_HEIGHTS);
const RAW_CHAIN_METRIC_DEFS = [
  {
    key: 'neighborhood_novelty',
    divId: 'plot-neighborhood-novelty',
    title: 'Neighborhood Novelty',
    yTitle: 'Novelty Index',
    summaryKey: 'neighborhood_novelty_mean',
    summaryLabel: 'Novelty',
    digits: 3,
    smoothingWindow: 5,
  },
  {
    key: 'core_bias',
    divId: 'plot-core-bias',
    title: 'Core Bias',
    yTitle: 'Dense-Choice Percentile',
    summaryKey: 'core_bias_mean',
    summaryLabel: 'Core Bias',
    digits: 3,
    smoothingWindow: 5,
  },
  {
    key: 'graph_spread',
    divId: 'plot-graph-spread',
    title: 'Graph Spread',
    yTitle: 'Mean Pairwise Graph Distance',
    summaryKey: 'graph_spread_mean',
    summaryLabel: 'Graph Spread',
    digits: 3,
    smoothingWindow: 1,
  },
];
const LENGTH_INVARIANT_CHAIN_METRIC_DEFS = [
  {
    key: 'neighborhood_novelty',
    divId: 'plot-li-neighborhood-novelty',
    title: 'Neighborhood Novelty',
    yTitle: 'Novelty Index',
    summaryKey: 'neighborhood_novelty_mean',
    summaryLabel: 'Novelty',
    digits: 3,
    smoothingWindow: 5,
  },
  {
    key: 'core_bias',
    divId: 'plot-li-core-bias',
    title: 'Core Bias',
    yTitle: 'Dense-Choice Percentile',
    summaryKey: 'core_bias_mean',
    summaryLabel: 'Core Bias',
    digits: 3,
    smoothingWindow: 5,
  },
  {
    key: 'incremental_graph_spread',
    divId: 'plot-li-graph-spread',
    title: 'Incremental Graph Spread',
    yTitle: 'Mean Distance to Prior Nodes',
    summaryKey: 'incremental_graph_spread_mean',
    summaryLabel: 'Incremental Spread',
    digits: 3,
    smoothingWindow: 3,
  },
];
const GRAPH_METRIC_SECTIONS = [
  {
    scorecardId: 'plot-exploration-scorecard',
    scorecardTitle: 'Exploration Scorecard',
    summariesKey: 'chain_metric_summaries',
    trajectoriesKey: 'chain_metric_trajectories',
    xMode: 'move',
    defs: RAW_CHAIN_METRIC_DEFS,
  },
  {
    scorecardId: 'plot-exploration-scorecard-li',
    scorecardTitle: 'Length-Invariant Scorecard',
    summariesKey: 'chain_metric_length_invariant_summaries',
    trajectoriesKey: 'chain_metric_length_invariant_trajectories',
    xMode: 'progress',
    defs: LENGTH_INVARIANT_CHAIN_METRIC_DEFS,
  },
];

function formatChainMetricValue(value, digits = 3) {
  if (value == null || Number.isNaN(value)) return 'n/a';
  return Number(value).toFixed(digits);
}

function rankNormalizeValues(values) {
  if (!values.length) return [];
  if (values.length === 1) return [0.5];
  const indexed = values.map((value, index) => ({ value, index }))
    .sort((a, b) => a.value - b.value);
  const normalized = new Array(values.length).fill(0.5);
  let start = 0;
  while (start < indexed.length) {
    let end = start + 1;
    while (end < indexed.length && indexed[end].value === indexed[start].value) end += 1;
    const avgRank = (start + end - 1) / 2;
    const pct = avgRank / (indexed.length - 1);
    for (let i = start; i < end; i += 1) normalized[indexed[i].index] = pct;
    start = end;
  }
  return normalized;
}

function smoothCenteredSeries(values, windowSize = 1) {
  if (!Array.isArray(values) || values.length === 0 || windowSize <= 1) return values ? values.slice() : [];
  const radius = Math.floor(windowSize / 2);
  return values.map((_, index) => {
    let sum = 0;
    let count = 0;
    const start = Math.max(0, index - radius);
    const end = Math.min(values.length - 1, index + radius);
    for (let idx = start; idx <= end; idx += 1) {
      const value = values[idx];
      if (value == null || Number.isNaN(value)) continue;
      sum += value;
      count += 1;
    }
    return count ? sum / count : values[index];
  });
}


function renderDirectionalLoading(message) {
  const loadingLayout = {
    ...plotlyLayout(),
    height: 450,
    title: {
      text: message,
      font: { size: 14, family: 'Newsreader, Georgia, serif', color: TC.textDim },
    },
  };
  ['plot-edit-types', 'plot-bridge-rate', 'plot-word-length-series']
    .forEach(id => Plotly.react(id, [], loadingLayout, PLOTLY_CONFIG));
}

function renderGraphMetricLoading(message) {
  GRAPH_METRIC_PLOT_IDS.forEach(id => renderPlotPlaceholder(id, message, GRAPH_METRIC_PLOT_HEIGHTS[id]));
}

function renderChainMetricScorecard(section) {
  const summaries = new Map((DATA[section.summariesKey] || []).map(row => [row.model, row]));
  const selected = dirModels.filter(mid => summaries.has(mid));
  if (!selected.length) {
    renderPlotPlaceholder(section.scorecardId, 'Select models above', CHAIN_METRIC_SCORECARD_HEIGHT);
    return;
  }

  const metricLabels = section.defs.map(def => def.summaryLabel);
  const yLabels = selected.map(mid => modelMap[mid]?.label || mid);
  const rawMatrix = selected.map(mid => {
    const row = summaries.get(mid) || {};
    return section.defs.map(def => row[def.summaryKey]);
  });

  const normalizedMatrix = rawMatrix.map(row => row.map(() => 0.5));
  for (let col = 0; col < section.defs.length; col += 1) {
    const values = rawMatrix.map(row => row[col]);
    const validEntries = values
      .map((value, index) => ({ value, index }))
      .filter(entry => entry.value != null && !Number.isNaN(entry.value));
    const normalized = rankNormalizeValues(validEntries.map(entry => entry.value));
    validEntries.forEach((entry, idx) => {
      normalizedMatrix[entry.index][col] = normalized[idx];
    });
  }

  const hoverText = rawMatrix.map((row, rowIdx) => row.map((value, colIdx) =>
    `${yLabels[rowIdx]}<br>${metricLabels[colIdx]}: ${formatChainMetricValue(value, section.defs[colIdx].digits)}`
  ));

  Plotly.react(section.scorecardId, [{
    type: 'heatmap',
    x: metricLabels,
    y: yLabels,
    z: normalizedMatrix,
    text: hoverText,
    hovertemplate: '%{text}<extra></extra>',
    colorscale: TC.heatScale,
    zmin: 0,
    zmax: 1,
    showscale: true,
    colorbar: { title: { text: 'Within-selection rank', side: 'right' } },
  }], {
    ...plotlyLayout(),
    height: CHAIN_METRIC_SCORECARD_HEIGHT,
    title: { text: section.scorecardTitle, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis: { ...plotlyLayout().xaxis, side: 'top' },
    yaxis: { ...plotlyLayout().yaxis, automargin: true, tickfont: { size: 10 } },
    margin: { ...plotlyLayout().margin, l: 180, t: 90 },
  }, PLOTLY_CONFIG);
}

function buildMetricProgressXs(length) {
  if (length <= 1) return [0];
  return Array.from({ length }, (_, index) => index / (length - 1));
}

function renderChainMetricTrajectoryPlot(definition, metricTrajectoriesByKey, xMode = 'move') {
  const metricTrajectories = metricTrajectoriesByKey?.[definition.key] || {};
  const selected = dirModels.filter(mid => metricTrajectories[mid]?.__all__?.length);
  if (!selected.length) {
    renderPlotPlaceholder(definition.divId, 'Select models above', CHAIN_METRIC_PLOT_HEIGHT);
    return;
  }

  const smoothWindow = definition.smoothingWindow || 1;
  const smoothingLabel = smoothWindow > 1 ? ` · Smoothed (${smoothWindow}-move window)` : '';
  const traces = [];
  selected.forEach(mid => {
    const payload = metricTrajectories[mid];
    const rawAvg = payload?.__all__ || [];
    const rawStd = payload?.__all_std__ || [];
    if (!rawAvg.length) return;

    const avg = smoothCenteredSeries(rawAvg, smoothWindow);
    const std = rawStd.length === rawAvg.length ? smoothCenteredSeries(rawStd, smoothWindow) : [];

    const color = getModelColor(mid, selected);
    const xs = xMode === 'progress' ? buildMetricProgressXs(avg.length) : avg.map((_, index) => index + 1);
    if (std.length === avg.length) {
      const upper = avg.map((value, index) => value + std[index]);
      const lower = avg.map((value, index) => Math.max(0, value - std[index]));
      traces.push({ type: 'scatter', mode: 'lines', x: xs, y: upper, line: { width: 0 }, showlegend: false, hoverinfo: 'skip', legendgroup: mid });
      traces.push({ type: 'scatter', mode: 'lines', x: xs, y: lower, line: { width: 0 }, fill: 'tonexty', fillcolor: hexToRgba(color, 0.15), showlegend: false, hoverinfo: 'skip', legendgroup: mid });
    }

    traces.push({
      type: 'scatter',
      mode: 'lines+markers',
      x: xs,
      y: avg,
      name: modelMap[mid]?.label || mid,
      customdata: rawAvg,
      legendgroup: mid,
      line: { color, width: 2 },
      marker: { size: 4 },
      hovertemplate: `${modelMap[mid]?.label || mid}<br>${xMode === 'progress' ? 'Progress %{x:.0%}' : 'Move %{x}'}<br>Smoothed ${definition.summaryLabel}: %{y:.${definition.digits}f}<br>Raw ${definition.summaryLabel}: %{customdata:.${definition.digits}f}<extra></extra>`,
    });
  });

  const metricSmoothingLabel = smoothWindow > 1
    ? ` · Smoothed (${smoothWindow}-${xMode === 'progress' ? 'progress-bin' : 'move'} window)`
    : '';
  const chainMetricTitleSuffix = smoothWindow > 1
    ? ` (Smoothed: ${smoothWindow}-${xMode === 'progress' ? 'progress-bin' : 'move'} window)`
    : '';
  const xaxis = xMode === 'progress'
    ? { ...plotlyLayout().xaxis, title: { text: 'Normalized Chain Progress', font: { size: 12 } }, tickformat: '.0%', range: [0, 1] }
    : { ...plotlyLayout().xaxis, title: { text: 'Move Index', font: { size: 12 } } };
  Plotly.react(definition.divId, traces, {
    ...plotlyLayout(),
    height: CHAIN_METRIC_PLOT_HEIGHT,
    title: { text: `${definition.title}${chainMetricTitleSuffix}`, font: { size: 15, family: 'Newsreader, Georgia, serif' } },
    xaxis,
    yaxis: { ...plotlyLayout().yaxis, title: { text: definition.yTitle, font: { size: 12 } } },
    showlegend: true,
    legend: { font: { size: 11 } },
  }, PLOTLY_CONFIG);
}

function renderGraphExplorationMetrics() {
  if (!DATA.chain_metric_trajectories || !DATA.chain_metric_summaries
      || !DATA.chain_metric_length_invariant_trajectories || !DATA.chain_metric_length_invariant_summaries) {
    renderGraphMetricLoading('Loading graph exploration metrics...');
    return;
  }
  GRAPH_METRIC_SECTIONS.forEach(section => {
    renderChainMetricScorecard(section);
    const trajectories = DATA[section.trajectoriesKey] || {};
    section.defs.forEach(definition => renderChainMetricTrajectoryPlot(definition, trajectories, section.xMode));
  });
}


function initDirectionalAnalysis() {
  const sorted = [...DATA.aggregated].sort((a, b) => b.sum_chain_avg - a.sum_chain_avg);
  const sharedSet = sharedSelectedModels ? new Set(sharedSelectedModels) : null;
  const modelItems = sorted
    .filter(d => modelMap[d.model])
    .map((d, i) => {
      const m = modelMap[d.model];
      const checked = sharedSet ? sharedSet.has(d.model) : i < 5;
      return { value: d.model, label: m.label, color: m.color, checked, searchExtra: m.company };
    });
  buildSearchableSelector('dir-model-selector', modelItems, {
    placeholder: 'Search models or companies...',
    onchange: (vals) => {
      applySharedModelSelection(vals);
      explorerModels = getSearchableSelectorValues('explorer-model-selector');
      syncURLState({ replace: true });
      if (activeTab === 'patterns') refreshPatternPlots();
    },
  });
  dirModels = modelItems.filter(m => m.checked).map(m => m.value);
  // Defer initial render — graphs need loading first
}

function renderDirectionalAnalysis() {
  if (!dirModels.length) {
    const emptyLayout = { ...plotlyLayout(), height: 450, title: { text: 'Select models above', font: { size: 14, family: 'Newsreader, Georgia, serif', color: TC.textDim } } };
    ['plot-edit-types','plot-bridge-rate','plot-word-length-series'].forEach(id =>
      Plotly.react(id, [], emptyLayout, PLOTLY_CONFIG));
    scheduleVisiblePlotlyResize();
    return;
  }
  // ─── Bridge Strategy Analysis ───
  // Classify each step as I(nsertion), D(eletion), S(ubstitution)
  function classifyEditType(a, b) {
    if (b.length > a.length) return 'I';
    if (b.length < a.length) return 'D';
    return 'S';
  }

  function getChainEditTypes(mid) {
    const types = [];
    const words = DATA.metadata.starting_words || [];
    for (const w of words) {
      const chain = DATA.chains[w]?.[mid];
      if (!chain || chain.length < 2) continue;
      for (let i = 0; i < chain.length - 1; i++) {
        types.push(classifyEditType(chain[i], chain[i + 1]));
      }
    }
    return types;
  }

  function getScaffoldRates(mid) {
    let bridge = 0, windows = 0;
    const words = DATA.metadata.starting_words || [];
    for (const w of words) {
      const chain = DATA.chains[w]?.[mid];
      if (!chain || chain.length < 4) continue;
      const edits = [];
      for (let i = 0; i < chain.length - 1; i++) edits.push(classifyEditType(chain[i], chain[i + 1]));
      for (let i = 0; i <= edits.length - 3; i++) {
        const pat = edits[i] + edits[i + 1] + edits[i + 2];
        if (pat === 'ISD' || pat === 'DSI') bridge++;
        windows++;
      }
    }
    return {
      bridge: windows > 0 ? bridge / windows : 0,
    };
  }

  function getWordLengthSeries(mid, word) {
    const chain = DATA.chains[word]?.[mid];
    if (!chain || chain.length < 2) return [];
    return chain.map(w => w.length);
  }

  // 3. Edit Type Distribution (stacked bar)
  const editTraces = { I: [], D: [], S: [] };
  const editLabels = [];
  dirModels.forEach(mid => {
    const types = getChainEditTypes(mid);
    const total = types.length || 1;
    const counts = { I: 0, D: 0, S: 0 };
    types.forEach(t => counts[t]++);
    editLabels.push(modelMap[mid]?.label || mid);
    editTraces.I.push(Math.round(counts.I / total * 1000) / 10);
    editTraces.D.push(Math.round(counts.D / total * 1000) / 10);
    editTraces.S.push(Math.round(counts.S / total * 1000) / 10);
  });
  const editNames = { I: 'Insertion', D: 'Deletion', S: 'Substitution' };
  const editColors = { I: CHAIN_PATTERN_COLORS.I, D: CHAIN_PATTERN_COLORS.D, S: CHAIN_PATTERN_COLORS.S };
  Plotly.react('plot-edit-types', ['I', 'D', 'S'].map(k => ({
    type: 'bar', x: editLabels, y: editTraces[k],
    name: editNames[k], marker: { color: editColors[k], opacity: 0.85 },
  })), {
    ...plotlyLayout(), barmode: 'stack', height: 600,
    margin: { ...plotlyLayout().margin, b: 150 },
    xaxis: { ...plotlyLayout().xaxis, tickangle: -45 },
    yaxis: { ...plotlyLayout().yaxis, title: { text: '% of Moves', font: { size: 12 } } },
    showlegend: true, legend: { font: { size: 11 } },
  }, PLOTLY_CONFIG);

  // 4. Bridge Pattern Rate
  const scLabels = [], scVals = [];
  dirModels.forEach(mid => {
    const rates = getScaffoldRates(mid);
    scLabels.push(modelMap[mid]?.label || mid);
    scVals.push(Math.round(rates.bridge * 1000) / 10);
  });
  Plotly.react('plot-bridge-rate', [
    { type: 'bar', x: scLabels, y: scVals, name: 'Bridge (I↔S↔D)', marker: { color: CHAIN_PATTERN_COLORS.bridge, opacity: 0.85 } },
  ], {
    ...plotlyLayout(), barmode: 'group', height: 600,
    margin: { ...plotlyLayout().margin, b: 150 },
    xaxis: { ...plotlyLayout().xaxis, tickangle: -45 },
    yaxis: { ...plotlyLayout().yaxis, title: { text: 'Rate (%)', font: { size: 12 } } },
    showlegend: true, legend: { font: { size: 11 } },
  }, PLOTLY_CONFIG);

  // 5. Word Length Over Chain Steps (line chart, per starting word)
  const wlWords = DATA.metadata.starting_words || [];
  if (!window._wlIdx) window._wlIdx = 0;
  if (!window._wlInit) {
    document.getElementById('wl-prev').addEventListener('click', () => {
      window._wlIdx = (window._wlIdx - 1 + wlWords.length) % wlWords.length;
      renderDirectionalAnalysis();
    });
    document.getElementById('wl-next').addEventListener('click', () => {
      window._wlIdx = (window._wlIdx + 1) % wlWords.length;
      renderDirectionalAnalysis();
    });
    window._wlInit = true;
  }
  const selectedWord = wlWords[window._wlIdx] || '';
  document.getElementById('wl-word-label').textContent = selectedWord;
  Plotly.react('plot-word-length-series', dirModels.map(mid => {
    const series = getWordLengthSeries(mid, selectedWord);
    return {
      type: 'scatter', mode: 'lines+markers',
      x: series.map((_, i) => i),
      y: series,
      name: modelMap[mid]?.label || mid,
      line: { color: getModelColor(mid, dirModels), width: 2 },
      marker: { size: 4 },
    };
  }), {
    ...plotlyLayout(), height: 450,
    xaxis: { ...plotlyLayout().xaxis, title: { text: 'Chain Step', font: { size: 12 } } },
    yaxis: { ...plotlyLayout().yaxis, title: { text: 'Word Length', font: { size: 12 } }, dtick: 1 },
    showlegend: true, legend: { font: { size: 11 } },
  }, PLOTLY_CONFIG);
  scheduleVisiblePlotlyResize();
}

// ─── Word Explorer (3D grid overview) ───
let explorerModels = [];
let explorerCells = {}; // word -> { canvas, ctx, graph, chains, animTimer, animStep, ... }
let sharedSelectedModels = null; // shared between trajectory + explorer selectors; null = first load
let explorerViewMode = '3d';

function syncExplorerModeUI() {
  const note = document.getElementById('explorer-3d-note');
  if (note) note.hidden = explorerViewMode !== '3d';
}

function syncModelSelector(containerId, values) {
  const valueSet = new Set(values);
  document.querySelectorAll(`[data-group="${containerId}"]`).forEach(cb => {
    cb.checked = valueSet.has(cb.value);
  });
  const countEl = document.getElementById(`${containerId}-count`);
  if (countEl) {
    const n = [...document.querySelectorAll(`[data-group="${containerId}"]:checked`)].length;
    countEl.textContent = `${n} selected`;
  }
  // Refresh chips if collapsible
  const list = document.getElementById(`${containerId}-list`);
  if (list) list.dispatchEvent(new Event('sync'));
}

function initExplorer() {
  const sorted = [...DATA.aggregated].sort((a, b) => b.sum_chain_avg - a.sum_chain_avg);
  const sharedSet = sharedSelectedModels ? new Set(sharedSelectedModels) : null;
  const modelItems = sorted
    .filter(d => modelMap[d.model])
    .map((d, i) => {
      const m = modelMap[d.model];
      const defaultSet = sharedSet || new Set(getDefaultSharedModelSelection());
      const checked = defaultSet.has(d.model);
      return { value: d.model, label: m.label, color: m.color, checked, searchExtra: m.company };
    });

  buildSearchableSelector('explorer-model-selector', modelItems, {
    placeholder: 'Search models or companies...',
    onchange: (vals) => {
      applySharedModelSelection(vals);
      syncURLState({ replace: true });
      renderExplorerGrid();
    },
  });
  explorerModels = modelItems.filter(m => m.checked).map(m => m.value);

  const gridContainer = document.getElementById('explorer-grid-container');
  if (gridContainer && !gridContainer.dataset.bound) {
    gridContainer.addEventListener('click', event => {
      const button = event.target.closest('button[data-action]');
      if (!button) return;
      const word = button.dataset.word;
      if (!word) return;
      if (button.dataset.action === 'play') playExplorerCell(word);
      if (button.dataset.action === 'maximize') openExplorerModal(word);
    });
    gridContainer.dataset.bound = 'true';
  }

  const viewToggle = document.getElementById('explorer-view-toggle');
  if (viewToggle && !viewToggle.dataset.bound) {
    initPillToggle(viewToggle);
    viewToggle.addEventListener('pill-change', e => {
      explorerViewMode = e.detail.dataset.view === 'text' ? 'text' : '3d';
      syncExplorerModeUI();
      renderExplorerGrid();
    });
    viewToggle.dataset.bound = 'true';
  }

  syncExplorerModeUI();
}


function buildExplorerMeta(word) {
  const meta = document.createElement('span');
  meta.className = 'explorer-cell-meta';

  const visibleChains = explorerModels
    .map(mid => ({ mid, chain: DATA.chains[word]?.[mid] }))
    .filter(entry => entry.chain);

  if (!visibleChains.length) return meta;

  meta.append(' · ');
  visibleChains.forEach((entry, index) => {
    if (index > 0) meta.append(' / ');
    const count = document.createElement('span');
    count.style.color = getModelColor(entry.mid, explorerModels);
    count.textContent = String(entry.chain.length);
    meta.appendChild(count);
  });

  return meta;
}

function getEditFragments(prev, next) {
  if (prev === next) {
    return { type: 'sub', letter: '', parts: [{ text: next, cls: '' }] };
  }

  if (next.length > prev.length) {
    let idx = 0;
    while (idx < prev.length && prev[idx] === next[idx]) idx += 1;
    return {
      type: 'insert',
      letter: next[idx] || '',
      parts: [
        { text: next.slice(0, idx), cls: '' },
        { text: next[idx] || '', cls: 'hero-edit hero-edit-insert' },
        { text: next.slice(idx + 1), cls: '' },
      ],
    };
  }

  if (next.length < prev.length) {
    let idx = 0;
    while (idx < next.length && prev[idx] === next[idx]) idx += 1;
    return {
      type: 'delete',
      letter: prev[idx] || '',
      parts: [
        { text: next.slice(0, idx), cls: '' },
        { text: prev[idx] || '', cls: 'hero-edit hero-edit-delete' },
        { text: next.slice(idx), cls: '' },
      ],
    };
  }

  let idx = 0;
  while (idx < prev.length && prev[idx] === next[idx]) idx += 1;
  return {
    type: 'sub',
    letter: prev[idx] || '',
    parts: [
      { text: next.slice(0, idx), cls: '' },
      { text: next[idx] || '', cls: 'hero-edit hero-edit-sub' },
      { text: next.slice(idx + 1), cls: '' },
    ],
  };
}

function createWordToken(parts, invalid = false) {
  const word = document.createElement('span');
  word.className = invalid ? 'hero-example-word hero-example-word-invalid' : 'hero-example-word';
  parts.forEach(part => {
    if (!part.text) return;
    if (!part.cls) {
      word.append(part.text);
      return;
    }
    const span = document.createElement('span');
    span.className = part.cls;
    span.textContent = part.text;
    word.appendChild(span);
  });
  return word;
}

function createTextArrow() {
  const arrow = document.createElement('span');
  arrow.className = 'explorer-text-arrow';
  arrow.textContent = '→';
  return arrow;
}

function buildTextChainView(chain) {
  const view = document.createElement('div');
  view.className = 'explorer-text-sequence';
  if (!chain?.length) return view;

  view.appendChild(createWordToken([{ text: chain[0], cls: '' }]));

  for (let i = 1; i < chain.length; i += 1) {
    const fragments = getEditFragments(chain[i - 1], chain[i]);
    view.appendChild(createTextArrow());
    view.appendChild(createWordToken(fragments.parts));
  }

  return view;
}

function buildExplorerTextContent(word) {
  const wrap = document.createElement('div');
  wrap.className = 'explorer-text-wrap';

  const list = document.createElement('div');
  list.className = 'explorer-text-list';

  explorerModels.forEach(mid => {
    const chain = DATA.chains[word]?.[mid];
    if (!chain || !chain.length) return;

    const item = document.createElement('div');
    item.className = 'explorer-text-chain';

    const label = document.createElement('div');
    label.className = 'explorer-text-model';

    const swatch = document.createElement('span');
    swatch.className = 'explorer-text-model-swatch';
    swatch.style.background = getModelColor(mid, explorerModels);
    label.appendChild(swatch);

    const name = document.createElement('span');
    name.textContent = modelMap[mid]?.label || mid;
    label.appendChild(name);

    const meta = document.createElement('span');
    meta.className = 'explorer-text-model-meta';
    meta.textContent = `${Math.max(chain.length - 1, 0)} steps`;
    label.appendChild(meta);

    item.appendChild(label);
    item.appendChild(buildTextChainView(chain));
    list.appendChild(item);
  });

  wrap.appendChild(list);
  return wrap;
}

function createExplorerTextPlaceholder() {
  const wrap = document.createElement('div');
  wrap.className = 'explorer-text-wrap loading';
  const placeholder = document.createElement('div');
  placeholder.className = 'explorer-text-placeholder';
  ['short', 'long', 'mid'].forEach(cls => {
    const line = document.createElement('div');
    line.className = `explorer-text-placeholder-line ${cls}`;
    placeholder.appendChild(line);
  });
  wrap.appendChild(placeholder);
  return wrap;
}

function renderExplorerGrid() {
  // Clean up previous state
  explorerPrefetchToken += 1;
  stopExplorerRAF();
  explorerVisibleCells.clear();
  Object.values(explorerCells).forEach(cell => {
    if (cell.animTimer) clearInterval(cell.animTimer);
  });
  explorerCells = {};

  const container = document.getElementById('explorer-grid-container');
  if (!container) return;
  const difficulty = DATA.metadata.word_difficulty || {};
  const words = [...DATA.metadata.starting_words].sort((a, b) => (difficulty[a] ?? -Infinity) - (difficulty[b] ?? -Infinity));

  const grid = document.createElement('div');
  grid.className = 'explorer-grid';

  words.forEach(word => {
    const cell = document.createElement('div');
    cell.className = 'explorer-cell';
    cell.id = `ecell-${word}`;

    const header = document.createElement('div');
    header.className = 'explorer-cell-header';

    const titleWrap = document.createElement('div');
    const wordLabel = document.createElement('span');
    wordLabel.className = 'explorer-cell-word';
    wordLabel.textContent = word;
    titleWrap.appendChild(wordLabel);
    header.appendChild(titleWrap);

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '6px';
    actions.style.alignItems = 'center';

    if (explorerViewMode === '3d') {
      const playButton = document.createElement('button');
      playButton.className = 'explorer-cell-play';
      playButton.id = `eplay-${word}`;
      playButton.type = 'button';
      playButton.title = 'Replay animation';
      playButton.setAttribute('aria-label', `Replay animation for ${word}`);
      playButton.dataset.action = 'play';
      playButton.dataset.word = word;
      playButton.appendChild(createPlayIcon());
      actions.appendChild(playButton);
    }

    const maximizeButton = document.createElement('button');
    maximizeButton.className = 'explorer-cell-maximize';
    maximizeButton.type = 'button';
    maximizeButton.title = 'Open larger explorer view';
    maximizeButton.setAttribute('aria-label', `Open larger explorer view for ${word}`);
    maximizeButton.dataset.action = 'maximize';
    maximizeButton.dataset.word = word;
    maximizeButton.appendChild(createMaximizeIcon());
    actions.appendChild(maximizeButton);

    header.appendChild(actions);
    cell.appendChild(header);

    if (explorerViewMode === 'text') {
      const textHost = document.createElement('div');
      textHost.id = `etext-${word}`;
      textHost.dataset.word = word;
      textHost.appendChild(createExplorerTextPlaceholder());
      cell.appendChild(textHost);
    } else {
      const wrap = document.createElement('div');
      wrap.className = 'explorer-cell-canvas-wrap';
      wrap.id = `ewrap-${word}`;
      wrap.dataset.word = word;

      const canvas = document.createElement('canvas');
      canvas.id = `ecanvas-${word}`;
      canvas.setAttribute('aria-label', `Word graph for ${word}`);
      wrap.appendChild(canvas);
      cell.appendChild(wrap);
    }
    grid.appendChild(cell);
  });

  container.replaceChildren(grid);
  if (explorerViewMode === 'text') {
    if (window._explorerLoadObserver) window._explorerLoadObserver.disconnect();
    if (window._explorerVisObserver) window._explorerVisObserver.disconnect();
    const textObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const host = entry.target;
        const word = host.dataset.word;
        if (!word) return;
        textObserver.unobserve(host);
        host.replaceChildren(buildExplorerTextContent(word));
      });
    }, { rootMargin: '200% 0px' });
    window._explorerLoadObserver = textObserver;
    requestAnimationFrame(() => {
      words.forEach(w => {
        const host = document.getElementById(`etext-${w}`);
        if (host) textObserver.observe(host);
      });
    });
    return;
  }

  ensureThreeJS();

  // Load observer: fetch graph data for cells approaching viewport
  if (window._explorerLoadObserver) window._explorerLoadObserver.disconnect();
  const loadObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const cell = entry.target;
      const w = cell.id.replace('ecell-', '');
      loadObserver.unobserve(cell);
      preloadExplorerCell(w).then(({ graph }) => {
        if (!graph) return;
        if (document.getElementById(`ewrap-${w}`)) initExplorerCell(w, graph);
      });
    });
  }, { rootMargin: '200% 0px' });
  window._explorerLoadObserver = loadObserver;

  // Visibility observer: track which cells are on screen for the shared RAF
  if (window._explorerVisObserver) window._explorerVisObserver.disconnect();
  const visObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const w = entry.target.id.replace('ecell-', '');
      if (entry.isIntersecting) {
        explorerVisibleCells.add(w);
        startExplorerRAF();
      } else {
        explorerVisibleCells.delete(w);
        if (explorerVisibleCells.size === 0) stopExplorerRAF();
      }
    });
  }, { rootMargin: '50px 0px' });
  window._explorerVisObserver = visObserver;

  requestAnimationFrame(() => {
    words.forEach(w => {
      const cell = document.getElementById(`ecell-${w}`);
      if (cell) { loadObserver.observe(cell); visObserver.observe(cell); }
    });
  });
  startExplorerPrefetch(words);
}

function initExplorerCell(word, graph) {
  const wrap = document.getElementById(`ewrap-${word}`);
  if (!wrap) return;

  const nodes = graph.nodes;
  const edges = graph.edges;
  const n = nodes.length;

  const nodeIdx = {};
  nodes.forEach((name, i) => nodeIdx[name] = i);

  const chains = {};
  explorerModels.forEach(mid => {
    const c = DATA.chains[word]?.[mid];
    if (c) chains[mid] = c;
  });

  explorerCells[word] = {
    word, graph, wrap, nodes, edges, n,
    nodeIdx, chains,
    animTimer: null, animStep: -1,
    threeScene: null, threeCamera: null, rotationAngle: 0,
    visible: false, needsInit3D: true,
  };

  const pos3dPromise = graph?.positions_3d ? Promise.resolve(graph.positions_3d) : getGraph3d(word);
  pos3dPromise.then(pos3d => {
    const cell = explorerCells[word];
    if (!cell) return;
    buildCellThreeScene(word, pos3d);
    cell.needsInit3D = false;
    startExplorerRAF();
  });
}

// ─── Shared 3D renderer for explorer grid ───
let explorerRenderer = null;
let explorerRAFId = null;
let explorerVisibleCells = new Set();
let explorerCircleTex = null;
let explorerCircleBorderTex = null;

function getExplorerRenderer() {
  if (explorerRenderer) return explorerRenderer;
  if (!threeLoaded) return null;
  explorerRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  explorerRenderer.setPixelRatio(window.devicePixelRatio || 1);
  explorerCircleTex = createCircleTexture();
  explorerCircleBorderTex = createCircleBorderTexture();
  return explorerRenderer;
}

function buildCellThreeScene(word, pos3dData) {
  const cell = explorerCells[word];
  if (!cell) return;
  const { nodes, edges, n, nodeIdx, chains, graph } = cell;

  const pos3d = pos3dData || graph.positions.map(p => [p[0], p[1], 0]);

  // Compute bounding box and center
  let cx = 0, cy = 0, cz = 0;
  for (let i = 0; i < n; i++) { cx += pos3d[i][0]; cy += pos3d[i][1]; cz += pos3d[i][2]; }
  cx /= n; cy /= n; cz /= n;
  let ext = 0;
  for (let i = 0; i < n; i++) {
    ext = Math.max(ext,
      Math.abs(pos3d[i][0] - cx), Math.abs(pos3d[i][1] - cy), Math.abs(pos3d[i][2] - cz));
  }
  ext = ext * 2 || 1;
  const scale = 30 / ext;

  const scaledPos = pos3d.map(p => [
    (p[0] - cx) * scale, (p[1] - cy) * scale, (p[2] - cz) * scale
  ]);
  cell.scaledPos = scaledPos;

  let maxRadiusSq = 0;
  for (let i = 0; i < scaledPos.length; i += 1) {
    const [x, y, z] = scaledPos[i];
    const radiusSq = x * x + y * y + z * z;
    if (radiusSq > maxRadiusSq) maxRadiusSq = radiusSq;
  }
  cell.cameraTarget = new THREE.Vector3(0, 0, 0);
  cell.cameraFitRadius = Math.max(Math.sqrt(maxRadiusSq), 1);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(TC.threeBg);

  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
  camera.position.set(0, 0, 40);
  camera.lookAt(0, 0, 0);

  // Edges
  const edgeVerts = new Float32Array(edges.length * 6);
  for (let i = 0; i < edges.length; i++) {
    const a = edges[i][0], b = edges[i][1];
    edgeVerts[i * 6] = scaledPos[a][0]; edgeVerts[i * 6 + 1] = scaledPos[a][1]; edgeVerts[i * 6 + 2] = scaledPos[a][2];
    edgeVerts[i * 6 + 3] = scaledPos[b][0]; edgeVerts[i * 6 + 4] = scaledPos[b][1]; edgeVerts[i * 6 + 5] = scaledPos[b][2];
  }
  const edgeGeom = new THREE.BufferGeometry();
  edgeGeom.setAttribute('position', new THREE.BufferAttribute(edgeVerts, 3));
  scene.add(new THREE.LineSegments(edgeGeom, new THREE.LineBasicMaterial({
    color: TC.threeEdge, transparent: true, opacity: 0.25
  })));

  // Background nodes
  const nodeVerts = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    nodeVerts[i * 3] = scaledPos[i][0]; nodeVerts[i * 3 + 1] = scaledPos[i][1]; nodeVerts[i * 3 + 2] = scaledPos[i][2];
  }
  const nodeGeom = new THREE.BufferGeometry();
  nodeGeom.setAttribute('position', new THREE.BufferAttribute(nodeVerts, 3));
  scene.add(new THREE.Points(nodeGeom, new THREE.PointsMaterial({
    color: 0x6B9FBF, size: 0.15, transparent: true, opacity: 0.35,
    sizeAttenuation: true, map: explorerCircleTex, alphaTest: 0.5
  })));

  // Chain group (rebuilt on anim)
  const chainGroup = new THREE.Group();
  chainGroup.name = 'chains';
  scene.add(chainGroup);

  cell.threeScene = scene;
  cell.threeCamera = camera;
  cell.chainGroup = chainGroup;

  buildCellChains(word, -1);
}

function buildCellChains(word, step) {
  const cell = explorerCells[word];
  if (!cell || !cell.chainGroup) return;
  const { chainGroup, scaledPos, nodeIdx, chains } = cell;

  // Dispose old
  while (chainGroup.children.length > 0) {
    const child = chainGroup.children[0];
    if (child.geometry) child.geometry.dispose();
    if (child.material) { if (child.material.map) child.material.map.dispose(); child.material.dispose(); }
    chainGroup.remove(child);
  }

  explorerModels.forEach(mid => {
    const chain = chains[mid];
    if (!chain || chain.length < 2) return;
    const color = getModelColor(mid, explorerModels);
    const threeColor = hexToThreeColor(color);
    const maxSteps = chain.length - 1;
    const showStep = step < 0 ? maxSteps : Math.min(step, maxSteps);
    const drawCount = Math.min(showStep + 1, chain.length);
    if (drawCount < 2) return;

    // Cylinders for chain edges
    for (let i = 0; i < drawCount - 1; i++) {
      const idxA = nodeIdx[chain[i]], idxB = nodeIdx[chain[i + 1]];
      if (idxA == null || idxB == null) continue;
      const pA = new THREE.Vector3(...scaledPos[idxA]);
      const pB = new THREE.Vector3(...scaledPos[idxB]);
      const dist = pA.distanceTo(pB);
      if (dist < 0.0001) continue;
      const geom = new THREE.CylinderGeometry(0.035, 0.035, dist, 6, 1, false);
      const mesh = new THREE.Mesh(geom, new THREE.MeshBasicMaterial({ color: threeColor }));
      mesh.position.copy(pA).lerp(pB, 0.5);
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), pB.clone().sub(pA).normalize());
      chainGroup.add(mesh);
    }

    // Chain node dots
    const verts = new Float32Array(drawCount * 3);
    let vi = 0;
    for (let i = 0; i < drawCount; i++) {
      const idx = nodeIdx[chain[i]];
      if (idx != null) { verts[vi++] = scaledPos[idx][0]; verts[vi++] = scaledPos[idx][1]; verts[vi++] = scaledPos[idx][2]; }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(verts.slice(0, vi), 3));
    chainGroup.add(new THREE.Points(g, new THREE.PointsMaterial({
      color: threeColor, size: 0.35, sizeAttenuation: true,
      map: explorerCircleTex, alphaTest: 0.5
    })));

    // Head marker
    if (drawCount > 1) {
      const headIdx = nodeIdx[chain[drawCount - 1]];
      if (headIdx != null) {
        const hg = new THREE.BufferGeometry();
        hg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(scaledPos[headIdx]), 3));
        chainGroup.add(new THREE.Points(hg, new THREE.PointsMaterial({
          color: threeColor, size: 0.5, sizeAttenuation: true,
          map: explorerCircleTex, alphaTest: 0.5
        })));
        const hg2 = new THREE.BufferGeometry();
        hg2.setAttribute('position', new THREE.BufferAttribute(new Float32Array(scaledPos[headIdx]), 3));
        chainGroup.add(new THREE.Points(hg2, new THREE.PointsMaterial({
          color: 0xffffff, size: 0.65, sizeAttenuation: true,
          map: explorerCircleBorderTex, alphaTest: 0.5, transparent: true
        })));
      }
    }
  });
}

let explorerLastRendererW = 0, explorerLastRendererH = 0;
let explorerLastPixelRatio = 0;

function startExplorerRAF() {
  if (explorerRAFId) return;
  function animate() {
    explorerRAFId = requestAnimationFrame(animate);
    const renderer = getExplorerRenderer();
    if (!renderer) return;
    const pixelRatio = window.devicePixelRatio || 1;

    explorerVisibleCells.forEach(word => {
      const cell = explorerCells[word];
      if (!cell || !cell.threeScene || !cell.threeCamera) return;
      const wrap = cell.wrap;
      const rect = wrap.getBoundingClientRect();
      const w = Math.max(1, Math.round(rect.width));
      const h = Math.max(1, Math.round(rect.height));
      if (!w || !h) return;

      // Auto-rotate
      cell.rotationAngle = (cell.rotationAngle || 0) + 0.004;
      cell.threeCamera.aspect = w / h;
      const fitRadius = cell.cameraFitRadius || 1;
      const vFov = THREE.MathUtils.degToRad(cell.threeCamera.fov);
      const hFov = 2 * Math.atan(Math.tan(vFov / 2) * cell.threeCamera.aspect);
      const fitDistance = Math.max(
        fitRadius / Math.tan(vFov / 2),
        fitRadius / Math.tan(hFov / 2),
      ) * 1.15;
      cell.threeCamera.position.set(
        fitDistance * Math.sin(cell.rotationAngle),
        0,
        fitDistance * Math.cos(cell.rotationAngle)
      );
      cell.threeCamera.lookAt(cell.cameraTarget);
      cell.threeCamera.updateProjectionMatrix();

      if (pixelRatio !== explorerLastPixelRatio) {
        renderer.setPixelRatio(pixelRatio);
        explorerLastPixelRatio = pixelRatio;
        explorerLastRendererW = 0;
        explorerLastRendererH = 0;
      }
      if (w !== explorerLastRendererW || h !== explorerLastRendererH) {
        renderer.setSize(w, h, false);
        explorerLastRendererW = w;
        explorerLastRendererH = h;
      }
      renderer.render(cell.threeScene, cell.threeCamera);

      // Copy to the cell's canvas
      if (!cell._ctx2d) {
        const canvas = document.getElementById(`ecanvas-${word}`);
        if (canvas) {
          canvas.style.width = '100%';
          canvas.style.height = '100%';
          cell._ctx2d = canvas.getContext('2d');
          cell._canvas = canvas;
        }
      }
      if (cell._ctx2d) {
        const targetWidth = Math.max(1, Math.round(w * pixelRatio));
        const targetHeight = Math.max(1, Math.round(h * pixelRatio));
        if (cell._canvas.width !== targetWidth || cell._canvas.height !== targetHeight) {
          cell._canvas.width = targetWidth;
          cell._canvas.height = targetHeight;
        }
        cell._ctx2d.setTransform(1, 0, 0, 1, 0, 0);
        cell._ctx2d.clearRect(0, 0, cell._canvas.width, cell._canvas.height);
        cell._ctx2d.drawImage(
          renderer.domElement,
          0,
          0,
          renderer.domElement.width,
          renderer.domElement.height,
          0,
          0,
          cell._canvas.width,
          cell._canvas.height,
        );
      }
    });
  }
  animate();
}

function stopExplorerRAF() {
  if (explorerRAFId) { cancelAnimationFrame(explorerRAFId); explorerRAFId = null; }
}

function playExplorerCell(word) {
  const cell = explorerCells[word];
  if (!cell || !cell.threeScene) return;

  if (cell.animTimer) {
    clearInterval(cell.animTimer);
    cell.animTimer = null;
    cell.animStep = -1;
    buildCellChains(word, -1);
    setButtonIcon(document.getElementById(`eplay-${word}`), createPlayIcon);
    return;
  }

  let maxLen = 0;
  explorerModels.forEach(mid => {
    const c = cell.chains[mid];
    if (c) maxLen = Math.max(maxLen, c.length);
  });
  if (maxLen <= 1) return;

  cell.animStep = 0;
  setButtonIcon(document.getElementById(`eplay-${word}`), createPauseIcon);

  cell.animTimer = setInterval(() => {
    cell.animStep++;
    buildCellChains(word, cell.animStep);
    if (cell.animStep >= maxLen) {
      clearInterval(cell.animTimer);
      cell.animTimer = null;
      cell.animStep = -1;
      setButtonIcon(document.getElementById(`eplay-${word}`), createPlayIcon);
    }
  }, ANIMATION_INTERVAL);
}

// ─── Explorer Modal ───
let modalState = null;
let modalResizeObserver = null;

function getModalFocusableElements() {
  const dialog = document.getElementById('explorer-modal');
  if (!dialog) return [];
  return [...dialog.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
    .filter(element => !element.closest('[hidden]'));
}

function renderModalMeta(word) {
  const meta = document.getElementById('modal-meta');
  if (!meta) return;
  meta.replaceChildren();
}

function initModalHandlers() {
  const overlay = document.getElementById('explorer-modal-overlay');
  const modalBody = document.getElementById('modal-body');
  const legend = document.getElementById('modal-legend');
  if (!overlay || overlay.dataset.bound) return;

  overlay.addEventListener('click', event => {
    if (event.target === overlay) closeExplorerModal();
  });
  document.getElementById('modal-close')?.addEventListener('click', () => closeExplorerModal());
  document.getElementById('modal-play')?.addEventListener('click', playModalAnimation);
  document.getElementById('modal-prev')?.addEventListener('click', () => navigateModal(-1));
  document.getElementById('modal-next')?.addEventListener('click', () => navigateModal(1));
  document.getElementById('modal-bg-toggle')?.addEventListener('change', toggleModalBG);
  document.getElementById('modal-labels-toggle')?.addEventListener('change', toggleModalLabels);
  document.getElementById('modal-autorotate-toggle')?.addEventListener('change', toggleModalAutoRotate);
  document.getElementById('modal-density-toggle')?.addEventListener('change', toggleModalDensity);
  legend?.addEventListener('click', event => {
    const item = event.target.closest('.modal-legend-item');
    if (!item || !modalState) return;
    const mid = item.dataset.mid;
    if (!mid) return;
    if (modalState.hiddenModels.has(mid)) {
      modalState.hiddenModels.delete(mid);
      item.classList.remove('hidden');
      item.setAttribute('aria-pressed', 'true');
    } else {
      modalState.hiddenModels.add(mid);
      item.classList.add('hidden');
      item.setAttribute('aria-pressed', 'false');
    }
    if (modalState.threeState) {
      modalState.threeState.buildChains(modalState.animStep);
      modalState.threeState.needsRender();
    }
  });
  document.addEventListener('keydown', modalKeyHandler);

  if (modalBody && !modalResizeObserver) {
    modalResizeObserver = new ResizeObserver(() => {
      if (!modalState) return;
      if (modalState.threeState?.onResize) {
        modalState.threeState.onResize();
      }
    });
    modalResizeObserver.observe(modalBody);
  }

  overlay.dataset.bound = 'true';
}

function getExplorerWordList() {
  const difficulty = DATA.metadata.word_difficulty || {};
  return [...DATA.metadata.starting_words].sort((a, b) => (difficulty[a] ?? -Infinity) - (difficulty[b] ?? -Infinity));
}

function navigateModal(dir) {
  if (!modalState) return;
  const words = getExplorerWordList();
  const curIdx = words.indexOf(modalState.word);
  if (curIdx < 0) return;
  const nextIdx = (curIdx + dir + words.length) % words.length;
  const carry = {
    hiddenModels: new Set(modalState.hiddenModels),
    showBG: modalState.showBG,
    showLabels: modalState.showLabels,
    showDensity: modalState.showDensity,
    autoRotate: modalState.threeState?.controls?.autoRotate ?? true,
  };
  openExplorerModal(words[nextIdx], { carry });
}

function openExplorerModal(word, options = {}) {
  if (modalState) closeExplorerModal({ updateHistory: false, restoreFocus: false });

  const graph = getGraphSync(word);
  if (!graph) {
    getGraph(word).then(loadedGraph => {
      if (loadedGraph) openExplorerModal(word, options);
    });
    return;
  }

  const overlay = document.getElementById('explorer-modal-overlay');
  const dialog = document.getElementById('explorer-modal');
  const appShell = document.getElementById('app-shell');
  if (!overlay || !dialog) return;

  const nodes = graph.nodes;
  const edges = graph.edges;
  const n = nodes.length;
  const nodeIdx = {};
  nodes.forEach((name, index) => nodeIdx[name] = index);

  const chains = {};
  explorerModels.forEach(mid => {
    const chain = DATA.chains[word]?.[mid];
    if (chain) chains[mid] = chain;
  });

  const carry = options.carry || null;
  modalState = {
    word,
    graph,
    nodes,
    edges,
    n,
    nodeIdx,
    chains,
    is3D: true,
    showBG: carry ? carry.showBG : true,
    showLabels: carry ? carry.showLabels : true,
    showDensity: carry ? carry.showDensity : false,
    animStep: -1,
    animTimer: null,
    hoverIdx: -1,
    hiddenModels: carry ? carry.hiddenModels : new Set(),
    restoreFocusEl: document.activeElement instanceof HTMLElement ? document.activeElement : null,
    _carryAutoRotate: carry ? carry.autoRotate : true,
  };

  document.getElementById('modal-word').textContent = word;
  renderModalMeta(word);
  document.getElementById('modal-bg-toggle').checked = modalState.showBG;
  document.getElementById('modal-labels-toggle').checked = modalState.showLabels;
  document.getElementById('modal-autorotate-toggle').checked = modalState._carryAutoRotate;
  document.getElementById('modal-density-toggle').checked = modalState.showDensity;
  setButtonIcon(document.getElementById('modal-play'), createPlayIcon);
  buildModalLegend();

  overlay.hidden = false;
  overlay.classList.add('open');
  document.body.classList.add('modal-open');
  appShell?.setAttribute('aria-hidden', 'true');

  requestAnimationFrame(() => {
    if (!modalState) return;
    ensureThreeJS().then(() => {
      if (!modalState || modalState.word !== word) return;
      renderModal3D();
      document.getElementById('modal-close')?.focus();
    });
  });

  if (options.updateHistory !== false) {
    syncURLState();
  }
}

function toggleModalLabels(e) {
  if (!modalState || !modalState.threeState) return;
  modalState.showLabels = e.target.checked;
  if (!modalState.showLabels) modalState.threeState.clearLabels?.();
  else modalState.threeState.markLabelsDirty?.();
  modalState.threeState.needsRender();
}

function toggleModalBG(e) {
  if (!modalState || !modalState.threeState) return;
  modalState.showBG = e.target.checked;
  const ts = modalState.threeState;
  ts.pointCloud.visible = modalState.showBG;
  ts.edgeLines.visible = modalState.showBG;
  ts.needsRender();
}

function toggleModalAutoRotate(e) {
  if (!modalState || !modalState.threeState?.controls) return;
  modalState.threeState.controls.autoRotate = e.target.checked;
  modalState.threeState.needsRender();
}

function toggleModalDensity(e) {
  if (!modalState || !modalState.threeState) return;
  modalState.showDensity = e.target.checked;
  modalState.threeState.buildChains(modalState.animStep);
  modalState.threeState.needsRender();
}

function closeExplorerModal(options = {}) {
  const restoreFocusEl = options.restoreFocus === false ? null : modalState?.restoreFocusEl;
  if (modalState?.animTimer) clearInterval(modalState.animTimer);
  disposeThreeState();

  const overlay = document.getElementById('explorer-modal-overlay');
  const container = document.getElementById('modal-3d-container');
  const legend = document.getElementById('modal-legend');
  const tooltip = document.getElementById('modal-tooltip');
  const appShell = document.getElementById('app-shell');
  if (overlay) {
    overlay.classList.remove('open');
    overlay.hidden = true;
  }
  if (container) {
    container.replaceChildren();
    container.classList.remove('active');
  }
  if (legend) legend.replaceChildren();
  if (tooltip) tooltip.style.display = 'none';
  document.body.classList.remove('modal-open');
  appShell?.removeAttribute('aria-hidden');
  modalState = null;
  setButtonIcon(document.getElementById('modal-play'), createPlayIcon);
  if (restoreFocusEl?.focus) restoreFocusEl.focus();
  if (options.updateHistory !== false) {
    syncURLState();
  }
}

function modalKeyHandler(e) {
  if (!modalState) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    closeExplorerModal();
    return;
  }
  if (e.key === 'ArrowLeft') { e.preventDefault(); navigateModal(-1); return; }
  if (e.key === 'ArrowRight') { e.preventDefault(); navigateModal(1); return; }
  if (e.key !== 'Tab') return;

  const focusable = getModalFocusableElements();
  if (!focusable.length) {
    e.preventDefault();
    document.getElementById('explorer-modal')?.focus();
    return;
  }

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}



function buildModalLegend() {
  if (!modalState) return;
  const legendDiv = document.getElementById('modal-legend');
  if (!legendDiv) return;
  const { chains, hiddenModels } = modalState;
  legendDiv.replaceChildren();

  explorerModels.forEach(mid => {
    const model = modelMap[mid];
    const chain = chains[mid];
    if (!model || !chain) return;

    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'modal-legend-item';
    item.dataset.mid = mid;
    item.setAttribute('aria-pressed', hiddenModels.has(mid) ? 'false' : 'true');
    if (hiddenModels.has(mid)) item.classList.add('hidden');

    const swatch = document.createElement('span');
    swatch.className = 'legend-swatch';
    swatch.style.background = getModelColor(mid, explorerModels);
    item.appendChild(swatch);

    const label = document.createElement('span');
    label.className = 'legend-label';
    label.textContent = `${model.label} (${chain.length})`;
    item.appendChild(label);

    legendDiv.appendChild(item);
  });
}


// ─── 3D Mode (Three.js) ───
function disposeThreeState() {
  if (!modalState?.threeState) return;
  const ts = modalState.threeState;
  if (ts.cleanup) ts.cleanup();
  if (ts.rafId) cancelAnimationFrame(ts.rafId);
  if (ts.controls) ts.controls.dispose();
  if (ts.renderer) {
    ts.renderer.dispose();
    ts.renderer.domElement.remove();
  }
  if (ts.scene) {
    ts.scene.traverse(obj => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
    });
  }
  modalState.threeState = null;
}


// Helper: create a circular point texture for Three.js
function createCircleTexture(size = 64) {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  const half = size / 2;
  ctx.beginPath();
  ctx.arc(half, half, half - 1, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

// Helper: create a circular point with a border for the head node
function createCircleBorderTexture(size = 64) {
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  const half = size / 2;
  ctx.beginPath();
  ctx.arc(half, half, half - 3, 0, Math.PI * 2);
  ctx.lineWidth = 4;
  ctx.strokeStyle = TC.headBorder;
  ctx.stroke();
  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

function hexToThreeColor(hex) {
  return new THREE.Color(hex);
}

function renderModal3D() {
  if (!modalState) return;
  const word = modalState.word;
  const container = document.getElementById('modal-3d-container');
  if (!container) return;

  // Load 3D positions on demand
  getGraph3d(word).then(pos3d => {
    if (!modalState || modalState.word !== word) return;  // modal was closed/changed
    _renderModal3DWithPositions(pos3d);
  });
}

function _renderModal3DWithPositions(pos3dData) {
  if (!modalState) return;
  const { graph, nodes, edges, n, nodeIdx, chains } = modalState;
  const container = document.getElementById('modal-3d-container');
  if (!container) return;

  // Dispose previous if any
  disposeThreeState();
  container.replaceChildren();

  const pos3d = pos3dData || graph.positions.map(p => [p[0], p[1], 0]);

  // Compute bounding box and center
  let cx = 0, cy = 0, cz = 0;
  let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity, zMin = Infinity, zMax = -Infinity;
  for (let i = 0; i < n; i++) {
    const p = pos3d[i];
    cx += p[0]; cy += p[1]; cz += p[2];
    if (p[0] < xMin) xMin = p[0]; if (p[0] > xMax) xMax = p[0];
    if (p[1] < yMin) yMin = p[1]; if (p[1] > yMax) yMax = p[1];
    if (p[2] < zMin) zMin = p[2]; if (p[2] > zMax) zMax = p[2];
  }
  cx /= n; cy /= n; cz /= n;
  const extent = Math.max(xMax - xMin, yMax - yMin, zMax - zMin) || 1;
  const scale = 30 / extent;

  // Setup scene
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(TC.threeBg);

  const width = container.clientWidth;
  const height = container.clientHeight;
  const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 2000);
  camera.position.set(0, 0, 40);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  // OrbitControls for rotate/zoom/pan
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.12;
  controls.enablePan = true;
  controls.enableZoom = true;
  controls.rotateSpeed = 0.8;
  controls.zoomSpeed = 1.2;
  controls.panSpeed = 0.5;
  controls.target.set(0, 0, 0);
  controls.autoRotate = document.getElementById('modal-autorotate-toggle')?.checked ?? true;
  controls.autoRotateSpeed = 1.0;

  // Scaled positions
  const scaledPos = pos3d.map(p => [
    (p[0] - cx) * scale,
    (p[1] - cy) * scale,
    (p[2] - cz) * scale
  ]);

  // ─── Edges (LineSegments for performance — single draw call) ───
  const edgeVerts = new Float32Array(edges.length * 6);
  for (let i = 0; i < edges.length; i++) {
    const a = edges[i][0], b = edges[i][1];
    edgeVerts[i * 6] = scaledPos[a][0];
    edgeVerts[i * 6 + 1] = scaledPos[a][1];
    edgeVerts[i * 6 + 2] = scaledPos[a][2];
    edgeVerts[i * 6 + 3] = scaledPos[b][0];
    edgeVerts[i * 6 + 4] = scaledPos[b][1];
    edgeVerts[i * 6 + 5] = scaledPos[b][2];
  }
  const edgeGeom = new THREE.BufferGeometry();
  edgeGeom.setAttribute('position', new THREE.BufferAttribute(edgeVerts, 3));
  const edgeMat = new THREE.LineBasicMaterial({
    color: TC.threeEdge, transparent: true, opacity: 0.25
  });
  const edgeLines = new THREE.LineSegments(edgeGeom, edgeMat);
  edgeLines.visible = modalState.showBG;
  scene.add(edgeLines);

  // ─── Background Nodes (Points — single draw call) ───
  const nodeVerts = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    nodeVerts[i * 3] = scaledPos[i][0];
    nodeVerts[i * 3 + 1] = scaledPos[i][1];
    nodeVerts[i * 3 + 2] = scaledPos[i][2];
  }
  const circleTexture = createCircleTexture();
  const circleBorderTexture = createCircleBorderTexture();
  const nodeGeom = new THREE.BufferGeometry();
  nodeGeom.setAttribute('position', new THREE.BufferAttribute(nodeVerts, 3));
  const nodeMat = new THREE.PointsMaterial({
    color: 0x6B9FBF, size: 0.15, transparent: true, opacity: 0.35,
    sizeAttenuation: true, map: circleTexture, alphaTest: 0.5
  });
  const pointCloud = new THREE.Points(nodeGeom, nodeMat);
  pointCloud.visible = modalState.showBG;
  scene.add(pointCloud);

  // ─── Node density values (experimental) ───
  // KDE-style: for each node, sum Gaussian contributions from all neighbors
  const densityValues = new Float32Array(n);
  const bandwidth = 3.0;
  const bw2 = bandwidth * bandwidth;
  for (let i = 0; i < n; i++) {
    let sum = 0;
    const xi = scaledPos[i][0], yi = scaledPos[i][1], zi = scaledPos[i][2];
    for (let j = 0; j < n; j++) {
      if (i === j) continue;
      const dx = xi - scaledPos[j][0];
      const dy = yi - scaledPos[j][1];
      const dz = zi - scaledPos[j][2];
      sum += Math.exp(-(dx * dx + dy * dy + dz * dz) / (2 * bw2));
    }
    densityValues[i] = sum;
  }
  let dMin = Infinity, dMax = -Infinity;
  for (let i = 0; i < n; i++) {
    if (densityValues[i] < dMin) dMin = densityValues[i];
    if (densityValues[i] > dMax) dMax = densityValues[i];
  }
  const dRange = dMax - dMin || 1;

  // Color ramp: cool blue → cyan → green → yellow → red
  function densityColor(t) {
    const stops = [
      [0.0,  0.15, 0.20, 0.60],
      [0.25, 0.10, 0.55, 0.75],
      [0.5,  0.20, 0.80, 0.40],
      [0.75, 0.90, 0.85, 0.15],
      [1.0,  0.95, 0.20, 0.10],
    ];
    let lo = stops[0], hi = stops[stops.length - 1];
    for (let s = 0; s < stops.length - 1; s++) {
      if (t >= stops[s][0] && t <= stops[s + 1][0]) { lo = stops[s]; hi = stops[s + 1]; break; }
    }
    const f = (t - lo[0]) / (hi[0] - lo[0] || 1);
    return [lo[1] + (hi[1] - lo[1]) * f, lo[2] + (hi[2] - lo[2]) * f, lo[3] + (hi[3] - lo[3]) * f];
  }

  // ─── Canvas Label Overlay ───
  const labelsCanvas = document.createElement('canvas');
  labelsCanvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:5;';
  container.appendChild(labelsCanvas);
  const labelsCtx = labelsCanvas.getContext('2d');
  const labelPixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  const visitedIndices = [];
  const visitedMask = new Uint8Array(n);
  const highlightedMask = new Uint8Array(n);
  let labelsDirty = true;
  if (chains) {
    Object.values(chains).forEach(chain => {
      if (!chain) return;
      chain.forEach(word => {
        const idx = nodeIdx[word];
        if (idx == null || visitedMask[idx]) return;
        visitedMask[idx] = 1;
        visitedIndices.push(idx);
      });
    });
  }

  function resizeLabelsCanvas() {
    const widthPx = Math.max(1, container.clientWidth);
    const heightPx = Math.max(1, container.clientHeight);
    labelsCanvas.width = Math.round(widthPx * labelPixelRatio);
    labelsCanvas.height = Math.round(heightPx * labelPixelRatio);
    labelsCtx.setTransform(labelPixelRatio, 0, 0, labelPixelRatio, 0, 0);
    labelsCtx.textAlign = 'center';
    labelsCtx.textBaseline = 'bottom';
    labelsDirty = true;
  }

  function clearLabels() {
    labelsCtx.clearRect(0, 0, container.clientWidth, container.clientHeight);
  }

  resizeLabelsCanvas();

  // ─── Chain paths + labels for selected models ───
  const chainGroup = new THREE.Group();
  chainGroup.name = 'chains';
  scene.add(chainGroup);

  function buildChains(step) {
    // Remove old chain objects
    while (chainGroup.children.length > 0) {
      const child = chainGroup.children[0];
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (child.material.map) child.material.map.dispose();
        child.material.dispose();
      }
      chainGroup.remove(child);
    }

    highlightedMask.fill(0);

    explorerModels.forEach(mid => {
      const chain = chains[mid];
      if (!chain || chain.length < 2) return;
      if (modalState.hiddenModels?.has(mid)) return;
      const color = getModelColor(mid, explorerModels);
      const threeColor = hexToThreeColor(color);
      const maxSteps = chain.length - 1;
      const showStep = step < 0 ? maxSteps : Math.min(step, maxSteps);
      const drawCount = Math.min(showStep + 1, chain.length);
      if (drawCount < 2) return;

      // Chain line (drawn using cylinders for true 3D thickness)
      const useDensity = modalState.showDensity;
      for (let i = 0; i < drawCount - 1; i++) {
        const idxA = nodeIdx[chain[i]];
        const idxB = nodeIdx[chain[i + 1]];
        if (idxA != null && idxB != null) {
          const pA = new THREE.Vector3(scaledPos[idxA][0], scaledPos[idxA][1], scaledPos[idxA][2]);
          const pB = new THREE.Vector3(scaledPos[idxB][0], scaledPos[idxB][1], scaledPos[idxB][2]);
          const distance = pA.distanceTo(pB);
          if (distance > 0.0001) {
            let cylColor = threeColor;
            if (useDensity) {
              const tMid = ((densityValues[idxA] + densityValues[idxB]) / 2 - dMin) / dRange;
              const [r, g, b] = densityColor(tMid);
              cylColor = new THREE.Color(r, g, b);
            }
            const cylinderGeom = new THREE.CylinderGeometry(0.035, 0.035, distance, 6, 1, false);
            const lineMat = new THREE.MeshBasicMaterial({ color: cylColor });
            const mesh = new THREE.Mesh(cylinderGeom, lineMat);
            mesh.position.copy(pA).lerp(pB, 0.5);
            mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), pB.clone().sub(pA).normalize());
            chainGroup.add(mesh);
          }
        }
      }

      // Chain node markers (all but head)
      const chainNodeVerts = new Float32Array(drawCount * 3);
      let vi = 0;
      for (let i = 0; i < drawCount; i++) {
        const idx = nodeIdx[chain[i]];
        if (idx != null) {
          chainNodeVerts[vi++] = scaledPos[idx][0];
          chainNodeVerts[vi++] = scaledPos[idx][1];
          chainNodeVerts[vi++] = scaledPos[idx][2];
        }
      }
      const chainNodeGeom = new THREE.BufferGeometry();
      const usedVerts = chainNodeVerts.slice(0, vi);
      chainNodeGeom.setAttribute('position', new THREE.BufferAttribute(usedVerts, 3));
      if (useDensity) {
        // Per-vertex density colors for chain nodes
        const nc = vi / 3;
        const cnColors = new Float32Array(nc * 3);
        for (let ci = 0; ci < nc; ci++) {
          const nIdx = nodeIdx[chain[ci]];
          const t = nIdx != null ? (densityValues[nIdx] - dMin) / dRange : 0;
          const [r, g, b] = densityColor(t);
          cnColors[ci * 3] = r; cnColors[ci * 3 + 1] = g; cnColors[ci * 3 + 2] = b;
        }
        chainNodeGeom.setAttribute('color', new THREE.BufferAttribute(cnColors, 3));
      }
      const chainNodeMat = new THREE.PointsMaterial({
        size: 0.35, sizeAttenuation: true,
        map: circleTexture, alphaTest: 0.5,
        ...(useDensity ? { vertexColors: true } : { color: threeColor })
      });
      chainGroup.add(new THREE.Points(chainNodeGeom, chainNodeMat));

      // Head node marker (larger with border)
      if (drawCount > 1) {
        const headIdx = nodeIdx[chain[drawCount - 1]];
        if (headIdx != null) {
          const headGeom = new THREE.BufferGeometry();
          const hArr = new Float32Array([scaledPos[headIdx][0], scaledPos[headIdx][1], scaledPos[headIdx][2]]);
          headGeom.setAttribute('position', new THREE.BufferAttribute(hArr, 3));
          // White color base so the texture defines the look, but we tint it with vertex colors or just draw another point.
          // Wait, the texture represents the node. The texture is white on inside, F4F2EC on border.
          // We tint the material to model color, so the border gets tinted too!
          // To avoid tinting the border, we can draw two Points.
          // 1) The colored circle
          let headColor = threeColor;
          if (useDensity) {
            const tH = (densityValues[headIdx] - dMin) / dRange;
            const [rH, gH, bH] = densityColor(tH);
            headColor = new THREE.Color(rH, gH, bH);
          }
          const headColorMat = new THREE.PointsMaterial({
            color: headColor, size: 0.5, sizeAttenuation: true,
            map: circleTexture, alphaTest: 0.5
          });
          chainGroup.add(new THREE.Points(headGeom, headColorMat));
          // 2) The border ring
          const headBorderMat = new THREE.PointsMaterial({
            color: 0xffffff, size: 0.5, sizeAttenuation: true,
            map: circleBorderTexture, alphaTest: 0.5, depthTest: false
          });
          chainGroup.add(new THREE.Points(headGeom, headBorderMat));
        }
      }

      for (let i = 0; i < drawCount; i++) {
        const idx = nodeIdx[chain[i]];
        if (idx != null && highlightedMask[idx] === 0) {
          highlightedMask[idx] = 1;
        }
      }
    });
    labelsDirty = true;
  }

  buildChains(modalState.animStep);

  // ─── Raycaster for hover ───
  const raycaster = new THREE.Raycaster();
  raycaster.params.Points.threshold = 0.3;
  const mouse = new THREE.Vector2();
  let hoveredIdx = -1;

  renderer.domElement.addEventListener('mousemove', (e) => {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(pointCloud);
    const tooltip = document.getElementById('modal-tooltip');
    let nextHoveredIdx = -1;
    for (let ii = 0; ii < intersects.length; ii++) {
      const idx = intersects[ii].index;
      if (idx != null && idx < nodes.length && visitedMask[idx]) {
        nextHoveredIdx = idx;
        tooltip.textContent = nodes[idx];
        tooltip.style.display = 'block';
        tooltip.style.left = (e.clientX - rect.left + 14) + 'px';
        tooltip.style.top = (e.clientY - rect.top - 10) + 'px';
        break;
      }
    }
    if (nextHoveredIdx === -1) {
      tooltip.style.display = 'none';
    }
    if (nextHoveredIdx !== hoveredIdx) {
      hoveredIdx = nextHoveredIdx;
      labelsDirty = true;
      needsRender = true;
    }
  });

  renderer.domElement.addEventListener('mouseleave', () => {
    const tooltip = document.getElementById('modal-tooltip');
    if (tooltip) tooltip.style.display = 'none';
    if (hoveredIdx !== -1) {
      hoveredIdx = -1;
      labelsDirty = true;
      needsRender = true;
    }
  });

  // ─── Legend overlay (reuse shared modal legend) ───
  // The shared legend in #modal-legend handles both 2D and 3D

  // ─── Animation loop (60FPS) ───
  let needsRender = true;
  controls.addEventListener('change', () => { needsRender = true; labelsDirty = true; });

  const tempV = new THREE.Vector3();
  function updateLabels() {
    if (!modalState?.showLabels) {
      clearLabels();
      return;
    }
    clearLabels();
    const width = container.clientWidth;
    const height = container.clientHeight;
    const halfW = width / 2;
    const halfH = height / 2;
    const margin = 20;
    const isAnimating = modalState.animStep >= 0;

    // Build visible node set from non-hidden model chains
    const visibleMask = new Uint8Array(n);
    explorerModels.forEach(mid => {
      if (modalState.hiddenModels?.has(mid)) return;
      const chain = chains[mid];
      if (!chain) return;
      chain.forEach(w => {
        const idx = nodeIdx[w];
        if (idx != null) visibleMask[idx] = 1;
      });
    });

    labelsCtx.fillStyle = TC.text;
    labelsCtx.font = "400 9px 'JetBrains Mono', monospace";

    for (let idx = 0; idx < n; idx++) {
      if (!visibleMask[idx]) continue;
      if (isAnimating && !highlightedMask[idx]) continue;

      const px = scaledPos[idx][0], py = scaledPos[idx][1], pz = scaledPos[idx][2];
      tempV.set(px, py + 0.1, pz);
      tempV.project(camera);
      if (tempV.z < -1 || tempV.z > 1) continue;

      const x = (tempV.x * halfW) + halfW;
      const y = -(tempV.y * halfH) + halfH;
      if (x < -margin || x > width + margin || y < -margin || y > height + margin) continue;

      labelsCtx.fillText(nodes[idx], x, y - 4);
    }
  }

  function animate(now = performance.now()) {
    const ts = modalState?.threeState;
    if (!ts || ts.disposed) return;
    ts.rafId = requestAnimationFrame(animate);
    controls.update();

    // If auto-rotate is on, we are continuously moving the camera, so we always need a render
    if (ts.controls && ts.controls.autoRotate) {
      needsRender = true;
      labelsDirty = true;
    }

    if (needsRender) {
      renderer.render(scene, camera);
      if (labelsDirty) {
        updateLabels();
        labelsDirty = false;
      }
      needsRender = false;
    }
  }

  // Handle resize
  function onResize() {
    if (!modalState?.threeState) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    resizeLabelsCanvas();
    needsRender = true;
  }
  window.addEventListener('resize', onResize);

  // Store state
  modalState.threeState = {
    scene, camera, renderer, controls, pointCloud, edgeLines, chainGroup,
    scaledPos, buildChains, nodes, raycaster,
    rafId: null, disposed: false,
    needsRender: () => { needsRender = true; },
    clearLabels,
    markLabelsDirty: () => { labelsDirty = true; },
    onResize, cleanup: () => { window.removeEventListener('resize', onResize); }
  };

  // Start render loop
  animate();
}

// ─── Modal Animation ───
function playModalAnimation() {
  if (!modalState) return;
  const btn = document.getElementById('modal-play');

  // If already playing, stop
  if (modalState.animTimer) {
    clearInterval(modalState.animTimer);
    modalState.animTimer = null;
    modalState.animStep = -1;
    setButtonIcon(btn, createPlayIcon);
    if (modalState.threeState) {
      modalState.threeState.buildChains(-1);
      modalState.threeState.needsRender();
    }
    return;
  }

  let maxLen = 0;
  explorerModels.forEach(mid => {
    const c = modalState.chains[mid];
    if (c) maxLen = Math.max(maxLen, c.length);
  });
  if (maxLen <= 1) return;

  modalState.animStep = 0;
  setButtonIcon(btn, createPauseIcon);

  modalState.animTimer = setInterval(() => {
    modalState.animStep++;
    if (modalState.threeState) {
      modalState.threeState.buildChains(modalState.animStep);
      modalState.threeState.needsRender();
    }
    if (modalState.animStep >= maxLen) {
      clearInterval(modalState.animTimer);
      modalState.animTimer = null;
      modalState.animStep = -1;
      setButtonIcon(btn, createPlayIcon);
    }
  }, ANIMATION_INTERVAL);
}
