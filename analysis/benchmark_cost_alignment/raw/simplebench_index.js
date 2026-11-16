window.HELP_IMPROVE_VIDEOJS = false;


$(document).ready(function() {
    // Check for click events on the navbar burger icon

    var options = {
			slidesToScroll: 1,
			slidesToShow: 1,
			loop: true,
			infinite: true,
			autoplay: true,
			autoplaySpeed: 5000,
    }

		// Initialize all div with carousel class
    var carousels = bulmaCarousel.attach('.carousel', options);
	
    bulmaSlider.attach();

})

function toggleSettings() {
	var settingsInfo = document.getElementById("settingsInfo");
	if (settingsInfo.style.display === "none" || settingsInfo.style.display === "") {
		settingsInfo.style.display = "block";
	} else {
		settingsInfo.style.display = "none";
	}
}

function isNewEntry(dateAdded) {
	if (!dateAdded) return false;
	const addedDate = new Date(dateAdded);
	const today = new Date();
	const twoWeeksAgo = new Date(today.getTime() - (14 * 24 * 60 * 60 * 1000));
	return addedDate >= twoWeeksAgo;
}

// Blended price = weighted $/1M tokens. Industry-standard 3:1 input:output weighting
// (the Artificial Analysis convention). Change these two numbers to reweight everything.
const INPUT_WEIGHT = 3, OUTPUT_WEIGHT = 1;
function blendedPrice(meta) {
	return (INPUT_WEIGHT * meta.input + OUTPUT_WEIGHT * meta.output) / (INPUT_WEIGHT + OUTPUT_WEIGHT);
}
function scoreNum(s) {
	const n = parseFloat(s);
	return isNaN(n) ? null : n;
}


// Timeline dot colours by organization (per site spec). Anything not listed -> "Other".
const ORG_COLORS = {
	'Google': '#1a73e8',      // gemini blue
	'OpenAI': '#e5484d',      // red
	'Anthropic': '#e8710a',   // orange
	'xAI': '#111827',         // black
	'DeepSeek': '#56b8e6',    // light blue
	'MiniMax': '#ec4899',     // pink
	'Nvidia': '#16a34a',      // green
	'Moonshot AI': '#4f46e5', // moonshot indigo
	'Alibaba': '#8b5cf6',      // qwen purple
	'Thinking Machines': '#ca8a04', // gold
	'Meta': '#65a30d'         // lime
};
const OTHER_COLOR = '#0d9488'; // distinctive teal for everyone else
function orgColor(org) { return ORG_COLORS[org] || OTHER_COLOR; }
// Model family for hover-highlight grouping (e.g. all GPTs, all Kimis, all Claudes).
function familyOf(model) { return String(model).trim().split(/[\s-]/)[0]; }
const LEGEND_ORDER = ['Google', 'OpenAI', 'Anthropic', 'xAI', 'DeepSeek', 'MiniMax', 'Nvidia', 'Alibaba', 'Moonshot AI', 'Thinking Machines', 'Meta', 'Other'];

function clearBoard() {
	const table = document.getElementById('leaderboardTable');
	table.innerHTML = '';
	return table;
}
function headerRow(cols) {
	const tr = document.createElement('tr');
	cols.forEach(c => {
		const th = document.createElement('th');
		if (c.center) th.className = 'center-align';
		th.textContent = c.label;
		tr.appendChild(th);
	});
	return tr;
}
function setNote(html) {
	document.getElementById('tabNote').innerHTML = html || '';
}
function showTable() {
	document.getElementById('leaderboardTable').style.display = '';
	document.getElementById('timelineChart').style.display = 'none';
	const pc = document.getElementById('perfChart');
	if (pc) pc.style.display = 'none';
	const pw = document.getElementById('perfWinners');
	if (pw) pw.style.display = 'none';
}

