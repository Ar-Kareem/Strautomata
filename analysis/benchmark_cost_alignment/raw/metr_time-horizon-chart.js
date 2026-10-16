const SHOW_CONFIDENCE_AREA = false; // Set to true to show shaded confidence interval
const SATURATION_THRESHOLD = 16; // hours - measurements above this are unreliable

// Chart constants
const TREND_LINE_POINTS = 120; // Number of points for smooth trend line
const CONFIDENCE_INTERVAL_T_VALUE = 1.96; // 95% confidence interval
const LABEL_RADIUS = 6; // Radius for data point dots
const LABEL_RADIUS_NARROW = 5; // Smaller radius for narrow mobile screens
const ERROR_BAR_CAP_WIDTH = 8;
const RESIZE_DEBOUNCE_DELAY = 250; // ms

let ANIMATION_DURATION = 750; // ms
let chartClickHandler = null;
const AUTO_SWITCH_ANIMATION_DURATION = 1500; // ms - slower transition for auto-switch

const CHART_TEXT = typeof timeHorizonChartI18n !== 'undefined' ? timeHorizonChartI18n : {};
const CHART_LOCALE = CHART_TEXT.lang || 'en';

function chartText(key, fallback) {
  return CHART_TEXT[key] || fallback;
}

function interpolateText(template, values = {}) {
  return Object.entries(values).reduce(
    (text, [key, value]) => text.split(`{${key}}`).join(value),
    template
  );
}

function appendLocalizedTspan(textSelection, line, x, dy = null, className = null) {
  const tspan = textSelection.append('tspan')
    .attr('x', x);
  if (dy) tspan.attr('dy', dy);
  if (className) tspan.attr('class', className);

  const parts = line.split('{prob}');
  if (parts.length === 1) {
    tspan.text(line);
    return tspan;
  }

  tspan.text(parts[0]);
  tspan.append('tspan')
    .attr('class', 'current-probability')
    .text(probabilityText(currentProbability));
  tspan.append('tspan').text(parts.slice(1).join('{prob}'));
  return tspan;
}

function localizedDurationParts(hours) {
  if (hours < 0.016) {
    return { seconds: Math.round(hours * 3600) };
  }
  if (hours < 1) {
    return { minutes: Math.round(hours * 60) };
  }
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remainingHours = Math.round(hours % 24);
    return { days: remainingHours === 24 ? days + 1 : days, hours: remainingHours === 24 ? 0 : remainingHours };
  }

  let wholeHours = Math.floor(hours);
  let minutes = Math.round((hours - wholeHours) * 60);
  if (minutes === 60) {
    wholeHours += 1;
    minutes = 0;
  }
  if (wholeHours >= 24) {
    return { days: 1 };
  }
  return { hours: wholeHours, minutes };
}

// Screen size helpers - uses container width for responsive layout
function getScreenSize(containerWidth = null) {
  // Use container width if provided, otherwise fall back to viewport width
  const width = containerWidth || window.innerWidth;
  return {
    isNarrowMobile: width <= 430,
    isMobile: width < 576,
    isSmallMobile: width <= 500,
    // hasHover stays viewport-based since it's about device capability
    hasHover: window.matchMedia('(any-hover: hover)').matches
  };
}

const FRONTIER_COLOR = '#2e7d32';
const NON_FRONTIER_COLOR = '#9e9e9e';

// Overlap detection threshold (in pixels)
const OVERLAP_THRESHOLD = LABEL_RADIUS * 1.5;

// Global state variables to persist across resizes
let isLogScale = window.location.pathname !== '/';
let currentProbability = 'p50';

// Track active timeouts to cancel them if needed
let timeouts = {
  labelTransition: null,
  backgroundUpdate: null,
  taskDescription: null
};

// Auto-switch to linear scale on homepage
let autoSwitchTimeout = null;
let autoSwitchDone = false;

const TASK_DESCRIPTIONS = {
  logScale: {
    p50: [
      { hours: 12, text: 'Optimally reduce the size of a language model' },
      { hours: 4, text: 'Train adversarially robust image model' },
      { hours: 0.82, text: 'Train classifier' }, // 49 min
      { hours: 0.17, text: 'Find fact on web' }, // 10 min
      { hours: 0.03, text: 'Count words in passage' }, // 2 min
      { hours: 0.00417, text: 'Answer question' } // 15 sec
    ],
    p80: [
      { hours: 0.82, text: 'Train classifier' }, // 49 min
      { hours: 0.17, text: 'Find fact on web' }, // 10 min
      { hours: 0.03, text: 'Count words in passage' }, // 2 min
      { hours: 0.00417, text: 'Answer question' } // 15 sec
    ]
  },
  linearScale: {
    p50: [
      { hours: 14.62, text: 'Fix complex bug in ML research codebase' }, // 14 hr 37 min
      { hours: 8.07, text: 'Exploit a vulnerable Ethereum smart contract' }, // 8 hr 4 min
      { hours: 4, text: 'Train adversarially robust image model' },
      { hours: 2.3, text: 'Exploit a buffer overflow' },
      { hours: 1.2, text: 'Fix bugs in small Python libraries' },
    ],
    p80: [
      { hours: 2.3, text: 'Exploit a buffer overflow' },
      { hours: 1.387, text: 'Debug a small Python library' }, // 83 min
      { hours: 0.82, text: 'Train classifier' }, // 49 min
      { hours: 0.383, text: 'Implement a simple webserver' }, // 23 min
    ]
  }
};

function probabilityArticle(probability) {
  return probability === 'p50' ? 'a' : 'an';
}

function probabilityText(probability) {
  return probability === 'p50' ? '50%' : '80%';
}

function probabilityArticleText(probability) {
  if (CHART_LOCALE !== 'en') return probabilityText(probability);
  return `${probabilityArticle(probability)} ${probabilityText(probability)}`;
}

function configureYScale(data, isLogScale, height, showSaturation) {
  if (isLogScale) {
    const minValue = Math.min(0.01, d3.min(data, d => d.horizonLength) * 0.5);
    const dataMax = d3.max(data, d => d.horizonLength) * 1.5;
    const maxValue = showSaturation ? Math.max(64, dataMax) : dataMax;
    return d3.scaleLog()
      .domain([minValue, maxValue])
      .range([height, 0]);
  } else {
    const maxDataValue = d3.max(data, d => d.horizonLength);
    const floor = showSaturation ? 18 : 0;
    let yScaleMax = Math.max(floor, maxDataValue * 1.1);
    // If maxValue is close to an integer, round up to next integer for cleaner scale
    if (Math.ceil(yScaleMax) < yScaleMax + 0.25) {
      yScaleMax = Math.ceil(Math.max(floor, maxDataValue));
    }
    return d3.scaleLinear()
      .domain([0, yScaleMax])
      .range([height, 0]);
  }
}

function getTaskDescriptions(isLog, probability) {
  const scaleKey = isLog ? 'logScale' : 'linearScale';
  const localizedTasks = CHART_TEXT.tasks?.[scaleKey]?.[probability];
  if (localizedTasks) return localizedTasks;
  return TASK_DESCRIPTIONS[scaleKey][probability] || [];
}

function generateLogScaleTicks(data) {
  const candidates = [4/3600, 36/3600, 6/60, 1, 4, 16];
  const minValue = Math.min(0.01, d3.min(data, d => d.horizonLength) * 0.5);
  const maxValue = d3.max(data, d => d.horizonLength);
  return candidates.filter(v => v >= minValue && v <= maxValue * 2);
}

function generateLinearScaleTicks(data, currentProbability) {
  const maxValue = d3.max(data, d => d.horizonLength);
  const tickValues = [];
  tickValues.push(0);

  if (maxValue < 0.5) {
    // Very small values - use minute increments
    const steps = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45];
    steps.forEach(v => {
      if (v <= maxValue) tickValues.push(v);
    });
  } else if (maxValue < 1) {
    // Small values - use 15-30 minute increments
    tickValues.push(0.25, 0.5, 0.75);
    if (maxValue > 0.75) tickValues.push(1);
  } else {
    // Normal range — step the hour labels so they don't crowd the axis at large maxValue.
    tickValues.push(0.5);

    const step = maxValue <= 4 ? 1
               : maxValue <= 10 ? 2
               : maxValue <= 24 ? 4
               : Math.ceil(maxValue / 6);
    if (step > 1) tickValues.push(1); // keep 1h anchor when stepping
    const yScaleMax = maxValue * 1.1;
    for (let i = step; i <= Math.ceil(maxValue); i += step) {
      if (i <= yScaleMax && i !== 1) tickValues.push(i);
    }
  }

  return tickValues;
}

// Detect overlapping dots and group them together
// Returns array of groups, where each group is an array of data points that overlap
function detectOverlappingDots(data, xScale, yScale) {
  const groups = [];
  const assigned = new Set();

  // Sort by release date so earlier models come first in groups
  const sortedData = [...data].sort((a, b) => a.releaseDate - b.releaseDate);

  for (let i = 0; i < sortedData.length; i++) {
    if (assigned.has(sortedData[i].id)) continue;

    const group = [sortedData[i]];
    assigned.add(sortedData[i].id);

    const x1 = xScale(sortedData[i].releaseDate);
    const y1 = yScale(sortedData[i].horizonLength);

    // Find all points that overlap with this one
    for (let j = i + 1; j < sortedData.length; j++) {
      if (assigned.has(sortedData[j].id)) continue;

      const x2 = xScale(sortedData[j].releaseDate);
      const y2 = yScale(sortedData[j].horizonLength);

      const distance = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));

      if (distance < OVERLAP_THRESHOLD) {
        group.push(sortedData[j]);
        assigned.add(sortedData[j].id);
      }
    }

    groups.push(group);
  }

  return groups;
}

function formatTickLabel(d) {
  if (d === 0) return '0';
  if (d < 0.001) return '0';
  if (d < 0.016) {
    const seconds = Math.round(d * 3600);
    if (CHART_LOCALE === 'zh-Hans') return `${seconds} 秒`;
    if (CHART_LOCALE === 'es') return `${seconds} s`;
    return `${seconds} sec`;
  }
  if (d < 1) {
    const minutes = Math.round(d * 60);
    if (CHART_LOCALE === 'zh-Hans') return `${minutes} 分钟`;
    return minutes === 30 ? '30 min' : `${minutes} min`;
  }
  const hours = Math.floor(d);
  const fractionalHours = d - hours;
  if (Math.abs(fractionalHours - 0.5) < 0.001) {
    if (CHART_LOCALE === 'zh-Hans') return `${hours} 小时 30 分`;
    if (CHART_LOCALE === 'es') return `${hours} h 30 min`;
    return `${hours}h 30m`;
  }
  if (CHART_LOCALE === 'zh-Hans') return `${d} 小时`;
  if (CHART_LOCALE === 'es') return d === 1 ? '1 hora' : `${d} horas`;
  return d === 1 ? '1 hour' : `${d} hours`;
}

function generateGridTicks(isLogScale, yScale, tickValues, maxValue) {
  if (isLogScale) {
    return [4/3600, 36/3600, 6/60, 1, 4, 16].filter(v => v >= yScale.domain()[0] && v <= yScale.domain()[1]);
  } else {
    // For linear scale, ensure we have reasonable grid lines
    if (maxValue < 0.5) {
      // For small values, use every other tick value to avoid overcrowding
      let gridTickValues = tickValues.filter((v, i) => v > 0 && i % 2 === 1);
      // Ensure we have at least 2-3 grid lines
      if (gridTickValues.length < 2) {
        gridTickValues = tickValues.filter(v => v > 0).slice(0, 3);
      }
      return gridTickValues;
    } else {
      // For normal range, use standard grid lines that fit within the range
      let gridTickValues = [0.5, 1, 1.5].filter(v => v <= maxValue * 1.1);
      // Add more grid lines if needed
      if (maxValue > 1.5) {
        for (let i = 2; i <= Math.ceil(maxValue); i += 0.5) {
          gridTickValues.push(i);
        }
      }
      return gridTickValues;
    }
  }
}