// --- MCQ / Open-Ended (unchanged columns) ---
function renderStandard(data) {
	showTable();
	const table = clearBoard();
	table.appendChild(headerRow([
		{ label: 'Rank' }, { label: 'Model' },
		{ label: 'Score (AVG@5)', center: true }, { label: 'Organization' }
	]));
	data.forEach(entry => {
		const row = table.insertRow();
		const newBadge = isNewEntry(entry.dateAdded)
			? '<span class="tag is-success is-light" style="margin-left: 8px; font-size: 0.7em;">NEW</span>'
			: '';
		row.innerHTML =
			`<td class="rank">${entry.rank}${newBadge}</td>` +
			`<td>${entry.model}</td>` +
			`<td>${entry.score}</td>` +
			`<td>${entry.organization}</td>`;
	});
	setNote('');
}

// --- Perf / $ : score-vs-cost scatter on top, combined table beneath ---
function buildPerfRows() {
	const PERF_EXCLUDE = new Set(['GPT-OSS 120B', 'Grok 4.1 Fast']); // Grok 4.1 Fast price was a guess
	// cpr = pre-computed cost to run the whole benchmark once (measured tokens x OpenRouter price).
	return leaderboardData
		.filter(e => !/Human/.test(e.model) && scoreNum(e.score) != null
			&& modelMeta[e.model] && modelMeta[e.model].cpr != null && !PERF_EXCLUDE.has(e.model))
		.map(e => {
			const m = modelMeta[e.model];
			return {
				model: e.model, org: e.organization, score: scoreNum(e.score),
				outTok: m.tout, costRun: m.cpr, perf: scoreNum(e.score) / m.cpr, est: m.est
			};
		})
		.sort((a, b) => b.perf - a.perf);
}

// Three value-winner cards (best "% per $" in each price/score bracket). Shown on Perf/$ + Timeline.
function renderWinners(rows) {
	rows = rows || buildPerfRows();
	const bestBy = pred => rows.filter(pred).sort((a, b) => b.perf - a.perf)[0];
	const cheap = bestBy(r => r.costRun < 1);
	const mid = bestBy(r => r.costRun >= 1 && r.costRun < 5);
	const big = bestBy(r => r.costRun >= 5);
	const card = (title, sub, r) => {
		if (!r) return `<div class="winner-card"><div class="winner-title">${title}</div><div class="winner-sub">${sub}</div><div class="winner-model">—</div></div>`;
		return `<div class="winner-card">` +
			`<div class="winner-title">${title}</div>` +
			`<div class="winner-sub">${sub}</div>` +
			`<div class="winner-model"><span class="legend-dot" style="background:${orgColor(r.org)}"></span>${r.model}</div>` +
			`<div class="winner-perf">${r.perf.toFixed(1)}<span> % per $</span></div>` +
			`<div class="winner-meta"><b>${r.score.toFixed(1)}%</b> score<br>$${r.costRun.toFixed(2)}/run</div>` +
			`</div>`;
	};
	const el = document.getElementById('perfWinners');
	el.innerHTML =
		card('🏆 Best Cheap Model', 'under $1 / run', cheap) +
		card('🏆 Best Mid Model', '$1&ndash;5 / run', mid) +
		card('🏆 Best Big Model', 'over $5 / run', big);
	el.style.display = '';
}

function renderPerf() {
	document.getElementById('leaderboardTable').style.display = 'none';
	document.getElementById('timelineChart').style.display = 'none';
	const perfChart = document.getElementById('perfChart');
	perfChart.style.display = '';
	clearBoard();
	const rows = buildPerfRows();

	renderParetoChart(perfChart, rows);

	// Dot family-highlight: hovering a dot lights that model's whole family
	// (all GPTs, all Kimis, ...); everything else dims.
	const dotEls = Array.from(perfChart.querySelectorAll('.dot'));
	dotEls.forEach(d => {
		const famD = familyOf(rows[+d.dataset.i].model);
		d.addEventListener('mouseenter', () => dotEls.forEach(o => { o.style.opacity = familyOf(rows[+o.dataset.i].model) === famD ? '1' : '0.12'; }));
		d.addEventListener('mouseleave', () => dotEls.forEach(o => { o.style.opacity = ''; }));
	});

	renderWinners(rows);
	setNote('(Recent models only &middot; “% per $” = score ÷ $/run)');
}