function calculateTrendLine(frontierData, probability) {
  if (frontierData.length <= 2) {
    return null;
  }

  // Fit exponential curve: y = a * e^(b * x)
  // Transform to linear regression: ln(y) = ln(a) + b * x
  const regressionData = frontierData.map(d => ({
    x: (d.releaseDate.getTime() - new Date('2020-01-01').getTime()) / (365.25 * 24 * 60 * 60 * 1000), // years since 2020
    y: Math.log(Math.max(d.horizonLength, 1e-7)) // Clip to avoid log(0)
  }));

  // Calculate linear regression coefficients
  const n = regressionData.length;
  const sumX = regressionData.reduce((sum, d) => sum + d.x, 0);
  const sumY = regressionData.reduce((sum, d) => sum + d.y, 0);
  const sumXY = regressionData.reduce((sum, d) => sum + d.x * d.y, 0);
  const sumXX = regressionData.reduce((sum, d) => sum + d.x * d.x, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const doublingTimeDays = slope > 0 ? (Math.LN2 / slope) * 365.25 : Infinity;
  console.log(
    `[Trendline fit] probability=${probability || 'unknown'}` +
    ` | models=[${frontierData.map(d => d.name).join(', ')}]` +
    ` | doubling_time=${doublingTimeDays.toFixed(1)} days`
  );

  // Calculate residuals for standard error
  const ssResidual = regressionData.reduce((sum, d) => {
    const yPred = intercept + slope * d.x;
    return sum + Math.pow(d.y - yPred, 2);
  }, 0);

  // Calculate standard error for confidence intervals
  const xMean = sumX / n;
  const se = Math.sqrt(ssResidual / (n - 2));
  const sxx = sumXX - n * xMean * xMean;

  // Get the date range of the actual data
  const dataMinDate = d3.min(frontierData, d => d.releaseDate);
  const dataMaxDate = d3.max(frontierData, d => d.releaseDate);

  // Define the date range for the trend line
  const startDate = new Date('2019-01-01');
  const endDate = new Date(dataMaxDate);
  endDate.setMonth(endDate.getMonth() + 3);

  // Generate smooth curve points for the entire range
  const curvePoints = [];
  const numPoints = TREND_LINE_POINTS;
  const timeSpan = endDate.getTime() - startDate.getTime();
  const tValue = CONFIDENCE_INTERVAL_T_VALUE;

  for (let i = 0; i <= numPoints; i++) {
    const date = new Date(startDate.getTime() + (i / numPoints) * timeSpan);
    const x = (date.getTime() - new Date('2020-01-01').getTime()) / (365.25 * 24 * 60 * 60 * 1000);
    const logY = intercept + slope * x;
    const y = Math.exp(logY);

    // Calculate confidence interval in log space
    const seY = se * Math.sqrt(1/n + Math.pow(x - xMean, 2) / sxx);
    const logYLower = logY - tValue * seY;
    const logYUpper = logY + tValue * seY;
    const yLower = Math.exp(logYLower);
    const yUpper = Math.exp(logYUpper);

    // Only include points within reasonable bounds
    if (y < 1000 && y > 1e-7) {
      curvePoints.push({
        date: date,
        value: y,
        lower: yLower,
        upper: yUpper
      });
    }
  }

  // Split into segments based on data range
  const solidPoints = curvePoints.filter(p => p.date >= dataMinDate && p.date <= dataMaxDate);
  const dashedBeforePoints = curvePoints.filter(p => p.date < dataMinDate);
  const dashedAfterPoints = curvePoints.filter(p => p.date > dataMaxDate);

  return {
    curvePoints,
    solidPoints,
    dashedBeforePoints,
    dashedAfterPoints
  };
}

// Clip screen points so the trend line stops at the x-axis instead of extending below it.
// Interpolates boundary crossings for a clean intersection point.
function clipScreenPointsAtBottom(points, chartHeight) {
  if (points.length === 0) return points;
  const result = [];
  for (let i = 0; i < points.length; i++) {
    const inBounds = points[i].screenY <= chartHeight;
    if (i > 0) {
      const prevInBounds = points[i - 1].screenY <= chartHeight;
      if (inBounds && !prevInBounds) {
        // Entering chart from below: interpolate entry point
        const prev = points[i - 1], curr = points[i];
        const t = (chartHeight - prev.screenY) / (curr.screenY - prev.screenY);
        result.push({
          date: new Date(prev.date.getTime() + t * (curr.date.getTime() - prev.date.getTime())),
          screenY: chartHeight
        });
      }
      if (!inBounds && prevInBounds) {
        // Leaving chart through bottom: interpolate exit point
        const prev = points[i - 1], curr = points[i];
        const t = (chartHeight - prev.screenY) / (curr.screenY - prev.screenY);
        result.push({
          date: new Date(prev.date.getTime() + t * (curr.date.getTime() - prev.date.getTime())),
          screenY: chartHeight
        });
      }
    }
    if (inBounds) result.push(points[i]);
  }
  return result;
}

// Model display names mapping
const modelMetadata = {
  'gpt2': { name: 'GPT-2' },
  'davinci_002': { name: 'GPT-3' },
  'gpt_3_5_turbo_instruct': { name: 'GPT-3.5' },
  'gpt_4': { name: 'GPT-4' },
  'gpt_4_turbo': { name: 'GPT-4 Turbo' },
  'gpt_4_1106': { name: 'GPT-4 Nov \'23' },
  'gpt_4_0125': { name: 'GPT-4 Jan \'24' },
  'gpt_4o': { name: 'GPT-4o', link: '/evaluations/gpt-4o-report/' },
  'claude_3_opus': { name: 'Claude 3 Opus' },
  'qwen_2_72b': { name: 'Qwen2-72B' },
  'claude_3_5_sonnet': { name: 'Claude 3.5 Sonnet (Old)', link: '/evaluations/claude-3-5-sonnet-report/' },
  'claude_3_5_sonnet_20240620': { name: 'Claude 3.5 Sonnet (Old)', link: '/evaluations/claude-3-5-sonnet-report/' },
  'claude_3_5_sonnet_20241022': { name: 'Claude 3.5 Sonnet (New)' },
  'o1_preview': { name: 'o1-preview', link: '/evaluations/openai-o1-preview-report/' },
  'qwen_2_5_72b': { name: 'Qwen2.5-72B', link: '/evaluations/deepseek-qwen-report/' },
  'o1_elicited': { name: 'o1' },
  'deepseek_v3': { name: 'DeepSeek-V3', link: '/evaluations/deepseek-v3-report/' },
  'deepseek_r1': { name: 'DeepSeek-R1', link: '/evaluations/deepseek-r1-report/' },
  'claude_3_7_sonnet': { name: 'Claude 3.7 Sonnet', link: '/evaluations/claude-3-7-report/' },
  'deepseek_v3_0324': { name: 'DeepSeek-V3-0324', link: '/evaluations/deepseek-qwen-report/' },
  'o4-mini': { name: 'o4-mini', link: '/evaluations/openai-o3-report/' },
  'o3': { name: 'o3', link: '/evaluations/openai-o3-report/' },
  'claude_4_opus': { name: 'Claude Opus 4', link: 'https://x.com/METR_Evals/status/1940088546385436738' },
  'claude_4_sonnet': { name: 'Claude Sonnet 4', link: 'https://x.com/METR_Evals/status/1940088546385436738' },
  'deepseek_r1_0528': { name: 'DeepSeek-R1-0528', link: '/evaluations/deepseek-qwen-report/' },
  'gemini_2_5_pro_preview': { name: 'Gemini 2.5 Pro Preview' },
  'grok_4': { name: 'Grok 4', link: 'https://x.com/METR_Evals/status/1950740117020389870' },
  'gpt_5_2025_08_07': { name: 'GPT-5', link: '/evaluations/gpt-5-report/' },
  'gpt_5': { name: 'GPT-5', link: '/evaluations/gpt-5-report/' },
  'claude_4_1_opus': { name: 'Claude Opus 4.1', link: 'https://x.com/METR_Evals/status/1961527692072993272' },
  'claude_sonnet_4_5': { name: 'Claude Sonnet 4.5', link: 'https://x.com/METR_Evals/status/1976331315772580274' },
  'claude_opus_4_5': { name: 'Claude Opus 4.5', link: 'https://x.com/METR_Evals/status/2002203627377574113' },
  'claude_opus_4_6': { name: 'Claude Opus 4.6', link: 'https://x.com/METR_Evals/status/2024923422867030027' },
  'gpt-oss-120b': { name: 'gpt-oss-120b' },
  'gpt_5_1_codex_max': { name: 'GPT-5.1-Codex-Max', link: '/evaluations/gpt-5-1-codex-max-report/' },
  'gemini_3_pro': { name: 'Gemini 3 Pro', link: 'https://x.com/METR_Evals/status/2018752230376210586' },
  'kimi_k2_thinking': { name: 'Kimi K2 Thinking (inference via Novita AI)', link: 'https://x.com/METR_Evals/status/1991658241932292537' },
  'gpt_5_2': { name: 'GPT-5.2 (high)', link: 'https://x.com/METR_Evals/status/2019169900317798857' },
  'gpt_5_3_codex': { name: 'GPT-5.3-Codex (high)', link: 'https://x.com/METR_Evals/status/2025035574118416460' },
  'gpt_5_4': { name: 'GPT-5.4 (xhigh)', link: 'https://x.com/METR_Evals/status/2042640545126965441' },
  'gemini_3_1_pro': { name: 'Gemini 3.1 Pro', link: 'https://x.com/METR_Evals/status/2044463380057194868' },
  'claude_mythos_preview_early': { name: 'Claude Mythos Preview (early)' },
};

// Calculate frontier status for each probability level
function calculateFrontierStatus(processedData) {
  const sortedData = [...processedData].sort((a, b) => a.releaseDate - b.releaseDate);

  // Track the maximum horizonLength seen so far for each probability level
  let maxP50 = 0;
  let maxP80 = 0;

  sortedData.forEach(model => {
    // For p50: check if this model has the highest p50.horizonLength seen so far
    if (model.p50.horizonLength > maxP50) {
      model.frontier_p50 = true;
      maxP50 = model.p50.horizonLength;
    } else {
      model.frontier_p50 = false;
    }

    // For p80: check if this model has the highest p80.horizonLength seen so far
    if (model.p80.horizonLength > maxP80) {
      model.frontier_p80 = true;
      maxP80 = model.p80.horizonLength;
    } else {
      model.frontier_p80 = false;
    }
  });

  return sortedData;
}

// Convert benchmark data to chart format
function processData(benchmarkData) {
  const results = benchmarkData.results;
  const processedData = [];

  for (const [modelKey, modelData] of Object.entries(results)) {
    // Strip "_inspect" suffix when looking up metadata
    const metadataKey = modelKey.replace(/_inspect$/, '');
    const metadata = modelMetadata[metadataKey] || modelMetadata[modelKey] || {
      name: metadataKey
    };

    const agentData = modelData.metrics;

    if (agentData && agentData.p50_horizon_length) {
      processedData.push({
        id: modelKey,
        name: metadata.name,
        link: metadata.link || null,
        releaseDate: new Date(modelData.release_date),
        // Store both p50 and p80 data
        p50: {
          horizonLength: agentData.p50_horizon_length.estimate / 60, // Convert to hours
          ciLow: agentData.p50_horizon_length.ci_low / 60,
          ciHigh: agentData.p50_horizon_length.ci_high / 60
        },
        p80: {
          horizonLength: agentData.p80_horizon_length ? agentData.p80_horizon_length.estimate / 60 : 0,
          ciLow: agentData.p80_horizon_length ? agentData.p80_horizon_length.ci_low / 60 : 0,
          ciHigh: agentData.p80_horizon_length ? agentData.p80_horizon_length.ci_high / 60 : 0
        },
        // Default to p50
        horizonLength: agentData.p50_horizon_length.estimate / 60,
        ciLow: agentData.p50_horizon_length.ci_low / 60,
        ciHigh: agentData.p50_horizon_length.ci_high / 60,
        frontier: agentData.is_sota || false,
        averageScore: agentData.average_score.estimate,
        benchmarkName: modelData.benchmark_name || null
      });
    }
  }

  // Calculate frontier status for p50 and p80
  const dataWithFrontiers = calculateFrontierStatus(processedData);

  return dataWithFrontiers.sort((a, b) => a.releaseDate - b.releaseDate);
}

// Split a long rightmost label into two balanced lines at the space closest to the middle.
// Returns { line1, line2 } where line2 is null when the name has no splittable space.
function splitLabelName(name) {
  const words = name.split(' ');
  if (words.length < 2) return { line1: name, line2: null };

  let bestSplit = 1;
  let bestDiff = Math.abs(words[0].length - name.length / 2);
  for (let i = 1; i < words.length - 1; i++) {
    const firstPart = words.slice(0, i + 1).join(' ');
    const diff = Math.abs(firstPart.length - name.length / 2);
    if (diff < bestDiff) {
      bestDiff = diff;
      bestSplit = i + 1;
    }
  }
  return {
    line1: words.slice(0, bestSplit).join(' '),
    line2: words.slice(bestSplit).join(' ')
  };
}

// Measure the rendered width of one or more label lines using a throwaway SVG text node
// styled like .model-label. Returns the widest line's advance, or null if the Montserrat
// web font isn't loaded yet (so callers can fall back to a character-count estimate rather
// than measure against fallback-font metrics that would be wrong).
function measureLabelWidth(container, lines, fontSize) {
  if (typeof document !== 'undefined' && document.fonts
      && !document.fonts.check(`500 ${fontSize} Montserrat`)) {
    return null;
  }
  const probe = container.append('svg')
    .style('position', 'absolute')
    .style('visibility', 'hidden')
    .style('width', 0)
    .style('height', 0);
  let maxWidth = 0;
  lines.forEach(line => {
    const node = probe.append('text')
      .style('font-family', 'Montserrat, sans-serif')
      .style('font-size', fontSize)
      .style('font-weight', '500')
      .text(line)
      .node();
    maxWidth = Math.max(maxWidth, node.getComputedTextLength());
  });
  probe.remove();
  return maxWidth;
}

// Estimate how far (px) the rightmost model's label extends to the right of its dot, so the
// right margin can reserve room for it. The dot sits left of the plot's right edge (3-month
// domain pad), so reserving labelMargin + text width as right-gutter is safe/conservative.
//
// The label is drawn text-anchor:middle centered on the measured width of its wider line (see
// positionLabels/updateChart), so its right edge is labelX + measuredWidth. We measure the
// same way here. When the Montserrat web font isn't loaded yet, measureLabelWidth returns null
// and we fall back to the charWidth estimate (the +breathing room at the call site covers the
// small font-metrics mismatch until the next resize re-render).
function estimateRightmostLabelExtent(name, container, fontSize, charWidth, labelMargin) {
  // Labels longer than 35 chars are never drawn (see positionLabels), so don't reserve for them.
  if (name.length > 35) return labelMargin;

  const { line1, line2 } = name.length > 12 ? splitLabelName(name) : { line1: name, line2: null };
  const lines = line2 ? [line1, line2] : [line1];

  const measuredWidth = measureLabelWidth(container, lines, fontSize);
  const textWidth = measuredWidth != null
    ? measuredWidth
    : Math.max(...lines.map(l => l.length * charWidth));
  return labelMargin + textWidth;
}

// Calculate position for a single label (shared by initial render and scale-toggle update)
function calculateSingleLabelPosition(d, xScale, yScale, height, { screenSize, rightmostPoint, labelMargin, charWidth }) {
  const x = xScale(d.releaseDate);
  const y = yScale(d.horizonLength);
  const estimatedWidth = d.name.length * charWidth;
  const isRightmost = d.name === rightmostPoint.name;

  let labelX, anchor;

  if (screenSize.isNarrowMobile) {
    labelX = x - labelMargin;
    anchor = 'end';
  } else if (isRightmost) {
    labelX = x + labelMargin;
    anchor = 'start';
  } else {
    labelX = x - labelMargin;
    anchor = 'end';
    if (x - labelMargin - estimatedWidth < 20) {
      labelX = x + labelMargin;
      anchor = 'start';
    }
  }

  let labelY = y + 4;
  if (y > height - 20) {
    labelY = height - 5;
  }

  return { labelX, labelY, anchor, isRightmost };
}

// Detect which labels should be visible based on overlap
function detectVisibleLabels(data, xScale, yScale, height, options = {}) {
  const { maxLabels = Infinity, containerWidth = null } = options;
  const screenSize = getScreenSize(containerWidth);
  const visibleLabels = new Set();
  const labelPositions = {};
  const labelWidths = {};
  const labelMargin = screenSize.isNarrowMobile ? 6 : 8;
  const labelHeight = screenSize.isNarrowMobile ? 12 : 14;
  const dotRadius = screenSize.isNarrowMobile ? LABEL_RADIUS_NARROW : LABEL_RADIUS;
  // Use smaller character width estimate for narrow screens (smaller font)
  const charWidth = screenSize.isNarrowMobile ? 5.5 : 7;

  // Find the latest model(s)
  const latestDate = d3.max(data, d => d.releaseDate);
  const latestModels = data.filter(d => d.releaseDate.getTime() === latestDate.getTime());

  // If there are multiple models with the same latest date, choose the one with highest p50
  let latestModel;
  if (latestModels.length > 1) {
    latestModel = latestModels.reduce((a, b) => a.horizonLength > b.horizonLength ? a : b);
  } else {
    latestModel = latestModels[0];
  }

  const rightmostPoint = latestModel;

  // On narrow screens, pre-select which models we'll even consider showing
  // to drastically reduce label clutter
  let candidateModels = data;
  if (screenSize.isNarrowMobile) {
    // On very narrow screens, only consider: latest model + top frontier models
    const frontierModels = data.filter(d => d.frontier && d.name !== latestModel.name);
    // Sort frontier by horizonLength descending, pick top 3
    const topFrontier = frontierModels
      .sort((a, b) => b.horizonLength - a.horizonLength)
      .slice(0, 3);
    candidateModels = [latestModel, ...topFrontier];
  } else if (screenSize.isSmallMobile) {
    // On small (but not narrowest) screens, be slightly less aggressive
    const frontierModels = data.filter(d => d.frontier && d.name !== latestModel.name);
    const topFrontier = frontierModels
      .sort((a, b) => b.horizonLength - a.horizonLength)
      .slice(0, 5);
    candidateModels = [latestModel, ...topFrontier];
  }

  // Sort data by priority: latest model first, then frontier models, then by y position
  const sortedData = [...candidateModels].sort((a, b) => {
    // Latest model always comes first
    if (a.name === latestModel.name) return -1;
    if (b.name === latestModel.name) return 1;

    // Then frontier models
    if (a.frontier !== b.frontier) return b.frontier - a.frontier;

    // Then by y position
    return yScale(a.horizonLength) - yScale(b.horizonLength);
  });

  // Check overlaps
  sortedData.forEach((d, i) => {
    if (currentProbability === 'p50' && d.horizonLength > SATURATION_THRESHOLD
      && !(d.name === latestModel.name && !screenSize.isMobile)) return;

    // Enforce max labels limit
    if (visibleLabels.size >= maxLabels) return;

    // Estimate label width (rough approximation)
    labelWidths[d.name] = d.name.length * charWidth;

    const { labelX, labelY, anchor } = calculateSingleLabelPosition(d, xScale, yScale, height, {
      screenSize, rightmostPoint, labelMargin, charWidth
    });

    // On narrow screens, if too close to left edge, skip this label entirely
    if (screenSize.isNarrowMobile && xScale(d.releaseDate) - labelMargin - labelWidths[d.name] < 10) {
      labelPositions[d.name] = { x: labelX, y: 0, anchor: anchor, tooCloseToEdge: true };
      return; // Skip to next iteration
    }

    // Store position
    labelPositions[d.name] = {
      x: labelX,
      y: labelY,
      anchor: anchor
    };

    // Check for overlaps with already placed labels and data points
    let hasOverlap = false;

    // Check overlap with other labels
    for (let j = 0; j < i; j++) {
      const other = sortedData[j];
      if (!visibleLabels.has(other.name)) continue;

      const otherPos = labelPositions[other.name];
      if (!otherPos) continue;

      // Calculate actual label bounds based on anchor
      const thisLeft = anchor === 'end' ? labelX - labelWidths[d.name] : labelX;
      const thisRight = anchor === 'end' ? labelX : labelX + labelWidths[d.name];
      const otherLeft = otherPos.anchor === 'end' ? otherPos.x - labelWidths[other.name] : otherPos.x;
      const otherRight = otherPos.anchor === 'end' ? otherPos.x : otherPos.x + labelWidths[other.name];

      // Check overlap - use larger margin on narrow screens to give more breathing room
      const overlapMargin = screenSize.isNarrowMobile ? 8 : 5;
      const xOverlap = thisRight > otherLeft && thisLeft < otherRight;
      const yOverlap = Math.abs(labelY - otherPos.y) < labelHeight + overlapMargin;

      if (xOverlap && yOverlap) {
        hasOverlap = true;
        break;
      }
    }

    // Check overlap with ALL data points (not just previous ones)
    if (!hasOverlap) {
      for (const point of data) {
        // Skip checking overlap with the point's own dot
        if (point.name === d.name) continue;

        const pointX = xScale(point.releaseDate);
        const pointY = yScale(point.horizonLength);

        // Calculate label bounds
        const labelLeft = anchor === 'end' ? labelX - labelWidths[d.name] : labelX;
        const labelRight = anchor === 'end' ? labelX : labelX + labelWidths[d.name];
        const labelTop = labelY - labelHeight / 2;
        const labelBottom = labelY + labelHeight / 2;

        // Check if label overlaps with point (including some margin)
        const margin = 3;
        if (labelLeft < pointX + dotRadius + margin &&
            labelRight > pointX - dotRadius - margin &&
            labelTop < pointY + dotRadius + margin &&
            labelBottom > pointY - dotRadius - margin) {
          hasOverlap = true;
          break;
        }
      }
    }

    // Always show the latest model's label, otherwise only show if no overlap
    if (d.name === latestModel.name || !hasOverlap) {
      visibleLabels.add(d.name);
    }
  });

  return { visibleLabels, labelPositions, rightmostPoint };
}

// Position labels with overlap detection
function positionLabels(labels, backgrounds, data, xScale, yScale, height, containerWidth = null) {
  // Use the shared overlap detection logic
  const { visibleLabels, labelPositions, rightmostPoint } = detectVisibleLabels(data, xScale, yScale, height, { containerWidth });

  const labelMargin = 8;
  const labelHeight = 14;
  const labelWidths = {};

  // Pre-calculate label widths
  data.forEach(d => {
    labelWidths[d.name] = d.name.length * 7;
  });

  // Apply positions and visibility
  labels.each(function(d, i) {
    // Use stored positions if available, otherwise calculate default
    let labelX, labelY, anchor;

    if (labelPositions[d.name]) {
      labelX = labelPositions[d.name].x;
      labelY = labelPositions[d.name].y;
      anchor = labelPositions[d.name].anchor;
    } else {
      // Fallback to default positioning
      const x = xScale(d.releaseDate);
      const y = yScale(d.horizonLength);

      labelX = x - labelMargin;
      labelY = y - labelHeight + 9;
      anchor = 'end';

      if (labelX - labelWidths[d.name] / 2 < 20) {
        labelX = x + labelMargin;
        anchor = 'start';
      }
    }

    const isVisible = visibleLabels.has(d.name);
    const isRightmost = d.name === rightmostPoint.name;

    // if d.name is over 35 characters skip
    if (d.name.length > 35) {
      return;
    }

    // Clear any existing content
    d3.select(this).selectAll('*').remove();

    // Position text
    d3.select(this)
      .attr('x', labelX)
      .attr('y', labelY)
      .attr('text-anchor', anchor)
      .style('display', isVisible ? 'block' : 'none');

    // Check if we should split the label (rightmost and long)
    const shouldSplit = isRightmost && d.name.length > 12;

    if (shouldSplit) {
      // Split label at the space closest to the middle (see splitLabelName)
      const { line1, line2 } = splitLabelName(d.name);

      if (line2) {
        // Adjust y position to center the two-line text
        const adjustedY = labelY - 6; // Move up slightly to center both lines

        const sel = d3.select(this)
          .attr('y', adjustedY)
          .attr('text-anchor', 'middle'); // Override to center both lines

        // Add two tspan elements for line break (x set after measuring their real width)
        const tspan1 = sel.append('tspan').attr('dy', 0).text(line1);
        const tspan2 = sel.append('tspan').attr('dy', '1.2em').text(line2);

        // Center on the actual rendered width of the wider line, not a 7px/char estimate.
        const maxWidth = Math.max(
          tspan1.node().getComputedTextLength(),
          tspan2.node().getComputedTextLength()
        );
        const centerX = anchor === 'start' ? labelX + maxWidth / 2
                      : anchor === 'end'   ? labelX - maxWidth / 2
                      : labelX;
        tspan1.attr('x', centerX);
        tspan2.attr('x', centerX);
      } else {
        // Single line (no spaces to split)
        d3.select(this).text(d.name);
      }
    } else {
      // Regular single-line text
      d3.select(this).text(d.name);
    }

    // Position background rectangle
    if (isVisible) {
      const bbox = this.getBBox();
      const paddingX = 3;
      const paddingY = -0.75;

      d3.select(backgrounds.nodes()[i])
        .attr('x', bbox.x - paddingX)
        .attr('y', bbox.y - paddingY)
        .attr('width', bbox.width + 2 * paddingX)
        .attr('height', bbox.height + 2 * paddingY)
        .style('display', 'block');
    } else {
      d3.select(backgrounds.nodes()[i])
        .style('display', 'none');
    }
  });
}

function renderTaskDescriptions(g, taskDescriptions, yScale, height, options = {}) {
  const {
    animate = false,
    animationDuration = 0
  } = options;

  taskDescriptions.forEach(task => {
    if (yScale(task.hours) >= 0 && yScale(task.hours) <= height) {
      // Add connecting line
      const line = g.append('line')
        .attr('class', 'task-connector')
        .attr('x1', 0)
        .attr('x2', 8)
        .attr('y1', yScale(task.hours))
        .attr('y2', yScale(task.hours))
        .style('stroke', '#999')
        .style('stroke-width', 1);

      if (animate) {
        line.style('opacity', 0)
          .transition()
          .duration(animationDuration)
          .style('opacity', 1);
      }

      // Add text
      let y = yScale(task.hours);
      task.text.split('\n').forEach((line, index) => {
        let adjustedY = y;
        if (y > height - 20) {
          // prevent low tick labels colliding with the labels of the early models
          adjustedY = y - 8;
        }
        const text = g.append('text')
          .attr('class', 'task-description')
          .attr('x', 12)
          .attr('y', adjustedY)
          .attr('dy', '0.35em')
          .style('font-size', '13px')
          .style('fill', '#666')
          .style('text-anchor', 'start')
          .text(line);

        if (animate) {
          text.style('opacity', 0)
            .transition()
            .duration(animationDuration)
            .style('opacity', 1);
        }

        y += 16;
      });
    }
  });
}

function configureYAxis(yScale, data, isLogScale, currentProbability) {
  const tickValues = isLogScale
    ? generateLogScaleTicks(data)
    : generateLinearScaleTicks(data, currentProbability);

  return d3.axisLeft(yScale)
    .tickValues(tickValues)
    .tickFormat(formatTickLabel);
}

function initChart() {
  // Sync button active state with initial scale (handles ?scale=linear)
  d3.select('#linear-scale').classed('active', !isLogScale);
  d3.select('#log-scale').classed('active', isLogScale);

  const data = processData(benchmarkData);

  // Set frontier status based on current probability level
  // (processData sets d.frontier from is_sota which only reflects p50 frontier)
  data.forEach(d => {
    d.frontier = currentProbability === 'p80' ? d.frontier_p80 : d.frontier_p50;
  });

  if (currentProbability === 'p80') {
    data.forEach(d => {
      d.horizonLength = d.p80.horizonLength;
      d.ciLow = d.p80.ciLow;
      d.ciHigh = d.p80.ciHigh;
    });
  }

  if (currentProbability === 'p50') {
    data.forEach(d => {
      if (d.p50.horizonLength > SATURATION_THRESHOLD) d.frontier = false;
    });
  }

  const container = d3.select('#time-horizon-chart');
  const containerRect = container.node().getBoundingClientRect();

  // Cap container width to available viewport space (fixes Firefox Android overflow)
  const rightPadding = 10;
  const availableWidth = Math.min(containerRect.width, window.innerWidth - containerRect.left - rightPadding);

  // Use container width for responsive sizing (supports container queries)
  const screenSize = getScreenSize(containerRect.width);
  const { isMobile, isNarrowMobile, isSmallMobile, hasHover } = screenSize;
  const compactView = document.querySelector('.compact-view-marker');

  // Adjust margins based on container size
  // On narrow containers, reduce right margin since labels are all on the left
  const baseRightMargin = isMobile ? (isNarrowMobile ? 24 : 84) : 80;
  const margin = {
    top: isMobile ? (isNarrowMobile ? 45 : 80) : 60,
    right: baseRightMargin,
    bottom: isNarrowMobile ? 40 : 20,
    left: isMobile ? (isNarrowMobile ? 40 : 90) : 100,
  };

  // Grow the right margin to fit the rightmost (latest) model's label, which is drawn to
  // the right of its dot. Its width varies with the current frontier model's name, so a
  // fixed margin overflows for long names (e.g. "Claude Mythos Preview (early)"). On narrow
  // mobile every label is anchored on the left, so no extra right-gutter is needed there.
  if (!isNarrowMobile && data.length) {
    const rightmostName = data.reduce((a, b) => {
      if (a.releaseDate.getTime() > b.releaseDate.getTime()) return a;
      if (a.releaseDate.getTime() === b.releaseDate.getTime() && a.horizonLength > b.horizonLength) return a;
      return b;
    }).name;
    // '12px' is the non-narrow label font size (render path, line ~1582); labelMargin 8 matches
    // calculateSingleLabelPosition; charWidth 7 is only the fallback when the font isn't loaded.
    const extent = estimateRightmostLabelExtent(rightmostName, container, '12px', 7, 8);
    margin.right = Math.max(baseRightMargin, Math.ceil(extent) + 4); // +4 breathing room
  }

  if (compactView) margin.left = isMobile ? 50 : 70;
  const width = availableWidth - margin.left - margin.right;

  let baseHeight = 500;
  if (!window.isEmbedMode && isMobile) baseHeight = 400;

  const height = baseHeight - margin.top - margin.bottom;

  // Use smaller dot radius on narrow screens
  const dotRadius = isNarrowMobile ? LABEL_RADIUS_NARROW : LABEL_RADIUS;

  const svg = container.append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .style('font-family', 'Montserrat, sans-serif')
    .style('overflow', 'visible');

  // Diagonal hatch pattern to signal "uncertain / unreliable measurements" region.
  const hatchDefs = svg.append('defs');
  const hatch = hatchDefs.append('pattern')
    .attr('id', 'saturation-hatch')
    .attr('width', 7)
    .attr('height', 7)
    .attr('patternUnits', 'userSpaceOnUse')
    .attr('patternTransform', 'rotate(45)');
  hatch.append('rect')
    .attr('width', 7).attr('height', 7)
    .attr('fill', 'rgba(200, 200, 200, 0.18)');
  hatch.append('line')
    .attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', 7)
    .attr('stroke', 'rgba(120, 120, 120, 0.55)')
    .attr('stroke-width', 1.2);

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Create scales
  const latestDataDate = d3.max(data, d => d.releaseDate);
  const xDomainEnd = new Date(latestDataDate);
  xDomainEnd.setMonth(xDomainEnd.getMonth() + 3);
  const xScale = d3.scaleTime()
    .domain([new Date('2019-01-01'), xDomainEnd])
    .range([0, width]);

  let yScale = configureYScale(data, isLogScale, height, currentProbability === 'p50');

  // Create axes
  const currentYear = new Date().getFullYear();
  const allYearTicks = d3.range(2020, currentYear + 1).map(y => new Date(y, 0, 1));
  // On narrow screens, show only even years (plus current year if odd) to avoid crowding
  const xTickValues = isNarrowMobile
    ? allYearTicks.filter(d => d.getFullYear() % 2 === 0 || d.getFullYear() === currentYear)
    : allYearTicks;
  const xAxis = d3.axisBottom(xScale)
    .tickValues(xTickValues)
    .tickFormat(d => d3.timeFormat('%Y')(d));

  let yAxis = configureYAxis(yScale, data, isLogScale, currentProbability);

  // Add grid
  g.append('g')
    .attr('class', 'grid')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(xScale)
      .tickSize(-height)
      .tickFormat(''));

  // Custom horizontal grid lines
  if (isLogScale) {
    const logTicks = generateLogScaleTicks(data);
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickValues(logTicks)
        .tickSize(-width)
        .tickFormat(''));
  } else {
    // For linear scale, use custom tick values
    const maxValue = d3.max(data, d => d.horizonLength);
    const tickValues = generateLinearScaleTicks(data, currentProbability);
    const gridTickValues = generateGridTicks(false, yScale, tickValues, maxValue);
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickValues(gridTickValues)
        .tickSize(-width)
        .tickFormat(''));
  }

  // Add axes
  g.append('g')
    .attr('class', 'axis x-axis')
    .attr('transform', `translate(0,${height})`)
    .call(xAxis);

  g.select('.x-axis .domain').attr('d', `M0,0H${width}V0`);

  const yAxisGroup = g.append('g')
    .attr('class', 'axis y-axis')
    .call(yAxis);

  // Left-align the title on narrow viewports; center it on wide screens.
  const shouldLeftAlign = window.innerWidth <= 1250;
  const isMediumScreen = containerRect.width >= 576 && containerRect.width <= 1450;

  let yLabel;

  // Add white background rectangle for title
  const titleBgRect = svg.append('rect')
    .attr('class', 'title-background')
    .attr('x', 0)
    .attr('y', -5)
    .attr('fill', 'white')
    .attr('opacity', 1);

  // Add chart title - position higher on narrow mobile
  const titleY = isNarrowMobile ? 15 : (isMobile ? 25 : margin.top / 2 - 5);
  const chartTitle = svg.append('text')
    .attr('class', 'chart-title')
    .attr('x', shouldLeftAlign ? 0 : margin.left + width / 2)
    .attr('y', titleY)
    .style('text-anchor', shouldLeftAlign ? 'start' : 'middle');

  // Check screen width and adjust title accordingly
  if (!compactView) {
    if (isNarrowMobile) {
      // Narrow mobile: single line title, smaller font
      chartTitle.append('tspan')
        .style('font-size', '14px')
        .text(chartText('chart_title_narrow', 'Length of software tasks LLMs can complete'));
    } else if (!isMobile) {
      const titleLines = isMediumScreen ?
        chartText('chart_title_desktop_medium', [
          'Length of software tasks that',
          'different LLMs can complete {prob} of the time'
        ]) :
        chartText('chart_title_desktop_wide', [
          'Length of software tasks that different LLMs',
          'can complete {prob} of the time'
        ]);
      titleLines.forEach((line, index) => {
        appendLocalizedTspan(
          chartTitle,
          line,
          shouldLeftAlign ? 0 : margin.left + width / 2,
          index === 0 ? null : '1.2em'
        );
      });
    } else {
      // Regular mobile: 3 line title
      const titleLines = chartText('chart_title_mobile', [
        'Length of software tasks that',
        'different LLMs can complete',
        '{prob} of the time'
      ]);
      titleLines.forEach((line, index) => {
        appendLocalizedTspan(
          chartTitle,
          line,
          shouldLeftAlign ? 0 : margin.left + width / 2,
          index === 0 ? null : '1.2em'
        );
      });
    }

    // Update title background rectangle dimensions based on title size
    // Use requestAnimationFrame to ensure text is fully rendered before measuring
    requestAnimationFrame(() => {
      const titleBBox = chartTitle.node().getBBox();
      const titlePaddingX = 10;
      const titlePaddingY = 2;

      // Set dimensions to match title text with padding
      titleBgRect
        .attr('x', titleBBox.x - titlePaddingX)
        .attr('width', titleBBox.width + titlePaddingX * 2)
        .attr('height', titleBBox.y + titleBBox.height + titlePaddingY);

      updateYAxisDomainLine(false);
    });
  
    console.log('Adding y-axis label, isMobile:', isMobile, 'isNarrowMobile:', isNarrowMobile);

    if (isMobile) {
      // No y-axis label on mobile
      yLabel = null;
    } else {
      // Desktop: rotated label on the left
      yLabel = g.append('text')
        .attr('class', 'axis-label')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left - 20)
        .attr('x', 0 - (height / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle');

      // First line - bigger
      yLabel.append('tspan')
        .style('font-size', '16px')
        .style('font-weight', '500')
        .text(chartText('y_axis_title', 'Task duration (for humans)'));

      // Second line
      yLabel.append('tspan')
        .attr('x', 0 - (height / 2))
        .attr('dy', '1.2em')
        .style('font-size', '12px')
        .html(chartText('y_axis_line2', 'where logistic regression of our data'));

      // Third line
      yLabel.append('tspan')
        .attr('x', 0 - (height / 2))
        .attr('dy', '1.2em')
        .style('font-size', '12px')
        .html(interpolateText(
          chartText('y_axis_line3', 'predicts the AI has {prob} chance of succeeding'),
          { prob: `<tspan class="a-current-probability">${probabilityArticleText(currentProbability)}</tspan>` }
        ));
    }

    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom + 20})`)
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text(chartText('x_axis_label', 'LLM release date'));
  }
  // Add task duration descriptions to the right of the y-axis
  // Hide on narrow screens to reduce clutter
  if (!isNarrowMobile) {
    const taskDescriptions = getTaskDescriptions(isLogScale, currentProbability);
    renderTaskDescriptions(g, taskDescriptions, yScale, height);
  }

  // Create tooltip
  const tooltip = d3.select('body').append('div')
    .attr('class', 'tooltip');

  // For tooltips with links, use a delay so user can move mouse to click the link
  let hideTimeout = null;
  let isMouseOverTooltip = false;

  // Add hover handlers to tooltip element
  tooltip.on('mouseenter', function() {
    isMouseOverTooltip = true;
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }
  });

  tooltip.on('mouseleave', function() {
    isMouseOverTooltip = false;
    hideTooltip();
  });

  // On touch devices, dismiss tooltip when tapping elsewhere
  if (!hasHover) {
    if (chartClickHandler) {
      document.removeEventListener('click', chartClickHandler);
    }
    chartClickHandler = function(event) {
      // Don't hide if clicking on a dot, label, or the tooltip itself
      const isDataPoint = event.target.closest('.dot, .model-label, .tooltip');
      if (!isDataPoint) {
        hideTooltip();
      }
    };
    document.addEventListener('click', chartClickHandler);
  }

  // Prevent the homepage chart link wrapper from navigating on touch taps,
  // while still allowing mouse/trackpad clicks to navigate
  const chartLink = document.querySelector('a > #time-horizon-chart')?.closest('a');
  if (chartLink) {
    let lastPointerType = 'mouse';
    chartLink.addEventListener('pointerdown', function(event) {
      lastPointerType = event.pointerType;
    });
    chartLink.addEventListener('click', function(event) {
      if (lastPointerType === 'touch') {
        event.preventDefault();
      }
    });
  }

  function showTooltip(event, d) {
    // Cancel any pending hide
    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }

    const reportType = (d.link && (d.link.includes('twitter.com') || d.link.includes('x.com')))
      ? chartText('tooltip_x_thread', 'X thread')
      : chartText('tooltip_report', 'report');

    const reportLink = d.link
      ? `<p><a href="${d.link}" target="_blank" rel="noopener noreferrer">${interpolateText(chartText('tooltip_view_report', 'View our {type}'), { type: reportType })}</a></p>`
      : '';

    // Extract version from benchmark_name (e.g., "METR-Horizon-v1.1" -> "v1.1")
    const versionFromBenchmark = d.benchmarkName ? d.benchmarkName.split('-').pop() : null;
    const versionLabel = versionFromBenchmark ? `TH ${versionFromBenchmark.replace('v', '')}` : (currentDataVersion === 'TH 1.1' ? 'TH 1.1' : 'TH 1.0');

    const taskLengthText = (currentProbability === 'p50' && d.horizonLength > SATURATION_THRESHOLD)
      ? chartText('likely_at_least_16_hours', 'Likely at least 16 hrs')
      : formatDuration(d.horizonLength);

    tooltip.style('opacity', 1);
    tooltip.html(`
      <h4>${d.name}</h4>
      <p><strong>${chartText('tooltip_release', 'Release')}:</strong> ${formatReleaseDate(d.releaseDate)}</p>
      <p><strong>${chartText('tooltip_task_length', 'Task Length')}:</strong> ${taskLengthText}</p>
      <p><strong>${chartText('tooltip_ci', '95% CI')}:</strong> ${formatDuration(d.ciLow)} - ${formatDuration(d.ciHigh)}</p>
      <p><strong>${chartText('tooltip_average_score', 'Average Score')}:</strong> ${(d.averageScore * 100).toFixed(1)}%</p>
      <p><strong>${chartText('tooltip_version', 'Version')}:</strong> ${versionLabel}</p>
      ${reportLink}
    `);

    const tooltipNode = tooltip.node();
    const tooltipWidth = tooltipNode.offsetWidth;
    const windowWidth = window.innerWidth;
    const scrollX = window.scrollX;

    let left = event.pageX + 10;
    let top = event.pageY - 28;

    if (left + tooltipWidth > windowWidth + scrollX - 10) {
      left = event.pageX - tooltipWidth - 10;
    }

    if (left < scrollX + 10) {
      left = scrollX + 10;
    }

    tooltip
      .style('left', left + 'px')
      .style('top', top + 'px')
      .style('pointer-events', 'auto');
  }

  function hideTooltip() {
    tooltip.style('opacity', 0);
    tooltip.style('pointer-events', 'none');
  }

  function handleMouseOut(_, d) {
    // If tooltip has a link, delay hiding to give user time to move to tooltip
    if (d && d.link) {
      hideTimeout = setTimeout(function() {
        if (!isMouseOverTooltip) {
          hideTooltip();
        }
      }, 150);
    } else {
      hideTooltip();
    }
  }

  // Add error bars
  let errorBars = g.selectAll('.error-bar')
    .data(data)
    .enter().append('line')
    .attr('class', d => `error-bar ${d.frontier ? 'frontier' : 'non-frontier'}`)
    .attr('x1', d => xScale(d.releaseDate))
    .attr('x2', d => xScale(d.releaseDate))
    .attr('y1', d => Math.min(yScale(d.ciLow), height)) // Clip at x-axis
    .attr('y2', d => Math.max(yScale(d.ciHigh), 0)) // Clip at top of chart
    .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
    .attr('stroke-width', 1)
    .attr('opacity', 0.2)
    .attr('data-model-name', d => d.name);

  // Add error bar caps
  const capWidth = ERROR_BAR_CAP_WIDTH;
  let errorBarCapsTop = g.selectAll('.error-bar-cap-top')
    .data(data)
    .enter().append('line')
    .attr('class', 'error-bar-cap error-bar-cap-top')
    .attr('x1', d => xScale(d.releaseDate) - capWidth / 2)
    .attr('x2', d => xScale(d.releaseDate) + capWidth / 2)
    .attr('y1', d => yScale(d.ciHigh))
    .attr('y2', d => yScale(d.ciHigh))
    .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
    .attr('stroke-width', 1)
    .attr('opacity', 0.2)
    .style('display', d => yScale(d.ciHigh) <= 0 ? 'none' : 'block'); // Hide if above chart

  let errorBarCapsBottom = g.selectAll('.error-bar-cap-bottom')
    .data(data)
    .enter().append('line')
    .attr('class', 'error-bar-cap error-bar-cap-bottom')
    .attr('x1', d => xScale(d.releaseDate) - capWidth / 2)
    .attr('x2', d => xScale(d.releaseDate) + capWidth / 2)
    .attr('y1', d => yScale(d.ciLow))
    .attr('y2', d => yScale(d.ciLow))
    .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
    .attr('stroke-width', 1)
    .attr('opacity', 0.2)
    .style('display', d => yScale(d.ciLow) >= height ? 'none' : 'block'); // Hide if at or below x-axis

  // Create a group for trend lines (before dots and labels so they appear behind)
  const trendlineGroup = g.append('g')
    .attr('class', 'trendline-group');

  // Detect overlapping dots
  let overlappingGroups = detectOverlappingDots(data, xScale, yScale);

  // Create a map of data point id to its group info
  let overlapInfo = new Map();
  overlappingGroups.forEach(group => {
    if (group.length > 1) {
      group.forEach((d, idx) => {
        overlapInfo.set(d.id, { group, index: idx, total: group.length });
      });
    }
  });

  // Create dot groups container
  const dotGroups = g.append('g').attr('class', 'dots-container');

  // Render single dots (non-overlapping)
  const singleDots = data.filter(d => !overlapInfo.has(d.id));
  let dots = dotGroups.selectAll('.dot')
    .data(singleDots, d => d.id)
    .enter().append('circle')
    .attr('class', d => `dot ${dotStatusClass(d)}`)
    .attr('r', dotRadius)
    .attr('cx', d => xScale(d.releaseDate))
    .attr('cy', d => yScale(d.horizonLength))
    .attr('data-model-name', d => d.name);

  if (hasHover) {
    dots.on('mouseover', showTooltip)
      .on('mouseout', handleMouseOut);
  } else {
    dots.on('click', function(event, d) {
      event.preventDefault();
      event.stopPropagation();
      showTooltip(event, d);
    });
  }

  // Render split dots (overlapping pairs)
  const splitDotGroups = overlappingGroups.filter(group => group.length === 2);
  splitDotGroups.forEach(group => {
    // Sort by release date to ensure earlier model gets left side
    const sorted = [...group].sort((a, b) => a.releaseDate - b.releaseDate);
    const [leftModel, rightModel] = sorted;

    // Use the average position for the split dot
    const cx = (xScale(leftModel.releaseDate) + xScale(rightModel.releaseDate)) / 2;
    const cy = (yScale(leftModel.horizonLength) + yScale(rightModel.horizonLength)) / 2;
    const r = dotRadius;

    // Create a group for this split dot
    const splitGroup = dotGroups.append('g')
      .attr('class', 'split-dot-group')
      .attr('transform', `translate(${cx}, ${cy})`);

    // Left semicircle (earlier model)
    const leftHalf = splitGroup.append('path')
      .attr('class', `dot-half dot-half-left ${dotStatusClass(leftModel)}`)
      .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 0 0 ${r} L 0 0 Z`)
      .attr('data-model-name', leftModel.name)
      .datum(leftModel);

    // Right semicircle (later model)
    const rightHalf = splitGroup.append('path')
      .attr('class', `dot-half dot-half-right ${dotStatusClass(rightModel)}`)
      .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 1 0 ${r} L 0 0 Z`)
      .attr('data-model-name', rightModel.name)
      .datum(rightModel);

    // Divider line
    splitGroup.append('line')
      .attr('class', 'split-dot-divider')
      .attr('x1', 0)
      .attr('y1', -r)
      .attr('x2', 0)
      .attr('y2', r)
      .attr('stroke', 'white')
      .attr('stroke-width', 1.5);

    // Add event handlers
    if (hasHover) {
      leftHalf.on('mouseover', function(event) { showTooltip(event, leftModel); })
        .on('mouseout', function(event) { handleMouseOut(event, leftModel); });
      rightHalf.on('mouseover', function(event) { showTooltip(event, rightModel); })
        .on('mouseout', function(event) { handleMouseOut(event, rightModel); });
    } else {
      leftHalf.on('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        showTooltip(event, leftModel);
      });
      rightHalf.on('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        showTooltip(event, rightModel);
      });
    }
  });

  // Handle groups with more than 2 overlapping dots (rare case - just show all as split)
  const largeSplitGroups = overlappingGroups.filter(group => group.length > 2);
  largeSplitGroups.forEach(group => {
    // For now, just render them as regular overlapping dots
    // This is a rare edge case
    group.forEach(d => {
      const dot = dotGroups.append('circle')
        .attr('class', `dot ${dotStatusClass(d)}`)
        .attr('r', dotRadius)
        .attr('cx', xScale(d.releaseDate))
        .attr('cy', yScale(d.horizonLength))
        .attr('data-model-name', d.name)
        .datum(d);
      if (hasHover) {
        dot.on('mouseover', function(event) { showTooltip(event, d); })
          .on('mouseout', function(event) { handleMouseOut(event, d); });
      } else {
        dot.on('click', function(event) {
          event.preventDefault();
          event.stopPropagation();
          showTooltip(event, d);
        });
      }
    });
  });

  // Add model name labels with background (after dots and trend lines)
  const labelGroups = g.selectAll('.model-label-group')
    .data(data)
    .enter().append('g')
    .attr('class', 'model-label-group');

  // Add white background rectangles
  let labelBackgrounds = labelGroups.append('rect')
    .attr('class', 'model-label-bg');

  // Add text labels
  const labelFontSize = isNarrowMobile ? '10px' : '12px';
  let labels = labelGroups.append('text')
    .attr('class', 'model-label')
    .style('font-size', labelFontSize)
    .style('fill', 'var(--text-dark)')
    .style('font-weight', '500')

  if (hasHover) {
    labels.on('mouseover', showTooltip)
      .on('mouseout', handleMouseOut);
  } else {
    labels.on('click', function(event, d) {
      event.preventDefault();
      event.stopPropagation();
      showTooltip(event, d);
    });
  }

  // Position labels with overlap detection
  positionLabels(labels, labelBackgrounds, data, xScale, yScale, height, containerRect.width);

  // Saturation zone above the threshold — hatched fill signals an uncertain/unreliable region.
  const saturationZoneY = Math.max(0, yScale(SATURATION_THRESHOLD));
  const saturationZone = g.append('rect')
    .attr('class', 'saturation-zone')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', width)
    .attr('height', saturationZoneY)
    .attr('fill', 'url(#saturation-hatch)')
    .style('pointer-events', 'none')
    .style('opacity', currentProbability === 'p50' && saturationZoneY > 5 ? 1 : 0);
  saturationZone.lower(); // keep the hatch behind axes, gridlines, dots, etc.

  const saturationTextFontSize = isNarrowMobile ? '10px' : '13px';
  const saturationText = g.append('text')
    .attr('class', 'saturation-text')
    .attr('x', width / 2)
    .attr('y', saturationZoneY / 2)
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .style('font-size', saturationTextFontSize)
    .style('fill', 'rgba(0, 0, 0, 0.85)')
    .style('font-style', 'italic')
    .style('paint-order', 'stroke')
    .style('stroke', 'rgba(255, 255, 255, 0.9)')
    .style('stroke-width', '4px')
    .style('stroke-linejoin', 'round')
    .style('pointer-events', 'none')
    .style('opacity', currentProbability === 'p50' && saturationZoneY > 30 ? 1 : 0);
  saturationText.append('tspan').attr('x', width / 2).attr('dy', '-0.6em')
    .text(chartText('saturation_line1', 'Measurements above 16 hrs are unreliable'));
  saturationText.append('tspan').attr('x', width / 2).attr('dy', '1.2em')
    .text(chartText('saturation_line2', 'with our current task suite'));

  // Add exponential trend line for frontier models
  const frontierData = data.filter(d => d.frontier);
  let dashedPathBefore = null;
  let dashedPathAfter = null;

  const trendLineData = calculateTrendLine(frontierData, currentProbability);

  if (trendLineData) {
    const { curvePoints, solidPoints, dashedBeforePoints, dashedAfterPoints } = trendLineData;

    // Create line generator
    const line = d3.line()
      .x(d => xScale(d.date))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX);

    // Create area generator for confidence interval
    const area = d3.area()
      .x(d => xScale(d.date))
      .y0(d => yScale(Math.min(d.upper, 1000))) // Clip to chart bounds
      .y1(d => yScale(Math.max(d.lower, 0.0001)))
      .curve(d3.curveMonotoneX);

    // Draw confidence interval shaded area (for all points)
    if (SHOW_CONFIDENCE_AREA && curvePoints.length > 0) {
      trendlineGroup.append('path')
        .datum(curvePoints)
        .attr('class', 'confidence-area')
        .attr('fill', FRONTIER_COLOR)
        .attr('opacity', 0.1)
        .attr('d', area)
        .style('pointer-events', 'none');
    }

    if (SHOW_CONFIDENCE_AREA) {
      // Draw dashed line before data (with reduced opacity)
      if (dashedBeforePoints.length > 0) {
        dashedPathBefore = trendlineGroup.append('path')
          .datum(dashedBeforePoints)
          .attr('fill', 'none')
          .attr('stroke', FRONTIER_COLOR)
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('opacity', 0.4)
          .attr('d', line)
          .style('pointer-events', 'none');
      }

      // Draw solid line within data range
      if (solidPoints.length > 0) {
        trendPath = trendlineGroup.append('path')
          .datum(solidPoints)
          .attr('fill', 'none')
          .attr('stroke', FRONTIER_COLOR)
          .attr('stroke-width', 2)
          .attr('opacity', 0.8)
          .attr('d', line)
          .style('pointer-events', 'none');
      }

      // Draw dashed line after data (with reduced opacity)
      if (dashedAfterPoints.length > 0) {
        dashedPathAfter = trendlineGroup.append('path')
          .datum(dashedAfterPoints)
          .attr('fill', 'none')
          .attr('stroke', FRONTIER_COLOR)
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('opacity', 0.4)
          .attr('d', line)
          .style('pointer-events', 'none');
      }
    } else {
      // When confidence area is disabled, draw entire line as dashed
      if (curvePoints.length > 0) {
        // Store raw (unclipped) screen coordinates for smooth transitions;
        // clip only at render time so old/new date grids always match.
        const rawScreenPoints = curvePoints.map(p => ({
          ...p,
          screenY: yScale(p.value)
        }));
        const clippedScreenPoints = clipScreenPointsAtBottom(rawScreenPoints, height);
        const screenLine = d3.line()
          .x(d => xScale(d.date))
          .y(d => d.screenY)
          .curve(d3.curveMonotoneX);
        trendPath = trendlineGroup.append('path')
          .datum(rawScreenPoints)
          .attr('fill', 'none')
          .attr('stroke', FRONTIER_COLOR)
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('opacity', 0.6)
          .attr('d', screenLine(clippedScreenPoints))
          .style('pointer-events', 'none');
      }
    }
  }

  // Add logo for container widths 750px and above
  // Note: Logo is appended after all other elements so it appears on top
  let logoGroup;
  if (containerRect.width >= 750) {
    const logoHeight = 24;

    const estimatedLogoWidth = logoHeight * 4;
    const logoPadding = margin.right - 20; // Padding from right edge

    // Position it in the top right, right-aligned
    // Position from the right edge of the SVG: full SVG width minus logo width minus padding
    const logoMarginY = containerRect.width >= 1024 ? 32 : 16;
    const svgWidth = width + margin.left + margin.right;
    const logoLeft = svgWidth - estimatedLogoWidth - logoPadding;
    
    logoGroup = svg.append('g')
      .attr('class', 'chart-logo')
      .attr('transform', `translate(${logoLeft}, ${logoMarginY})`);

    // Create clickable area
    const logoLink = logoGroup.append('a')
      .attr('href', '/')
      .style('text-decoration', 'none');

    // Add logo image
    logoLink.append('image')
      .attr('href', '/assets/images/logo/logo.svg')
      .attr('height', logoHeight)
      .attr('preserveAspectRatio', 'xMidYMin meet')
      .attr('class', 'logo-image');
  }

  // Function to set frontier values based on probability level
  function isSaturated(d) {
    return currentProbability === 'p50' && d.p50.horizonLength > SATURATION_THRESHOLD;
  }

  function dotStatusClass(d) {
    return isSaturated(d) ? 'saturated' : (d.frontier ? 'frontier' : 'non-frontier');
  }

  function setFrontierValues(probability) {
    if (probability === 50) {
      data.forEach(d => {
        d.frontier = d.frontier_p50;
      });
    } else if (probability === 80) {
      data.forEach(d => {
        d.frontier = d.frontier_p80;
      });
    }
    data.forEach(d => {
      if (isSaturated(d)) d.frontier = false;
    });

    // Update visual elements based on new frontier status
    // Use classed() instead of attr('class') to preserve other classes like 'exiting'
    dots.classed('frontier', d => d.frontier)
      .classed('non-frontier', d => !d.frontier && !isSaturated(d))
      .classed('saturated', d => isSaturated(d));
    // Also update split dot halves
    g.selectAll('.dot-half')
      .classed('frontier', d => d.frontier)
      .classed('non-frontier', d => !d.frontier && !isSaturated(d))
      .classed('saturated', d => isSaturated(d));
    errorBars
      .classed('frontier', d => d.frontier)
      .classed('non-frontier', d => !d.frontier)
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR);
    errorBarCapsTop
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR);
    errorBarCapsBottom
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR);
  }

  // Probability toggle
  function setProbability(probability) {
    if (currentProbability === probability) return;

    currentProbability = probability;

    d3.select('#p50').classed('active', probability === 'p50');
    d3.select('#p80').classed('active', probability === 'p80');

    const probKey = probability;
    data.forEach(d => {
      d.horizonLength = d[probKey].horizonLength;
      d.ciLow = d[probKey].ciLow;
      d.ciHigh = d[probKey].ciHigh;
    });

    setFrontierValues(probability === 'p50' ? 50 : 80);

    if (!compactView && yLabel) {
      const tspans = yLabel.selectAll('tspan');
      const tspanCount = tspans.size();
      if (tspanCount === 3) {
        // Desktop or regular mobile with 3 tspans
        tspans.filter((_, i) => i === 0).text(chartText('y_axis_title', 'Task duration (for humans)'));
        tspans.filter((_, i) => i === 1).text(chartText('y_axis_line2', 'where logistic regression of our data'));
        tspans.filter((_, i) => i === 2).html(interpolateText(
          chartText('y_axis_line3', 'predicts the AI has {prob} chance of succeeding'),
          { prob: `<tspan class="a-current-probability">${probabilityArticleText(probability)}</tspan>` }
        ));
      }
    }

    yScale = configureYScale(data, isLogScale, height, currentProbability === 'p50');
    updateChart();
  }

  d3.select('#p50').on('click', () => setProbability('p50'));
  d3.select('#p80').on('click', () => setProbability('p80'));

  function setScale(useLogScale) {
    if (isLogScale === useLogScale) return;

    isLogScale = useLogScale;

    d3.select('#linear-scale').classed('active', !useLogScale);
    d3.select('#log-scale').classed('active', useLogScale);

    yScale = configureYScale(data, useLogScale, height, currentProbability === 'p50');
    updateChart();
  }

  d3.select('#linear-scale').on('click', () => setScale(false));
  d3.select('#log-scale').on('click', () => setScale(true));

  // Auto-switch to log scale on homepage after 2 seconds,
  // unless the user is hovering over the chart or controls.
  if (window.location.pathname === '/' && !autoSwitchDone) {
    if (autoSwitchTimeout) {
      clearTimeout(autoSwitchTimeout);
    }

    let isHoveringChart = false;
    const chartArea = document.querySelector('.time-horizon-chart-container');

    const onEnter = () => { isHoveringChart = true; };
    const onLeave = () => { isHoveringChart = false; };

    if (chartArea) {
      chartArea.addEventListener('mouseenter', onEnter);
      chartArea.addEventListener('mouseleave', onLeave);
    }

    const GLOW_FADE_IN = 500;
    const GLOW_HOLD_AT_PEAK = 250;
    const GLOW_HOLD_AFTER = 750;

    // Start glow 500ms before the 2s mark so it reaches peak 500ms before scale change
    setTimeout(() => {
      if (autoSwitchDone || isHoveringChart) return;
      const toggle = document.querySelector('.scale-toggle');
      // Phase 1: fade in glow
      if (toggle) toggle.classList.add('effect-glow');
    }, 2000 - GLOW_FADE_IN - GLOW_HOLD_AT_PEAK);

    autoSwitchTimeout = setTimeout(() => {
      autoSwitchDone = true;
      if (chartArea) {
        chartArea.removeEventListener('mouseenter', onEnter);
        chartArea.removeEventListener('mouseleave', onLeave);
      }
      if (!isHoveringChart) {
        const toggle = document.querySelector('.scale-toggle');
        // Phase 2: start scale change (glow already at peak)
        ANIMATION_DURATION = AUTO_SWITCH_ANIMATION_DURATION;
        setScale(true);
        ANIMATION_DURATION = 750;
        // Phase 3: hold glow during transition + 1000ms, then fade out
        setTimeout(() => {
          if (toggle) toggle.classList.remove('effect-glow');
        }, AUTO_SWITCH_ANIMATION_DURATION + GLOW_HOLD_AFTER);
      } else {
        // User is hovering, remove glow without scale change
        const toggle = document.querySelector('.scale-toggle');
        if (toggle) toggle.classList.remove('effect-glow');
      }
    }, 2000);
  }

  // Data source toggle - exposed globally for the dropdown to call
  function setDataSource() {
    // First, immediately remove any elements that are in exit transitions
    // This prevents issues when switching data sources before previous transitions complete
    g.selectAll('.dot.exiting').interrupt('exit').remove();
    g.selectAll('.error-bar.exiting').interrupt('exit').remove();
    g.selectAll('.error-bar-cap-top.exiting').interrupt('exit').remove();
    g.selectAll('.error-bar-cap-bottom.exiting').interrupt('exit').remove();
    g.selectAll('.model-label-group.exiting').interrupt('exit').remove();
    // Resolve any still-entering groups from a previous switch
    g.selectAll('.model-label-group.entering')
      .classed('entering', false)
      .interrupt('enter')
      .style('opacity', 1);

    // Remove split dot groups - they'll be rebuilt after data update
    g.selectAll('.split-dot-group').remove();

    // Reprocess data from the (updated) global benchmarkData
    const newProcessedData = processData(benchmarkData);
    const newDataMap = new Map(newProcessedData.map(d => [d.id, d]));
    const oldDataMap = new Map(data.map(d => [d.id, d]));

    // Find models to add, update, and remove
    const toAdd = newProcessedData.filter(d => !oldDataMap.has(d.id));
    const toRemove = data.filter(d => !newDataMap.has(d.id));
    const toUpdate = data.filter(d => newDataMap.has(d.id));

    // Remove old items from data array first (before any DOM operations)
    toRemove.forEach(d => {
      const idx = data.indexOf(d);
      if (idx > -1) data.splice(idx, 1);
    });

    // Update existing items in the data array
    toUpdate.forEach(d => {
      const newD = newDataMap.get(d.id);
      d.p50 = newD.p50;
      d.p80 = newD.p80;
      d.frontier = newD.frontier;
      d.frontier_p50 = newD.frontier_p50;
      d.frontier_p80 = newD.frontier_p80;
      d.averageScore = newD.averageScore;
      d.benchmarkName = newD.benchmarkName;

      const probKey = currentProbability;
      d.horizonLength = d[probKey].horizonLength;
      d.ciLow = d[probKey].ciLow;
      d.ciHigh = d[probKey].ciHigh;
    });

    // Prepare new items with current probability values
    toAdd.forEach(d => {
      const probKey = currentProbability;
      d.horizonLength = d[probKey].horizonLength;
      d.ciLow = d[probKey].ciLow;
      d.ciHigh = d[probKey].ciHigh;
    });

    // Add new items to data array
    toAdd.forEach(d => data.push(d));

    // Re-sort data by release date
    data.sort((a, b) => a.releaseDate - b.releaseDate);

    // Recalculate frontier status
    const sortedForFrontier = [...data].sort((a, b) => a.releaseDate - b.releaseDate);
    let maxP50 = 0, maxP80 = 0;
    sortedForFrontier.forEach(model => {
      model.frontier_p50 = model.p50.horizonLength > maxP50;
      if (model.frontier_p50) maxP50 = model.p50.horizonLength;
      model.frontier_p80 = model.p80.horizonLength > maxP80;
      if (model.frontier_p80) maxP80 = model.p80.horizonLength;
    });

    // Update frontier status based on current probability
    setFrontierValues(currentProbability === 'p50' ? 50 : 80);

    // Reconfigure scale
    yScale = configureYScale(data, isLogScale, height, currentProbability === 'p50');

    // Now update DOM elements with enter/update/exit pattern

    // Update error bars - use named transitions ('enter'/'exit') so they don't get
    // interrupted by updateChart's transitions
    const errorBarUpdate = g.selectAll('.error-bar').data(data, d => d.id);

    // Exit: mark as exiting, fade out and remove
    errorBarUpdate.exit()
      .classed('exiting', true)
      .transition('exit').duration(ANIMATION_DURATION)
      .style('opacity', 0)
      .remove();

    // Enter: create new error bars
    const errorBarEnter = errorBarUpdate.enter().append('line')
      .attr('class', d => `error-bar ${d.frontier ? 'frontier' : 'non-frontier'}`)
      .attr('x1', d => xScale(d.releaseDate))
      .attr('x2', d => xScale(d.releaseDate))
      .attr('y1', d => Math.min(yScale(d.ciLow), height))
      .attr('y2', d => Math.max(yScale(d.ciHigh), 0))
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
      .attr('stroke-width', 1)
      .attr('opacity', 0)
      .attr('data-model-name', d => d.name);

    errorBarEnter.transition('enter').duration(ANIMATION_DURATION)
      .attr('opacity', 0.2);

    // Update error bar caps (top)
    const capTopUpdate = g.selectAll('.error-bar-cap-top').data(data, d => d.id);
    capTopUpdate.exit().classed('exiting', true).transition('exit').duration(ANIMATION_DURATION).style('opacity', 0).remove();
    const capTopEnter = capTopUpdate.enter().append('line')
      .attr('class', 'error-bar-cap error-bar-cap-top')
      .attr('x1', d => xScale(d.releaseDate) - ERROR_BAR_CAP_WIDTH / 2)
      .attr('x2', d => xScale(d.releaseDate) + ERROR_BAR_CAP_WIDTH / 2)
      .attr('y1', d => yScale(d.ciHigh))
      .attr('y2', d => yScale(d.ciHigh))
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
      .attr('stroke-width', 1)
      .attr('opacity', 0)
      .style('display', d => yScale(d.ciHigh) <= 0 ? 'none' : 'block');
    capTopEnter.transition('enter').duration(ANIMATION_DURATION).attr('opacity', 0.2);

    // Update error bar caps (bottom)
    const capBottomUpdate = g.selectAll('.error-bar-cap-bottom').data(data, d => d.id);
    capBottomUpdate.exit().classed('exiting', true).transition('exit').duration(ANIMATION_DURATION).style('opacity', 0).remove();
    const capBottomEnter = capBottomUpdate.enter().append('line')
      .attr('class', 'error-bar-cap error-bar-cap-bottom')
      .attr('x1', d => xScale(d.releaseDate) - ERROR_BAR_CAP_WIDTH / 2)
      .attr('x2', d => xScale(d.releaseDate) + ERROR_BAR_CAP_WIDTH / 2)
      .attr('y1', d => yScale(d.ciLow))
      .attr('y2', d => yScale(d.ciLow))
      .attr('stroke', d => d.frontier ? FRONTIER_COLOR : NON_FRONTIER_COLOR)
      .attr('stroke-width', 1)
      .attr('opacity', 0)
      .style('display', d => yScale(d.ciLow) >= height ? 'none' : 'block');
    capBottomEnter.transition('enter').duration(ANIMATION_DURATION).attr('opacity', 0.2);

    // Recalculate overlapping dots
    overlappingGroups = detectOverlappingDots(data, xScale, yScale);
    overlapInfo = new Map();
    overlappingGroups.forEach(group => {
      if (group.length > 1) {
        group.forEach((d, idx) => {
          overlapInfo.set(d.id, { group, index: idx, total: group.length });
        });
      }
    });

    // Get container for dots
    let dotsContainer = g.select('.dots-container');
    if (dotsContainer.empty()) {
      dotsContainer = g.append('g').attr('class', 'dots-container');
    }

    // Filter data to only non-overlapping points for regular dots
    const singleDotData = data.filter(d => !overlapInfo.has(d.id));

    // Update dots (only non-overlapping ones)
    const dotUpdate = dotsContainer.selectAll('.dot').data(singleDotData, d => d.id);

    dotUpdate.exit()
      .classed('exiting', true)
      .transition('exit').duration(ANIMATION_DURATION)
      .style('opacity', 0)
      .remove();

    const dotEnter = dotUpdate.enter().append('circle')
      .attr('class', d => `dot ${dotStatusClass(d)}`)
      .attr('r', LABEL_RADIUS)
      .attr('cx', d => xScale(d.releaseDate))
      .attr('cy', d => yScale(d.horizonLength))
      .attr('data-model-name', d => d.name)
      .style('opacity', 0);

    if (hasHover) {
      dotEnter.on('mouseover', showTooltip).on('mouseout', handleMouseOut);
    } else {
      dotEnter.on('click', function(event, d) {
        event.preventDefault();
        event.stopPropagation();
        showTooltip(event, d);
      });
    }

    dotEnter.transition('enter').duration(ANIMATION_DURATION).style('opacity', 1);

    // Rebuild split dots for overlapping pairs
    const splitDotGroupsData = overlappingGroups.filter(group => group.length === 2);
    splitDotGroupsData.forEach(group => {
      const sorted = [...group].sort((a, b) => a.releaseDate - b.releaseDate);
      const [leftModel, rightModel] = sorted;

      const cx = (xScale(leftModel.releaseDate) + xScale(rightModel.releaseDate)) / 2;
      const cy = (yScale(leftModel.horizonLength) + yScale(rightModel.horizonLength)) / 2;
      const r = LABEL_RADIUS;

      const splitGroup = dotsContainer.append('g')
        .attr('class', 'split-dot-group')
        .attr('transform', `translate(${cx}, ${cy})`)
        .style('opacity', 0);

      const leftHalf = splitGroup.append('path')
        .attr('class', `dot-half dot-half-left ${dotStatusClass(leftModel)}`)
        .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 0 0 ${r} L 0 0 Z`)
        .attr('data-model-name', leftModel.name)
        .datum(leftModel);

      const rightHalf = splitGroup.append('path')
        .attr('class', `dot-half dot-half-right ${dotStatusClass(rightModel)}`)
        .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 1 0 ${r} L 0 0 Z`)
        .attr('data-model-name', rightModel.name)
        .datum(rightModel);

      splitGroup.append('line')
        .attr('class', 'split-dot-divider')
        .attr('x1', 0)
        .attr('y1', -r)
        .attr('x2', 0)
        .attr('y2', r)
        .attr('stroke', 'white')
        .attr('stroke-width', 1.5);

      if (hasHover) {
        leftHalf.on('mouseover', function(event) { showTooltip(event, leftModel); })
          .on('mouseout', function(event) { handleMouseOut(event, leftModel); });
        rightHalf.on('mouseover', function(event) { showTooltip(event, rightModel); })
          .on('mouseout', function(event) { handleMouseOut(event, rightModel); });
      } else {
        leftHalf.on('click', function(event) {
          event.preventDefault();
          event.stopPropagation();
          showTooltip(event, leftModel);
        });
        rightHalf.on('click', function(event) {
          event.preventDefault();
          event.stopPropagation();
          showTooltip(event, rightModel);
        });
      }

      splitGroup.transition('enter').duration(ANIMATION_DURATION).style('opacity', 1);
    });

    // Update label groups
    const labelGroupUpdate = g.selectAll('.model-label-group').data(data, d => d.id);

    // Exit: fade out old labels immediately as line starts moving
    labelGroupUpdate.exit()
      .classed('exiting', true)
      .transition('exit').duration(ANIMATION_DURATION / 2)
      .style('opacity', 0)
      .remove();

    // Enter: create new labels hidden via group opacity, overlap detection will
    // hide overlapping ones before the group is revealed
    const labelGroupEnter = labelGroupUpdate.enter().append('g')
      .attr('class', 'model-label-group entering')
      .style('opacity', 0); // Start hidden at group level

    labelGroupEnter.append('rect')
      .attr('class', 'model-label-bg');

    const newLabels = labelGroupEnter.append('text')
      .attr('class', 'model-label')
      .style('font-size', '12px')
      .style('font-weight', '500');

    if (hasHover) {
      newLabels.on('mouseover', showTooltip).on('mouseout', handleMouseOut);
    } else {
      newLabels.on('click', function(event, d) {
        event.preventDefault();
        event.stopPropagation();
        showTooltip(event, d);
      });
    }

    // Merge and update references for updateChart to use
    dots = dotsContainer.selectAll('.dot');
    errorBars = g.selectAll('.error-bar');
    errorBarCapsTop = g.selectAll('.error-bar-cap-top');
    errorBarCapsBottom = g.selectAll('.error-bar-cap-bottom');
    labels = g.selectAll('.model-label');
    labelBackgrounds = g.selectAll('.model-label-bg');

    // Now call updateChart to handle the transitions for existing elements
    updateChart();
  }

  // Expose setDataSource globally
  window.setDataSource = setDataSource;

  // Extends the y-axis line to reach the topmost tick, but not beyond the title middle
  function updateYAxisDomainLine(isTransition = false) {
    const tickValues = isLogScale ? generateLogScaleTicks(data) : generateLinearScaleTicks(data, currentProbability);
    const uncappedTopTickY = Math.min(0, ...tickValues.map(t => yScale(t)));

    // Calculate how far up (negative) the axis can go before hitting the title
    const titleBBox = chartTitle.node().getBBox();
    const chartTopInSvg = margin.top;
    const titleMiddleInSvg = titleBBox.y + titleBBox.height / 2;
    const minAllowedY = titleMiddleInSvg - chartTopInSvg;

    const topTickY = Math.max(minAllowedY, uncappedTopTickY);

    const domain = yAxisGroup.select('.domain');
    if (isTransition) {
      domain.transition().duration(ANIMATION_DURATION).attr('d', `M-6,${height}H0V${topTickY}`);
    } else {
      domain.attr('d', `M-6,${height}H0V${topTickY}`);
    }
  }

  function updateChart() {
    // Cancel any pending timeouts from previous transitions
    Object.keys(timeouts).forEach(key => {
      if (timeouts[key]) {
        clearTimeout(timeouts[key]);
      }
    });

    // Update y-axis with appropriate ticks for each scale
    const maxValue = d3.max(data, d => d.horizonLength);
    let tickValues = []; // Declare tickValues outside the if/else block

    let yAxis = configureYAxis(yScale, data, isLogScale, currentProbability);

    document.querySelectorAll('.current-probability').forEach(el => el.textContent = probabilityText(currentProbability));
    document.querySelectorAll('.a-current-probability').forEach(el => el.textContent = probabilityArticleText(currentProbability));

    yAxisGroup.transition().duration(ANIMATION_DURATION).call(yAxis);

    updateYAxisDomainLine(true);

    // Update grid with custom tick values
    const gridTickValues = generateGridTicks(isLogScale, yScale, tickValues, maxValue);

    g.select('.grid:nth-of-type(2)')
      .transition().duration(ANIMATION_DURATION)
      .call(d3.axisLeft(yScale)
        .tickValues(gridTickValues)
        .tickSize(-width)
        .tickFormat(''));

    // Update saturation zone position (only visible in p50 mode)
    const showSaturation = currentProbability === 'p50';
    const newSatZoneY = Math.max(0, yScale(SATURATION_THRESHOLD));
    g.select('.saturation-zone')
      .transition().duration(ANIMATION_DURATION)
      .attr('height', newSatZoneY)
      .style('opacity', showSaturation && newSatZoneY > 5 ? 1 : 0);
    g.select('.saturation-text')
      .transition().duration(ANIMATION_DURATION)
      .attr('y', newSatZoneY / 2)
      .style('opacity', showSaturation && newSatZoneY > 30 ? 1 : 0);

    // Recalculate overlapping groups with new scale
    const newOverlappingGroups = detectOverlappingDots(data, xScale, yScale);
    const newOverlapInfo = new Map();
    newOverlappingGroups.forEach(group => {
      if (group.length > 1) {
        group.forEach((d, idx) => {
          newOverlapInfo.set(d.id, { group, index: idx, total: group.length });
        });
      }
    });

    // Get dots container
    const dotsContainer = g.select('.dots-container');

    // Build new pair keys (sorted ID pairs) for size-2 overlap groups
    const newPairKeys = new Set();
    const newPairGroups = new Map(); // pairKey → group
    newOverlappingGroups.forEach(group => {
      if (group.length === 2) {
        const key = [group[0].id, group[1].id].sort().join('|');
        newPairKeys.add(key);
        newPairGroups.set(key, group);
      }
    });

    // Build old pair keys from existing split-dot-groups
    const oldPairKeys = new Map(); // pairKey → splitGroup DOM element
    g.selectAll('.split-dot-group').each(function() {
      const splitGroup = d3.select(this);
      const leftHalf = splitGroup.select('.dot-half-left');
      const rightHalf = splitGroup.select('.dot-half-right');
      if (leftHalf.empty() || rightHalf.empty()) return;
      const key = [leftHalf.datum().id, rightHalf.datum().id].sort().join('|');
      oldPairKeys.set(key, this);
    });

    // IDs in new size-2 pairs (for checking if an unsplit model should become a single dot)
    const newSplitIds = new Set();
    newPairGroups.forEach(group => group.forEach(d => newSplitIds.add(d.id)));

    // Split groups to remove: old pairs not in new pairs
    const pairsToRemove = new Set([...oldPairKeys.keys()].filter(k => !newPairKeys.has(k)));
    // Split groups to create: new pairs not in old pairs
    const pairsToCreate = new Set([...newPairKeys].filter(k => !oldPairKeys.has(k)));

    // Handle removed/changed split groups
    g.selectAll('.split-dot-group').each(function() {
      const splitGroup = d3.select(this);
      const leftHalf = splitGroup.select('.dot-half-left');
      const rightHalf = splitGroup.select('.dot-half-right');
      if (leftHalf.empty() || rightHalf.empty()) return;

      const key = [leftHalf.datum().id, rightHalf.datum().id].sort().join('|');

      if (pairsToRemove.has(key)) {
        // This pair no longer exists — remove and create individual dots where needed
        splitGroup.transition('split-exit').duration(ANIMATION_DURATION / 2)
          .style('opacity', 0)
          .remove();

        [leftHalf.datum(), rightHalf.datum()].forEach(d => {
          if (!newSplitIds.has(d.id)) {
            const dot = dotsContainer.append('circle')
              .attr('class', `dot ${dotStatusClass(d)}`)
              .attr('r', dotRadius)
              .attr('cx', xScale(d.releaseDate))
              .attr('cy', yScale(d.horizonLength))
              .attr('data-model-name', d.name)
              .datum(d)
              .style('opacity', 0);
            if (hasHover) {
              dot.on('mouseover', showTooltip).on('mouseout', handleMouseOut);
            } else {
              dot.on('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                showTooltip(event, d);
              });
            }
            dot.transition('split-enter').delay(ANIMATION_DURATION / 2).duration(ANIMATION_DURATION / 2)
              .style('opacity', 1);
          }
        });
      } else {
        // Pair unchanged — animate to new position
        const leftModel = leftHalf.datum();
        const rightModel = rightHalf.datum();
        const cx = (xScale(leftModel.releaseDate) + xScale(rightModel.releaseDate)) / 2;
        const cy = (yScale(leftModel.horizonLength) + yScale(rightModel.horizonLength)) / 2;
        splitGroup.interrupt();
        splitGroup.transition().duration(ANIMATION_DURATION)
          .attr('transform', `translate(${cx}, ${cy})`)
          .style('opacity', 1);
      }
    });

    // Handle new split groups (new pairs that didn't exist before)
    const newSplitGroups = [...pairsToCreate].map(k => newPairGroups.get(k));
    newSplitGroups.forEach(group => {
      const sorted = [...group].sort((a, b) => a.releaseDate - b.releaseDate);
      const [leftModel, rightModel] = sorted;

      // Remove existing individual dots for these models
      dotsContainer.selectAll('.dot').filter(d => d.id === leftModel.id || d.id === rightModel.id)
        .transition('split-exit').duration(ANIMATION_DURATION / 2)
        .style('opacity', 0)
        .remove();

      const cx = (xScale(leftModel.releaseDate) + xScale(rightModel.releaseDate)) / 2;
      const cy = (yScale(leftModel.horizonLength) + yScale(rightModel.horizonLength)) / 2;
      const r = dotRadius;

      const splitGroup = dotsContainer.append('g')
        .attr('class', 'split-dot-group')
        .attr('transform', `translate(${cx}, ${cy})`)
        .style('opacity', 0);

      const leftHalf = splitGroup.append('path')
        .attr('class', `dot-half dot-half-left ${dotStatusClass(leftModel)}`)
        .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 0 0 ${r} L 0 0 Z`)
        .attr('data-model-name', leftModel.name)
        .datum(leftModel);

      const rightHalf = splitGroup.append('path')
        .attr('class', `dot-half dot-half-right ${dotStatusClass(rightModel)}`)
        .attr('d', `M 0 ${-r} A ${r} ${r} 0 0 1 0 ${r} L 0 0 Z`)
        .attr('data-model-name', rightModel.name)
        .datum(rightModel);

      splitGroup.append('line')
        .attr('class', 'split-dot-divider')
        .attr('x1', 0).attr('y1', -r)
        .attr('x2', 0).attr('y2', r)
        .attr('stroke', 'white')
        .attr('stroke-width', 1.5);

      if (hasHover) {
        leftHalf.on('mouseover', function(event) { showTooltip(event, leftModel); })
          .on('mouseout', function(event) { handleMouseOut(event, leftModel); });
        rightHalf.on('mouseover', function(event) { showTooltip(event, rightModel); })
          .on('mouseout', function(event) { handleMouseOut(event, rightModel); });
      } else {
        leftHalf.on('click', function(event) {
          event.preventDefault(); event.stopPropagation();
          showTooltip(event, leftModel);
        });
        rightHalf.on('click', function(event) {
          event.preventDefault(); event.stopPropagation();
          showTooltip(event, rightModel);
        });
      }

      splitGroup.transition('split-enter').delay(ANIMATION_DURATION / 2).duration(ANIMATION_DURATION / 2)
        .style('opacity', 1);
    });

    // Update single dots that stay single (use named transition to avoid
    // clobbering the 'split-enter' opacity transition on newly created dots)
    dotsContainer.selectAll('.dot:not(.exiting)').transition('position').duration(ANIMATION_DURATION)
      .attr('cy', d => yScale(d.horizonLength));

    // Update overlap tracking
    overlappingGroups = newOverlappingGroups;
    overlapInfo = newOverlapInfo;

    // Update dots reference
    dots = dotsContainer.selectAll('.dot');

    // Update error bars (exclude exiting elements to not block D3's .remove())
    errorBars.filter(':not(.exiting)').transition().duration(ANIMATION_DURATION)
      .attr('y1', d => Math.min(yScale(d.ciLow), height)) // Clip at x-axis
      .attr('y2', d => Math.max(yScale(d.ciHigh), 0)); // Clip at top of chart

    errorBarCapsTop.filter(':not(.exiting)').transition().duration(ANIMATION_DURATION)
      .attr('y1', d => yScale(d.ciHigh))
      .attr('y2', d => yScale(d.ciHigh))
      .style('display', d => yScale(d.ciHigh) <= 0 ? 'none' : 'block'); // Hide if above chart

    errorBarCapsBottom.filter(':not(.exiting)').transition().duration(ANIMATION_DURATION)
      .attr('y1', d => yScale(d.ciLow))
      .attr('y2', d => yScale(d.ciLow))
      .style('display', d => yScale(d.ciLow) >= height ? 'none' : 'block'); // Hide if at or below x-axis

    // Update labels with smooth transition
    // First interrupt any existing transitions on labels and backgrounds
    labels.interrupt();
    labelBackgrounds.interrupt();

    const updateScreenSize = getScreenSize(containerRect.width);
    const updateLabelMargin = updateScreenSize.isNarrowMobile ? 6 : 8;
    const updateCharWidth = updateScreenSize.isNarrowMobile ? 5.5 : 7;
    const updateRightmostPoint = data.reduce((a, b) => {
      if (a.releaseDate.getTime() > b.releaseDate.getTime()) return a;
      if (a.releaseDate.getTime() === b.releaseDate.getTime() && a.horizonLength > b.horizonLength) return a;
      return b;
    });

    labels.each(function(d) {
      const { labelX, labelY: baseLabelY, anchor, isRightmost } = calculateSingleLabelPosition(d, xScale, yScale, height, {
        screenSize: updateScreenSize,
        rightmostPoint: updateRightmostPoint,
        labelMargin: updateLabelMargin,
        charWidth: updateCharWidth
      });
      let labelY = baseLabelY;

      // Handle multi-line labels
      const shouldSplit = isRightmost && d.name.length > 12;
      const label = d3.select(this);

      // Check if this is a new label that needs text content set
      const hasContent = label.text() || label.selectAll('tspan').size() > 0;

      if (shouldSplit) {
        const { line1, line2 } = splitLabelName(d.name);
        if (line2) {
          labelY = labelY - 6; // Adjust for two-line text

          // centerColumn(): center on the actual rendered width of the wider line (measured
          // from the live tspans), not a 7px/char estimate, so it matches the reserved margin.
          const centerColumn = (tspanSelection) => {
            let maxWidth = 0;
            tspanSelection.each(function() {
              maxWidth = Math.max(maxWidth, this.getComputedTextLength());
            });
            return anchor === 'start' ? labelX + maxWidth / 2
                 : anchor === 'end'   ? labelX - maxWidth / 2
                 : labelX;
          };

          // Build the tspan structure when it isn't already present. This covers entering
          // labels AND a label that was previously a single line and only now became the
          // rightmost/split label (e.g. a p50<->p80 tie-break changed which model is latest);
          // without this it would keep its plain text but get text-anchor:middle and no
          // centering, mis-positioning it. Otherwise transition the existing tspans.
          if (label.selectAll('tspan').empty()) {
            label.text(null); // drop any stale single-line text before adding tspans
            label
              .attr('x', labelX)
              .attr('y', labelY)
              .attr('text-anchor', 'middle');
            label.append('tspan').attr('dy', 0).text(line1);
            label.append('tspan').attr('dy', '1.2em').text(line2);
            const tspans = label.selectAll('tspan');
            tspans.attr('x', centerColumn(tspans));
          } else {
            // Existing label - transition to new position
            label.transition().duration(ANIMATION_DURATION)
              .attr('x', labelX)
              .attr('y', labelY)
              .attr('text-anchor', 'middle');

            // Update tspan positions (measure existing tspans for the center column)
            const tspans = label.selectAll('tspan');
            tspans.transition().duration(ANIMATION_DURATION)
              .attr('x', centerColumn(tspans));
          }
        } else {
          // Single word, no split - set text and position
          if (!hasContent) {
            label.text(d.name)
              .attr('x', labelX)
              .attr('y', labelY)
              .attr('text-anchor', anchor);
          } else {
            label.transition().duration(ANIMATION_DURATION)
              .attr('x', labelX)
              .attr('y', labelY)
              .attr('text-anchor', anchor);
          }
        }
      } else {
        // Regular single-line labels - set text and position. Reset the text when the label
        // is new OR is leaving the split state with stale tspans (the mirror of the rebuild
        // above: a previously-rightmost split label that is no longer rightmost); a plain
        // transition would leave its two tspans positioned as a single line.
        if (!hasContent || !label.selectAll('tspan').empty()) {
          label.text(d.name)
            .attr('x', labelX)
            .attr('y', labelY)
            .attr('text-anchor', anchor);
        } else {
          label.transition().duration(ANIMATION_DURATION)
            .attr('x', labelX)
            .attr('y', labelY)
            .attr('text-anchor', anchor);
        }
      }
    });

    // Hide label backgrounds during transition to avoid visual glitches
    labelBackgrounds.style('opacity', 0);

    // Update label backgrounds during transition
    labelBackgrounds.each(function(_, i) {
      const labelElement = labels.nodes()[i];
      if (labelElement && d3.select(labelElement).style('display') !== 'none') {
        // Get current position for smooth transition
        const label = d3.select(labelElement);
        const x = parseFloat(label.attr('x'));
        const y = parseFloat(label.attr('y'));
        const anchor = label.attr('text-anchor');

        // Skip if label position isn't set yet (new labels being created)
        if (isNaN(x) || isNaN(y)) return;

        const text = label.text() || label.selectAll('tspan').nodes().map(n => d3.select(n).text()).join(' ');
        const estimatedWidth = text.length * 7;

        let bgX, bgWidth;
        if (anchor === 'middle') {
          bgX = x - estimatedWidth / 2 - 3;
          bgWidth = estimatedWidth + 6;
        } else if (anchor === 'end') {
          bgX = x - estimatedWidth - 3;
          bgWidth = estimatedWidth + 6;
        } else {
          bgX = x - 3;
          bgWidth = estimatedWidth + 6;
        }

        d3.select(this).transition().duration(ANIMATION_DURATION)
          .attr('x', bgX)
          .attr('y', y - 10)
          .attr('width', bgWidth)
          .attr('height', 20);
      }
    });

    // After transition completes, run overlap detection and fade in/out labels
    timeouts['labelTransition'] = setTimeout(() => {
      // Store current visibility state
      const currentlyVisible = new Set();
      labels.each(function(d) {
        if (d3.select(this).style('display') !== 'none') {
          currentlyVisible.add(d.name);
        }
      });

      // Use the shared overlap detection logic
      const { visibleLabels } = detectVisibleLabels(data, xScale, yScale, height, { containerWidth: containerRect.width });

      // Fade in/out labels based on overlap detection
      labels.each(function(d, i) {
        const shouldBeVisible = visibleLabels.has(d.name);
        const wasVisible = currentlyVisible.has(d.name);

        if (shouldBeVisible && !wasVisible) {
          // Fade in
          d3.select(this)
            .style('display', 'block')
            .style('opacity', 0)
            .transition().duration(300)
            .style('opacity', 1);

          d3.select(labelBackgrounds.nodes()[i])
            .style('display', 'block')
            .style('opacity', 0)
            .transition().duration(300)
            .style('opacity', 0.75);
        } else if (!shouldBeVisible && wasVisible) {
          // Fade out
          d3.select(this)
            .transition().duration(300)
            .style('opacity', 0)
            .on('end', function() {
              d3.select(this).style('display', 'none');
            });

          d3.select(labelBackgrounds.nodes()[i])
            .transition().duration(300)
            .style('opacity', 0)
            .on('end', function() {
              d3.select(this).style('display', 'none');
            });
        }
        // Labels that remain visible don't need any change
      });

      // For entering label groups: hide overlapping labels immediately, then
      // reveal the group. This prevents the flicker where all labels briefly
      // appear before overlap detection hides them.
      const enteringGroups = g.selectAll('.model-label-group.entering');
      if (!enteringGroups.empty()) {
        enteringGroups.each(function() {
          const group = d3.select(this);
          // Immediately hide labels that should not be visible
          group.selectAll('.model-label').each(function(d) {
            if (!visibleLabels.has(d.name)) {
              d3.select(this).style('display', 'none').interrupt();
            }
          });
          group.selectAll('.model-label-bg').each(function(d) {
            if (!visibleLabels.has(d.name)) {
              d3.select(this).style('display', 'none').interrupt();
            }
          });
        });
        // Now reveal entering groups (overlapping labels already hidden)
        enteringGroups
          .classed('entering', false)
          .transition('enter')
          .duration(ANIMATION_DURATION / 2)
          .style('opacity', 1);
      }

      // Update background positions for visible labels
      timeouts['backgroundUpdate'] = setTimeout(() => {
        labelBackgrounds.each(function(_, i) {
          const labelElement = labels.nodes()[i];
          if (labelElement && d3.select(labelElement).style('display') !== 'none') {
            const bbox = labelElement.getBBox();
            d3.select(this)
              .attr('x', bbox.x - 3)
              .attr('y', bbox.y + 0.75)
              .attr('width', bbox.width + 6)
              .attr('height', bbox.height + 1.5)
              .style('opacity', 0.75);
          }
        });
      }, 350);
    }, ANIMATION_DURATION);

    // Update task descriptions (skip on narrow containers)
    const currentScreenSize = getScreenSize(containerRect.width);
    if (!currentScreenSize.isNarrowMobile) {
      // Fade out existing descriptions and connectors
      g.selectAll('.task-description, .task-connector')
        .transition()
        .duration(300)
        .style('opacity', 0)
        .remove();

      // After delay, add new descriptions based on scale
      timeouts['taskDescription'] = setTimeout(() => {
        const taskDescriptions = getTaskDescriptions(isLogScale, currentProbability);

        renderTaskDescriptions(g, taskDescriptions, yScale, height, {
          animate: true,
          animationDuration: ANIMATION_DURATION,
        });
      }, 500);
    }

    // Update trend line and confidence area
    // Recalculate frontier data based on current values
    const frontierData = data.filter(d => d.frontier);

    // Select the trend line group and path from the DOM
    const trendlineGroup = g.select('.trendline-group');
    const trendPath = trendlineGroup.select('path:not(.confidence-area)');

    const trendLineData = calculateTrendLine(frontierData, currentProbability);

    if (!trendPath.empty() && trendLineData) {
      const { curvePoints, solidPoints, dashedBeforePoints, dashedAfterPoints } = trendLineData;

      const line = d3.line()
        .x(d => xScale(d.date))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

      // Create area generator for confidence interval
      const area = d3.area()
        .x(d => xScale(d.date))
        .y0(d => yScale(Math.min(d.upper, 1000)))
        .y1(d => yScale(Math.max(d.lower, 0.0001)))
        .curve(d3.curveMonotoneX);

      // Update shaded area
      if (SHOW_CONFIDENCE_AREA) {
        let shadedArea = g.select('.confidence-area');
        if (shadedArea.empty() && curvePoints.length > 0) {
          // Create if doesn't exist
          shadedArea = g.append('path')
            .attr('class', 'confidence-area')
            .attr('fill', '#2e7d32')
            .attr('opacity', 0.1)
            .style('pointer-events', 'none');
        }
        if (!shadedArea.empty()) {
          shadedArea.transition().duration(ANIMATION_DURATION).attr('d', area(curvePoints));
        }
      }

      // Update paths
      if (SHOW_CONFIDENCE_AREA) {
        if (dashedPathBefore) {
          dashedPathBefore.transition().duration(ANIMATION_DURATION).attr('d', line(dashedBeforePoints));
        }
        if (trendPath) {
          trendPath.transition().duration(ANIMATION_DURATION).attr('d', line(solidPoints));
        }
        if (dashedPathAfter) {
          dashedPathAfter.transition().duration(ANIMATION_DURATION).attr('d', line(dashedAfterPoints));
        }
      } else {
        // When confidence area is disabled, animate by interpolating screen coordinates
        // This avoids issues with simultaneous y-scale and data changes.
        // We store raw (unclipped) screen points as the datum so old/new always share
        // the same date grid; clipping is applied per-frame during animation.
        if (!trendPath.empty()) {
          trendPath.interrupt(); // Cancel any in-progress transition

          // Get the old raw screen coordinates from stored data
          const oldRawScreenPoints = trendPath.datum();

          // Calculate new raw screen coordinates with the NEW yScale (unclipped)
          const newRawScreenPoints = curvePoints.map(p => ({
            ...p,
            screenY: yScale(p.value)
          }));

          // Check if old data has valid screenY values
          const hasValidOldScreenY = oldRawScreenPoints &&
            oldRawScreenPoints.length > 0 &&
            oldRawScreenPoints[0] &&
            typeof oldRawScreenPoints[0].screenY === 'number';

          // Store new raw screen coordinates for future transitions
          trendPath.datum(newRawScreenPoints);

          const screenLine = d3.line()
            .x(d => xScale(d.date))
            .y(d => d.screenY)
            .curve(d3.curveMonotoneX);

          if (hasValidOldScreenY) {
            // Build a map of old screen Y values by date timestamp for fast lookup
            const oldScreenYByDate = new Map();
            oldRawScreenPoints.forEach(p => {
              oldScreenYByDate.set(p.date.getTime(), p.screenY);
            });

            trendPath
              .transition()
              .duration(ANIMATION_DURATION)
              .attrTween('d', function() {
                return function(t) {
                  const interpolatedPoints = newRawScreenPoints.map(point => {
                    const dateTime = point.date.getTime();
                    const startY = oldScreenYByDate.get(dateTime) ?? point.screenY;
                    return {
                      date: point.date,
                      screenY: startY + (point.screenY - startY) * t
                    };
                  });
                  return screenLine(clipScreenPointsAtBottom(interpolatedPoints, height));
                };
              });
          } else {
            // No valid old screen coordinates - just set directly
            const clippedScreenPoints = clipScreenPointsAtBottom(newRawScreenPoints, height);
            trendPath.attr('d', screenLine(clippedScreenPoints));
          }
        }
      }
    }
  }
}