// Score-vs-cost scatter. X = cost per full benchmark run (log scale), Y = score %.
// Dots coloured by org; a subtle green value-gradient shades the plot (greenest top-left
// = high score + cheap, palest bottom-right = low score + expensive).
function renderParetoChart(chart, rows) {
	const W = 800, H = 470, ml = 52, mr = 20, mt = 18, mb = 62;
	const plotW = W - ml - mr, plotH = H - mt - mb;
	const costs = rows.map(r => r.costRun);
	const L0 = Math.log10(Math.min(...costs) * 0.8), L1 = Math.log10(Math.max(...costs) * 1.25);
	const yBot = 10, yTop = 90;
	const x = c => ml + (Math.log10(c) - L0) / (L1 - L0) * plotW;
	const y = s => mt + (yTop - s) / (yTop - yBot) * plotH;

	let svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Score versus cost">`;
	// Subtle value shading: greenest at top-left (high score, cheap), palest toward bottom-right.
	svg += `<defs><linearGradient id="valueGrad" x1="0" y1="0" x2="1" y2="1">` +
		`<stop offset="0" stop-color="#bbdec5"/><stop offset="1" stop-color="#f8fcf9"/></linearGradient></defs>`;
	svg += `<rect x="${ml}" y="${mt}" width="${plotW}" height="${plotH}" fill="url(#valueGrad)"/>`;
	for (let s = yBot; s <= yTop; s += 20) {
		svg += `<line x1="${ml}" y1="${y(s)}" x2="${W - mr}" y2="${y(s)}" class="grid"/>`;
		svg += `<text x="${ml - 8}" y="${y(s) + 4}" class="axis-lbl" text-anchor="end">${s}%</text>`;
	}
	[0.1, 0.3, 1, 3, 10, 30, 100, 300].filter(t => Math.log10(t) >= L0 && Math.log10(t) <= L1).forEach(t => {
		svg += `<line x1="${x(t)}" y1="${mt}" x2="${x(t)}" y2="${H - mb}" class="grid"/>`;
		svg += `<text x="${x(t)}" y="${H - mb + 18}" class="axis-lbl" text-anchor="middle">$${t}</text>`;
	});
	svg += `<line x1="${ml}" y1="${H - mb}" x2="${W - mr}" y2="${H - mb}" class="axis"/>`;
	svg += `<line x1="${ml}" y1="${mt}" x2="${ml}" y2="${H - mb}" class="axis"/>`;
	svg += `<text x="${ml + plotW / 2}" y="${H - 12}" class="axis-title" text-anchor="middle">&#8592; Cheaper &#160;&#160;&#160;&#160;&#160; $ per full benchmark run (log) &#160;&#160;&#160;&#160;&#160; More expensive &#8594;</text>`;
	svg += `<text transform="translate(15 ${mt + plotH / 2}) rotate(-90)" class="axis-title" text-anchor="middle">&#8592; Lower &#160;&#160;&#160; Score (%) &#160;&#160;&#160; Higher &#8594;</text>`;
	rows.forEach((r, i) => {
		svg += `<circle cx="${x(r.costRun).toFixed(1)}" cy="${y(r.score).toFixed(1)}" r="5" class="dot" fill="${orgColor(r.org)}" data-i="${i}"/>`;
	});
	svg += `</svg>`;
	chart.querySelector('.chart-svg').innerHTML = svg;

	const shown = LEGEND_ORDER.filter(o => o === 'Other' ? rows.some(r => !ORG_COLORS[r.org]) : rows.some(r => r.org === o));
	chart.querySelector('.chart-legend').innerHTML = shown.map(o => {
		const c = o === 'Other' ? OTHER_COLOR : ORG_COLORS[o];
		return `<span class="legend-item"><span class="legend-dot" style="background:${c}"></span>${o}</span>`;
	}).join('');

	const tip = chart.querySelector('.chart-tip');
	chart.querySelectorAll('.dot').forEach(dot => {
		const r = rows[+dot.getAttribute('data-i')];
		dot.addEventListener('mouseenter', () => {
			dot.classList.add('dot-hi');
			const bb = dot.getBoundingClientRect(), cr = chart.getBoundingClientRect();
			tip.innerHTML = `<b>${r.model}</b><br><b>${r.perf.toFixed(1)} % per $</b><br>${r.score.toFixed(1)}% score &middot; $${r.costRun.toFixed(2)}/run`;
			tip.style.left = (bb.left - cr.left + bb.width / 2) + 'px';
			tip.style.top = (bb.top - cr.top - 10) + 'px';
			tip.style.opacity = 1;
		});
		dot.addEventListener('mouseleave', () => { dot.classList.remove('dot-hi'); tip.style.opacity = 0; });
	});
}

// --- Timeline (release date vs score, single-hue scatter, model on hover) ---
function renderTimeline() {
	document.getElementById('leaderboardTable').style.display = 'none';
	const pc = document.getElementById('perfChart');
	if (pc) pc.style.display = 'none';
	const chart = document.getElementById('timelineChart');
	chart.style.display = '';

	const pts = leaderboardData
		.filter(e => !/Human/.test(e.model) && scoreNum(e.score) != null && modelMeta[e.model] && modelMeta[e.model].released)
		.map(e => ({ model: e.model, org: e.organization, score: scoreNum(e.score), t: new Date(modelMeta[e.model].released).getTime(), released: modelMeta[e.model].released }));

	const W = 800, H = 460, ml = 46, mr = 18, mt = 18, mb = 42;
	const plotW = W - ml - mr, plotH = H - mt - mb;
	const times = pts.map(p => p.t);
	const tMin = Math.min(...times), tMax = Math.max(...times);
	const pad = (tMax - tMin) * 0.03;
	const t0 = tMin - pad, t1 = tMax + pad;
	const x = t => ml + (t - t0) / (t1 - t0) * plotW;
	const y = s => mt + (100 - s) / 100 * plotH;

	// X ticks: 1st of Jan & Jul spanning the data
	const xTicks = [];
	const dMin = new Date(t0), dMax = new Date(t1);
	let yr = dMin.getUTCFullYear();
	for (let Y = yr; Y <= dMax.getUTCFullYear(); Y++) {
		[0, 6].forEach(mo => {
			const d = Date.UTC(Y, mo, 1);
			if (d >= t0 && d <= t1) xTicks.push(d);
		});
	}
	const monthLbl = ['Jan', 'Jul'];
	const fmtTick = ms => { const d = new Date(ms); return (d.getUTCMonth() === 0 ? 'Jan' : 'Jul') + " '" + String(d.getUTCFullYear()).slice(2); };

	let svg = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Model score by release date">`;
	// Y gridlines + labels
	for (let s = 0; s <= 100; s += 20) {
		svg += `<line x1="${ml}" y1="${y(s)}" x2="${W - mr}" y2="${y(s)}" class="grid"/>`;
		svg += `<text x="${ml - 8}" y="${y(s) + 4}" class="axis-lbl" text-anchor="end">${s}%</text>`;
	}
	// Human baseline reference line (site thesis)
	const hb = 83.7;
	svg += `<line x1="${ml}" y1="${y(hb)}" x2="${W - mr}" y2="${y(hb)}" class="baseline"/>`;
	svg += `<text x="${W - mr}" y="${y(hb) - 6}" class="axis-lbl baseline-lbl" text-anchor="end">Human baseline ${hb}%</text>`;
	// X ticks + labels
	xTicks.forEach(ms => {
		svg += `<line x1="${x(ms)}" y1="${mt}" x2="${x(ms)}" y2="${H - mb}" class="grid"/>`;
		svg += `<text x="${x(ms)}" y="${H - mb + 20}" class="axis-lbl" text-anchor="middle">${fmtTick(ms)}</text>`;
	});
	// Axis lines
	svg += `<line x1="${ml}" y1="${H - mb}" x2="${W - mr}" y2="${H - mb}" class="axis"/>`;
	svg += `<line x1="${ml}" y1="${mt}" x2="${ml}" y2="${H - mb}" class="axis"/>`;
	// Points
	// Trend: ordinary least-squares line of best fit — a single straight line across the
	// full range, to convey the steady upward march. x normalised to [0,1] for stability.
	const span = t1 - t0, n = pts.length;
	const xn = pts.map(p => (p.t - t0) / span);
	const mx = xn.reduce((a, b) => a + b, 0) / n;
	const my = pts.reduce((a, p) => a + p.score, 0) / n;
	let sxy = 0, sxx = 0;
	for (let i = 0; i < n; i++) { sxy += (xn[i] - mx) * (pts[i].score - my); sxx += (xn[i] - mx) * (xn[i] - mx); }
	const slope = sxx > 1e-9 ? sxy / sxx : 0, intercept = my - slope * mx;
	svg += `<line x1="${x(t0).toFixed(1)}" y1="${y(intercept).toFixed(1)}" x2="${x(t1).toFixed(1)}" y2="${y(intercept + slope).toFixed(1)}" class="trend"/>`;
	pts.forEach((p, i) => {
		svg += `<circle cx="${x(p.t).toFixed(1)}" cy="${y(p.score).toFixed(1)}" r="5" class="dot" fill="${orgColor(p.org)}" data-i="${i}"/>`;
	});
	svg += `</svg>`;
	chart.querySelector('.chart-svg').innerHTML = svg;

	// Family hover-highlight (dots only; timeline has no stat table).
	const tDots = Array.from(chart.querySelectorAll('.dot'));
	tDots.forEach(d => {
		const famJ = familyOf(pts[+d.dataset.i].model);
		d.addEventListener('mouseenter', () => tDots.forEach(o => { o.style.opacity = familyOf(pts[+o.dataset.i].model) === famJ ? '1' : '0.12'; }));
		d.addEventListener('mouseleave', () => tDots.forEach(o => { o.style.opacity = ''; }));
	});

	// Legend (colour is meaningful now, so identity is never colour-alone)
	const shown = LEGEND_ORDER.filter(o => o === 'Other'
		? pts.some(p => !ORG_COLORS[p.org])
		: pts.some(p => p.org === o));
	chart.querySelector('.chart-legend').innerHTML = shown.map(o => {
		const c = o === 'Other' ? OTHER_COLOR : ORG_COLORS[o];
		return `<span class="legend-item"><span class="legend-dot" style="background:${c}"></span>${o}</span>`;
	}).join('');

	// Hover tooltip
	const tip = chart.querySelector('.chart-tip');
	const fmtDate = iso => { const d = new Date(iso); return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getUTCMonth()] + ' ' + d.getUTCFullYear(); };
	chart.querySelectorAll('.dot').forEach(dot => {
		const p = pts[+dot.getAttribute('data-i')];
		// Hover shows the tooltip only — no resize, no z-reorder (both left dots stuck big).
		dot.addEventListener('mouseenter', () => {
			dot.classList.add('dot-hi');
			const r = dot.getBoundingClientRect(), cr = chart.getBoundingClientRect();
			tip.innerHTML = `<b>${p.model}</b><br>${p.score.toFixed(1)}% &middot; ${fmtDate(p.released)}`;
			tip.style.left = (r.left - cr.left + r.width / 2) + 'px';
			tip.style.top = (r.top - cr.top - 10) + 'px';
			tip.style.opacity = 1;
		});
		dot.addEventListener('mouseleave', () => { dot.classList.remove('dot-hi'); tip.style.opacity = 0; });
	});
	setNote('Each point is a model at its public-release date (OpenRouter listing date). Hover for name, score and date. ' +
		'Human baseline (83.7%) shown for reference.');
	renderWinners();
}

function switchTab(tab) {
	// Highlight by matching each button's own onclick target, so it stays correct
	// no matter how many tabs exist or what order they're in.
	document.querySelectorAll('.leaderboard-tab').forEach(t => {
		const on = t.getAttribute('onclick') || '';
		t.classList.toggle('active', on.indexOf("'" + tab + "'") !== -1);
	});
	if (tab === 'mcq') renderStandard(leaderboardData);
	else if (tab === 'open-ended') renderStandard(openEndedData);
	else if (tab === 'perf') renderPerf();
	else if (tab === 'timeline') renderTimeline();
	// Video Summary stays on the score tables; the two chart tabs point to Patreon instead.
	const chartTab = (tab === 'perf' || tab === 'timeline');
	const vs = document.getElementById('videoSummary'), pn = document.getElementById('patreonNote');
	if (vs) vs.style.display = chartTab ? 'none' : '';
	if (pn) pn.style.display = chartTab ? '' : 'none';
}

document.addEventListener('DOMContentLoaded', () => {
	renderStandard(leaderboardData);
});