function formatReleaseDate(date) {
  const locale = CHART_LOCALE === 'zh-Hans' ? 'zh-Hans' : (CHART_LOCALE === 'es' ? 'es' : 'en');
  return new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric' }).format(date);
}

function formatDuration(hours) {
  const parts = localizedDurationParts(hours);

  if (CHART_LOCALE === 'zh-Hans') {
    if (parts.seconds !== undefined) return `${parts.seconds} 秒`;
    if (parts.minutes !== undefined && parts.hours === undefined) return parts.minutes === 60 ? '1 小时' : `${parts.minutes} 分钟`;
    if (parts.days !== undefined) {
      if (!parts.hours) return `${parts.days} 天`;
      return `${parts.days} 天 ${parts.hours} 小时`;
    }
    if (!parts.minutes) return `${parts.hours} 小时`;
    return `${parts.hours} 小时 ${parts.minutes} 分钟`;
  }

  if (CHART_LOCALE === 'es') {
    if (parts.seconds !== undefined) return `${parts.seconds} segundos`;
    if (parts.minutes !== undefined && parts.hours === undefined) return parts.minutes === 60 ? '1 hora' : `${parts.minutes} ${parts.minutes === 1 ? 'minuto' : 'minutos'}`;
    if (parts.days !== undefined) {
      const days = `${parts.days} ${parts.days === 1 ? 'día' : 'días'}`;
      if (!parts.hours) return days;
      return `${days} ${parts.hours} ${parts.hours === 1 ? 'hora' : 'horas'}`;
    }
    if (!parts.minutes) return `${parts.hours} ${parts.hours === 1 ? 'hora' : 'horas'}`;
    return `${parts.hours} ${parts.hours === 1 ? 'hora' : 'horas'} ${parts.minutes} ${parts.minutes === 1 ? 'minuto' : 'minutos'}`;
  }

  if (parts.seconds !== undefined) return `${parts.seconds} seconds`;
  if (parts.minutes !== undefined && parts.hours === undefined) {
    if (parts.minutes === 60) return '1 hour';
    return `${parts.minutes} ${parts.minutes === 1 ? 'minute' : 'minutes'}`;
  }
  if (parts.days !== undefined) {
    if (!parts.hours) return `${parts.days} ${parts.days === 1 ? 'day' : 'days'}`;
    return `${parts.days} ${parts.days === 1 ? 'day' : 'days'} ${parts.hours} ${parts.hours === 1 ? 'hour' : 'hours'}`;
  }
  if (!parts.minutes) return `${parts.hours} ${parts.hours === 1 ? 'hour' : 'hours'}`;
  return `${parts.hours} ${parts.hours === 1 ? 'hour' : 'hours'} ${parts.minutes} ${parts.minutes === 1 ? 'minute' : 'minutes'}`;
}

function rerenderChart() {
  d3.select('#time-horizon-chart').selectAll('*').remove();
  d3.selectAll('.tooltip').remove();
  initChart();
}

document.addEventListener('DOMContentLoaded', function() {
  initChart();

  // On a cold load Montserrat may not be ready when initChart() measures label widths, so the
  // right margin (and the rightmost label's centering) get sized from fallback-font metrics.
  // Re-render once the font finishes loading so they reflect the real Montserrat metrics.
  // (Guarded so warm loads, where the font is already cached, don't re-render needlessly.)
  if (document.fonts && !document.fonts.check('500 12px Montserrat')) {
    document.fonts.ready.then(rerenderChart);
  }

  // Add resize event listener with debouncing
  let resizeTimer;
  window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(rerenderChart, RESIZE_DEBOUNCE_DELAY);
  });
});
