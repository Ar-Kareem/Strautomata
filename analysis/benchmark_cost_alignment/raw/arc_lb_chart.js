"use strict";
// @ts-nocheck
const namedReasoningLevels = [
    { pattern: /\bnone\b/i, rank: 0 },
    { pattern: /\bminimal\b/i, rank: 1 },
    { pattern: /\blow\b/i, rank: 2 },
    { pattern: /\bmedium\b/i, rank: 3 },
    { pattern: /\b(?:xhigh|x-high|extra[\s_-]*high)\b/i, rank: 5 },
    { pattern: /\bhigh\b/i, rank: 4 },
    { pattern: /\bmax(?:imum)?\b/i, rank: 6 },
];
/**
 * Returns a model's explicit reasoning level, when one is present in its
 * display name or id. Named levels and numeric thinking budgets are kept as
 * separate scales because they are not directly comparable.
 */
function getModelReasoningOrder(datum) {
    const displayName = String(datum.modelDisplayName || "");
    const parentheticalSections = [];
    const parentheticalPattern = /\(([^)]*)\)/g;
    let parentheticalMatch;
    while ((parentheticalMatch = parentheticalPattern.exec(displayName)) !== null) {
        parentheticalSections.push(parentheticalMatch[1]);
    }
    // Display names consistently put reasoning levels in parentheses. Only
    // inspect the id when a display name is unavailable so model names such as
    // "Magistral Medium" are not mistaken for reasoning levels.
    const label = parentheticalSections.length > 0
        ? parentheticalSections.join(" ")
        : displayName
            ? ""
            : String(datum.modelId || "");
    for (const level of namedReasoningLevels) {
        if (level.pattern.test(label)) {
            return { kind: "named", rank: level.rank };
        }
    }
    const budgetMatch = label.match(/\b(\d+(?:\.\d+)?)\s*k\b/i);
    if (budgetMatch) {
        return { kind: "budget", rank: Number(budgetMatch[1]) };
    }
    return null;
}
/**
 * Returns true for an explicit none reasoning level. These points remain visible
 * but do not participate in model-family connector lines.
 */
function isNoneReasoningLevel(datum) {
    const order = getModelReasoningOrder(datum);
    return (order === null || order === void 0 ? void 0 : order.kind) === "named" && order.rank === 0;
}
/**
 * Orders points from the least to the most reasoning within a model family.
 * Cost remains the deterministic fallback for models without explicit levels.
 */
function compareModelReasoningLevels(a, b, xAccessor = d => d.costPerTask) {
    const aOrder = getModelReasoningOrder(a);
    const bOrder = getModelReasoningOrder(b);
    if (aOrder && bOrder && aOrder.kind === bOrder.kind && aOrder.rank !== bOrder.rank) {
        return aOrder.rank - bOrder.rank;
    }
    // An unlabelled base model precedes its explicitly reasoned variants.
    if (!aOrder && bOrder)
        return -1;
    if (aOrder && !bOrder)
        return 1;
    const costDifference = Number(xAccessor(a)) - Number(xAccessor(b));
    if (Number.isFinite(costDifference) && costDifference !== 0) {
        return costDifference;
    }
    return String(a.modelId || "").localeCompare(String(b.modelId || ""));
}
// Results pages draw their emphasized model-family line as an overlay after
// the shared chart renders, so expose the same comparator for that overlay.
globalThis.compareModelReasoningLevels = compareModelReasoningLevels;
globalThis.isNoneReasoningLevel = isNoneReasoningLevel;
/**
 * reusableScatterplot
 *
 * Creates a reusable scatterplot chart component using D3.js.
 *
 * @returns {function} A chart function that can be called on a D3 selection.
 */
function reusableScatterplot() {
    // --- Default Configuration ---
    let width = 800;
    let height = 450;
    let responsive = false; // viewBox-based sizing: scale down to fit narrow containers
    let margin = { top: 20, right: 65, bottom: 40, left: 105 };
    let xAxisLabel = "COST PER TASK ($)";
    let yAxisLabel = "SCORE (%)";
    let xAxisMin = 0.001;
    let xAxisMinLabel = null;
    let xAxisMax = 100;
    let yAxisMin = 0;
    let yAxisMax = 100; // Initial Y-axis max
    let xScaleType = "log";
    let showLabels = true;
    let labelPadding = 8; // Pixels between point and label
    let labelCollisionDetection = true;
    let labelFontSize = "10px";
    let labelColor = "#dbdbdb";
    // --- Accessor Functions ---
    // These functions define how to get the necessary data properties from each datum
    let xValue = d => d.costPerTask;
    let yValue = d => d.score * 100;
    let idValue = d => `${d.modelId}-${d.datasetId}`; // Unique identifier for points
    let versionValue = d => d.datasetId;
    let providerValue = d => d.providerDisplayName; // For color mapping
    let modelGroupValue = d => d.modelGroup; // For connecting points within same group
    let labelValue = d => d.modelDisplayName;
    // --- Internal Variables ---
    let svg, g, x, y, xAxis, yAxis, pointsGroup, gridGroup, labelsGroup, linesGroup, annotationsGroup; // D3 selections and scales
    let initialized = false; // Flag to track if initial setup is done
    let fullData = []; // Store the complete dataset
    let originalXDomain = [xAxisMin, xAxisMax];
    let originalYDomain = [yAxisMin, yAxisMax];
    let currentHighlightSet = null; // Store the set of highlighted point IDs
    let quadtree; // Quadtree for efficient hover detection
    let tooltipDiv; // Tooltip element
    let hoverTarget = null; // Store the currently hovered point ID
    let currentColorMapping = {}; // Default empty object for custom color mappings
    let currentColorMode = "provider"; // Default to "provider" mode
    let highlightId = null; // Optional id of a single point to emphasize (e.g. config subject)
    // --- Subject dimming -------------------------------------------------
    // A "subject" is the point (or set of points) the viewer cares about — e.g.
    // a single config or a whole model family. When a subject set is provided,
    // every non-subject point, its model-group line, and its label are faded to
    // `dimOpacity` so the subject stands out. One value drives all three.
    let subjectIds = null; // Set<string> of subject point ids, or null = none
    let dimOpacity = 1; // opacity for non-subject points/lines/labels (1 = off)
    const highlightDimOpacity = 0.15;
    const highlightDimColor = "#555555";
    const hoverStrokeColor = "#ffffff"; // White stroke on hover
    const hoverStrokeWidth = 1.5;
    const hoverSearchRadius = 50; // Search radius for quadtree
    // --- Symbol Mapping ---
    const triangleSymbol = d3.symbol().type(d3.symbolTriangle).size(20);
    const circleSymbol = d3.symbol().type(d3.symbolCircle).size(25);
    const starSymbol = d3.symbol().type(d3.symbolStar).size(25);
    const basePointSize = 25; // Default circle symbol area (keep in sync with circleSymbol)
    const highlightPointSize = basePointSize * 9; // ~3x diameter for the emphasized point
    const highlightStrokeColor = "#ffffff"; // Halo ring around the emphasized point
    const highlightStrokeWidth = 1.5;
    const highlightLabelFontSize = "13px"; // Larger, bold label for the emphasized point
    const defaultColor = labelColor; // "#ffdc00ff"; // Color for unknown values
    function pointSymbol(d, size) {
        return (d.pointShape === "star" ? starSymbol : circleSymbol).size(size)();
    }
    // --- Subject helpers -------------------------------------------------
    // A point is a "subject" when it is the single emphasized point (highlightId)
    // or a member of the subject set. With no subject configured, everything is
    // treated as a subject (so nothing is dimmed).
    function isSubjectId(id) {
        if (highlightId != null && id === highlightId)
            return true;
        if (subjectIds && subjectIds.size > 0)
            return subjectIds.has(id);
        return true;
    }
    function isSubject(d) {
        return isSubjectId(idValue(d));
    }
    /** Opacity for an element, dimming it when it is not part of the subject. */
    function subjectOpacity(d, base = 1) {
        return isSubject(d) ? base : base * dimOpacity;
    }
    /**
     * The main chart function that processes the selection and data.
     * @param {d3.Selection} selection - The D3 selection to render the chart into.
     */
    function chart(selection) {
        selection.each(function (data) {
            //console.log("SELECTION DATA", data);
            fullData = data; // Store the full dataset
            currentHighlightSet = null; // Reset highlight on new data
            // Interrupt all running transitions to prevent overlap when switching versions quickly
            if (initialized && g) {
                g.selectAll("*").interrupt();
                pointsGroup.selectAll(".point").interrupt();
                labelsGroup.selectAll(".point-label").interrupt();
                linesGroup.selectAll("*").interrupt();
                annotationsGroup.selectAll("*").interrupt();
            }
            // Calculate inner dimensions based on current width/height/margins
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            // Store original domains from config
            originalXDomain = [xAxisMin, xAxisMax];
            originalYDomain = [yAxisMin, yAxisMax];
            // --- Initialize Scales ---
            x = (xScaleType === "time" ? d3.scaleUtc() : d3.scaleLog())
                .domain(originalXDomain) // Use initial domain
                .range([0, innerWidth]);
            if (xScaleType === "log") {
                x.nice();
            }
            y = d3.scaleLinear()
                .domain(originalYDomain) // Use initial domain
                .range([innerHeight, 0])
                .nice();
            // --- Initialize Axes ---
            xAxis = d3.axisBottom(x)
                .tickValues(getXAxisTickValues(x, innerWidth))
                .tickFormat(formatXAxisTick) // Use helper for formatting
                .tickSizeOuter(0);
            yAxis = d3.axisLeft(y)
                .ticks(10) // Adjust number of ticks as needed
                .tickFormat(d => `${d}%`) // Format as percentage
                .tickSizeOuter(0);
            // --- SVG and Group Setup (run once) ---
            if (!initialized) {
                svg = d3.select(this).append("svg");
                g = svg.append("g");
                // Add background rect
                g.append("rect")
                    .attr("class", "chart-background")
                    .attr("fill", "var(--offblack)"); // Match global site background
                // Add gridlines group (drawn before axes and points)
                gridGroup = g.append("g").attr("class", "grid-group");
                // Add axes groups
                g.append("g").attr("class", "x-axis axis");
                g.append("g").attr("class", "y-axis axis");
                // Add group for annotations (drawn after grid/axes, before points/lines)
                annotationsGroup = g.append("g").attr("class", "annotations-group");
                // Add group for model lines (between axes and points)
                linesGroup = g.append("g").attr("class", "model-lines-group");
                // Add points group
                pointsGroup = g.append("g").attr("class", "points-group");
                // Add labels group (after points so labels appear on top)
                labelsGroup = g.append("g").attr("class", "labels-group");
                // Add axis labels groups
                g.append("g").attr("class", "x-axis-label-group axis-label");
                g.append("g").attr("class", "y-axis-label-group axis-label");
                // Add logo group (positioned in top right)
                g.append("g").attr("class", "logo-group");
                // --- NEW: Initialize Tooltip ---
                tooltipDiv = d3.select("body").selectAll(".chart-tooltip").data([null])
                    .join("div") // Use join for enter/update
                    .attr("class", "chart-tooltip")
                    .style("position", "absolute")
                    .style("opacity", 0)
                    .style("background-color", "rgba(0, 0, 0, 0.9)")
                    .style("color", "#fff")
                    .style("padding", "8px 12px")
                    .style("border-radius", "4px")
                    .style("font-size", "12px")
                    .style("pointer-events", "none") // Prevent tooltip from capturing mouse events
                    .style("z-index", "10");
                initialized = true;
            }
            // Bind full data to SVG for potential later access
            svg.datum(fullData);
            // --- Update SVG and Group Dimensions ---
            if (responsive) {
                // Fixed pixel dimensions overflow and get clipped on narrow screens
                // (mobile). A viewBox lets the whole chart scale down with its
                // container; max-width caps it at the design size on desktop.
                svg.attr("viewBox", `0 0 ${width} ${height}`)
                    .attr("preserveAspectRatio", "xMidYMid meet")
                    .attr("width", null)
                    .attr("height", null)
                    .style("width", "100%")
                    .style("max-width", `${width}px`)
                    .style("height", "auto")
                    .style("display", "block");
            }
            else {
                svg.attr("width", width).attr("height", height);
            }
            g.attr("transform", `translate(${margin.left},${margin.top})`);
            g.select(".chart-background")
                .attr("width", innerWidth)
                .attr("height", innerHeight);
            // --- Draw Grid Lines ---
            drawGridLines(gridGroup, x, y, innerWidth, innerHeight);
            // --- Draw Axes ---
            g.select(".x-axis")
                .attr("transform", `translate(0,${innerHeight})`)
                .call(xAxis)
                .call(g => g.selectAll("text").attr("fill", "#9a9a9a")) // Style ticks
                .call(g => g.select(".domain").attr("stroke", "#555")); // Style axis line
            g.select(".y-axis")
                // .transition().duration(750) // No transition on initial draw
                .call(yAxis)
                .call(g => g.selectAll("text").attr("fill", "#9a9a9a")) // Style ticks
                .call(g => g.select(".domain").attr("stroke", "#555")); // Style axis line
            // --- Draw Axis Labels ---
            drawAxisLabels(g, innerWidth, innerHeight);
            // --- Draw Logo ---
            drawLogo(g, innerWidth, innerHeight);
            // --- Draw Max Annotations ---
            drawMaxAnnotation(annotationsGroup, fullData, x, y, innerWidth, null, 0);
            // --- Draw Model Group Lines ---
            // Pass full data and null highlightSet for initial draw
            drawModelGroups(linesGroup, fullData, x, y, 0, null);
            // --- Draw Points ---
            // Pass full data and null highlightSet for initial draw
            drawPoints(pointsGroup, fullData, x, y, 0, null);
            // --- Draw Labels (if enabled) ---
            if (showLabels) {
                // Pass full data and null highlightSet for initial draw
                drawLabels(labelsGroup, fullData, x, y, innerWidth, innerHeight, 0, null);
            }
            else {
                // Clear labels if disabled
                labelsGroup.selectAll(".point-label").remove();
            }
            // --- NEW: Setup Quadtree and Hover Listener ---
            setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, null);
        });
    }
    // --- Helper Functions ---
    /** Calculates nice tick values for a log scale. */
    function getLogTickValues(logScale) {
        const [minVal, maxVal] = logScale.domain();
        const ticks = [];
        // Handle potential non-positive minVal for log scale
        const startMinVal = Math.max(minVal, Number.MIN_VALUE); // Ensure positive value
        const minExp = Math.floor(Math.log10(startMinVal));
        const maxExp = Math.ceil(Math.log10(maxVal));
        for (let i = minExp; i <= maxExp; i++) {
            ticks.push(Math.pow(10, i));
        }
        return ticks.filter(t => t >= startMinVal && t <= maxVal); // Ensure ticks are within domain
    }
    /** Returns tick values appropriate for the configured X scale. */
    function getXAxisTickValues(xScale, innerWidth) {
        if (xScaleType === "time") {
            return xScale.ticks(Math.max(3, Math.floor(innerWidth / 130)));
        }
        return getLogTickValues(xScale);
    }
    /** Formats X-axis ticks as either dates or costs. */
    function formatXAxisTick(d) {
        if (xScaleType === "time") {
            return d3.utcFormat("%b %Y")(d);
        }
        if (xAxisMinLabel !== null &&
            Math.abs(d - xAxisMin) <= Math.abs(xAxisMin) * 1e-9) {
            return xAxisMinLabel;
        }
        if (d >= 1000)
            return `$${(d / 1000).toFixed(0)}K`;
        if (d < 0.01)
            return `$${d.toExponential(0)}`; // Use exponential for very small
        if (d < 1)
            return `$${d.toFixed(2)}`; // Show cents for values < $1
        return `$${d.toFixed(0)}`;
    }
    /** Draws grid lines for both axes. */
    function drawGridLines(selection, xScale, yScale, w, h) {
        selection.selectAll("*").remove(); // Clear previous gridlines
        const xTickValues = getXAxisTickValues(xScale, w);
        // X grid lines (vertical)
        selection.append("g")
            .attr("class", "grid x-grid")
            .style("pointer-events", "none")
            .attr("transform", `translate(0,${h})`)
            .call(d3.axisBottom(xScale)
            .tickValues(xTickValues)
            .tickSize(-h)
            .tickFormat(""))
            .call(g => g.selectAll("line")
            .attr("stroke", "#333")
            .attr("stroke-opacity", 0.7))
            .call(g => g.select(".domain").remove());
        // Y grid lines (horizontal)
        selection.append("g")
            .attr("class", "grid y-grid")
            .style("pointer-events", "none")
            .call(d3.axisLeft(yScale)
            .ticks(10) // Match Y axis ticks
            .tickSize(-w)
            .tickFormat(""))
            .call(g => g.selectAll("line")
            .attr("stroke", "#333")
            .attr("stroke-opacity", 0.7))
            .call(g => g.select(".domain").remove());
    }
    /** Draws X and Y axis labels. */
    function drawAxisLabels(selection, w, h) {
        // X Axis Label
        let xLabel = selection.select(".x-axis-label-group").selectAll("text")
            .data([xAxisLabel]); // Use data join pattern
        xLabel.exit().remove();
        xLabel.enter().append("text")
            .attr("class", "axis-title")
            .attr("text-anchor", "middle")
            .attr("fill", "#dbdbdb")
            .attr("font-size", "12px") // Smaller font size
            .attr("letter-spacing", "0.15em") // Adjust spacing
            .merge(xLabel) // Merge enter and update selections
            .attr("x", w / 2)
            .attr("y", h + margin.bottom - 5) // Position below axis ticks
            .text(d => d);
        // Y Axis Label
        let yLabel = selection.select(".y-axis-label-group").selectAll("text")
            .data([yAxisLabel]);
        yLabel.exit().remove();
        yLabel.enter().append("text")
            .attr("class", "axis-title")
            .attr("transform", "rotate(-90)")
            .attr("text-anchor", "middle")
            .attr("fill", "#dbdbdb")
            .attr("font-size", "12px") // Smaller font size
            .attr("letter-spacing", "0.15em") // Adjust spacing
            .merge(yLabel)
            .attr("x", -h / 2)
            .attr("y", -margin.left + 15) // Position left of axis ticks
            .text(d => d);
    }
    /** Draws the ARC Prize logo in the top left and URL in top right. */
    function drawLogo(selection, w, h) {
        const logoGroup = selection.select(".logo-group");
        // Clear previous logo
        logoGroup.selectAll("*").remove();
        // Add verified badge image
        const badgeHeight = 30;
        const badgeWidth = (283 / 80) * badgeHeight; // Maintain aspect ratio
        const badgeX = 14;
        const badgeY = 6;
        logoGroup.append("image")
            .attr("href", "/media/images/badges/arc-prize-verified-badge-dark-color.svg")
            .attr("x", badgeX)
            .attr("y", badgeY)
            .attr("width", badgeWidth)
            .attr("height", badgeHeight)
            .attr("opacity", 1)
            .attr("preserveAspectRatio", "xMidYMid meet");
    }
    /** Draws horizontal lines and text for max scores per version */
    function drawMaxAnnotation(selection, data, xScale, yScale, innerWidth, highlightSet = null, duration = 0) {
        // selection.selectAll("*").remove(); // Clear previous annotations
        const versions = ["ARC-AGI-1", "ARC-AGI-2"];
        const annotationData = [];
        // Determine the data subset to use for max calculation
        const relevantData = highlightSet ? data.filter(d => highlightSet.has(idValue(d))) : data;
        versions.forEach(v => {
            // Filter the *relevant* data for the current version (excluding Human for max calc)
            const versionData = relevantData.filter(d => d.version === v && d.Provider !== "Human");
            // Still find Human data from the *full* dataset for comparison context
            const humanData = data.find(d => d.version === v && d.Provider === "Human");
            //.log("HUMAN DATA", humanData); // Keep original human data lookup
            if (versionData.length > 0) {
                const maxEntry = versionData.reduce((max, p) => p.score > max.score ? p : max, versionData[0]);
                let diffText = "";
                if (humanData && maxEntry) { // Check if maxEntry exists
                    const diff = humanData.score - maxEntry.score;
                    // Only show diff if positive, indicating human is higher
                    if (diff > 0) {
                        diffText = `(${diff.toFixed(1)}% < Human)`;
                    }
                    else if (diff < 0) {
                        // Optional: Indicate if max in set is higher than human
                        // diffText = ` (${Math.abs(diff).toFixed(1)}% > Human)`;
                    }
                    else {
                        // Optional: Indicate if scores are equal
                        // diffText = ` (matches Human)`;
                    }
                }
                annotationData.push({
                    version: v,
                    score: maxEntry.score, // Use the score from the maxEntry within the subset
                    // yPos calculation moved to drawing phase to use latest scale
                    text: `Max${highlightSet ? ' (in selection)' : ''}: ${maxEntry.score.toFixed(1)}%`, // Update text
                    diff: diffText
                });
            }
            // Optional: Handle case where versionData is empty (no points of this version in selection)
            // else {
            //   annotationData.push({ version: v, score: null, text: `${v}: No data in selection`, diff: "" });
            // }
        });
        // --- Drawing Logic (Lines and Text) ---
        // Data join uses annotationData calculated above
        const lines = selection.selectAll(".annotation-line")
            .data(annotationData.filter(d => d.score !== null), d => d.version); // Filter out entries with no score
        lines.exit()
            .transition("anno-line-exit").duration(duration / 2)
            .attr("opacity", 0)
            .remove(); // Use remove()
        const linesEnter = lines.enter()
            .append("line")
            .attr("class", "annotation-line")
            .attr("x1", 0)
            .attr("x2", innerWidth)
            .attr("y1", d => yScale(d.score)) // Initial position
            .attr("y2", d => yScale(d.score)) // Initial position
            .attr("stroke", "#888")
            .attr("stroke-width", 1)
            .attr("opacity", 0) // Start transparent
            .attr("stroke-dasharray", "4,4");
        lines.merge(linesEnter)
            // .attr("opacity", 0.33) // Opacity set in transition
            .transition("anno-line-update").duration(duration)
            .attr("x2", innerWidth) // Update width in case it changed
            .attr("y1", d => yScale(d.score)) // Transition to new y position
            .attr("y2", d => yScale(d.score)) // Transition to new y position
            .attr("opacity", 0.5); // Fade in/maintain opacity
        // Draw Text Annotations
        const texts = selection.selectAll(".annotation-text")
            .data(annotationData.filter(d => d.score !== null), d => d.version); // Filter out entries with no score
        texts.exit()
            .transition("anno-text-exit").duration(duration / 2)
            .attr("opacity", 0)
            .remove(); // Use remove()
        const textsEnter = texts.enter()
            .append("text")
            .attr("class", "annotation-text")
            .attr("x", innerWidth + 5) // Initial position
            .attr("y", d => yScale(d.score)) // Initial position
            .attr("dy", "0.35em") // Adjusted dy for better alignment
            .attr("text-anchor", "start")
            .attr("fill", "#ccc")
            .style("font-size", "10px")
            .attr("opacity", 0); // Start transparent
        // Append tspans within the enter selection
        textsEnter.append("tspan")
            .attr("class", "annotation-text-version") // Class for main text
            .attr("x", innerWidth + 5) // Position relative to parent text start
            .text(d => d.version);
        textsEnter.append("tspan")
            .attr("class", "annotation-text-main") // Class for main text
            .attr("x", innerWidth + 5) // Position relative to parent text start
            .attr("dy", "1.2em") // Adjust dy for spacing below main text
            .text(d => d.text);
        textsEnter.append("tspan")
            .attr("class", "annotation-text-diff")
            .attr("x", innerWidth + 5) // Position relative to parent text start
            // .attr("y", d => yScale(d.score)) // y is controlled by parent text
            .attr("dy", "2.4em") // Adjust dy for spacing below main text
            .attr("text-anchor", "start")
            .attr("fill", "#aaa") // Slightly different color for diff
            .style("font-style", "italic")
            .text(d => d.diff);
        texts.merge(textsEnter)
            .transition("anno-text-update").duration(duration)
            .attr("x", innerWidth + 5) // Transition x (in case innerWidth changed)
            .attr("y", d => yScale(d.score)) // Transition y
            .attr("opacity", 1); // Fade in/maintain opacity
        // Update tspans within the merged selection
        texts.merge(textsEnter).select(".annotation-text-main")
            .text(d => d.text); // Update main text content
        texts.merge(textsEnter).select(".annotation-text-diff")
            .attr("x", innerWidth + 5) // Keep x aligned
            // .attr("y", d => yScale(d.score)) // Y position is handled by the parent text element
            .attr("dy", "1.2em") // Keep relative positioning
            .text(d => d.diff); // Update diff text content
    }
    /**
     * Draws the point labels with collision detection and transitions.
     * Handles highlighting by only drawing labels for the highlighted subset.
     * @param {d3.Selection} selection - The group element for labels.
     * @param {Array} data - The *full* dataset.
     * @param {d3.Scale} xScale - The X scale.
     * @param {d3.Scale} yScale - The Y scale.
     * @param {number} innerWidth - Chart inner width.
     * @param {number} innerHeight - Chart inner height.
     * @param {number} [duration=0] - Transition duration.
     * @param {Set|null} highlightSet - Set of IDs for highlighted points, or null if none.
     */
    function drawLabels(selection, data, xScale, yScale, innerWidth, innerHeight, duration = 0, highlightSet = null) {
        const targetLabels = {}; // Store target positions for collision detection
        // Determine the data to use for labels (only highlighted ones if set)
        // Also filter out data where displayLabel is explicitly false
        const labelData = (highlightSet ? data.filter(d => highlightSet.has(idValue(d))) : data)
            .filter(d => d.displayLabel !== false); // Show label if displayLabel is missing (undefined/null) or true
        // Calculate target positions first for *potentially* visible labels
        // Supports optional labelOffsetX and labelOffsetY properties on evaluation data
        labelData.forEach(d => {
            // Push the emphasized point's label further out so the larger dot doesn't overlap it.
            const extraPad = (highlightId != null && idValue(d) === highlightId) ? 6 : 0;
            const pointX = xScale(xValue(d));
            const labelOffsetX = d.labelOffsetX || 0;
            targetLabels[idValue(d)] = {
                id: idValue(d),
                pointX,
                extraPad,
                labelOffsetX,
                x: pointX + labelPadding + extraPad + labelOffsetX,
                y: yScale(yValue(d)) + (d.labelOffsetY || 0),
                anchor: "start"
            };
        });
        // Data Join using labelData
        const labels = selection.selectAll(".point-label")
            .data(labelData, d => idValue(d));
        // Exit: Transition out labels that are removed (no longer highlighted or removed from data)
        labels.exit()
            .transition("label-exit").duration(duration / 2)
            .attr("opacity", 0)
            .remove();
        // Enter: Add new labels, starting transparent and at target position
        const labelsEnter = labels.enter().append("text")
            .attr("class", d => `point-label label-${versionValue(d)} provider-${providerValue(d).replace(/\s+/g, '-').toLowerCase()}`)
            .attr("x", d => targetLabels[idValue(d)].x) // Start at target X
            .attr("y", d => targetLabels[idValue(d)].y) // Start at target Y
            .attr("dy", "0.35em")
            .attr("text-anchor", d => targetLabels[idValue(d)].anchor)
            .attr("font-size", d => (highlightId != null && idValue(d) === highlightId) ? highlightLabelFontSize : labelFontSize)
            .attr("font-weight", d => (highlightId != null && idValue(d) === highlightId) ? "bold" : "normal")
            .attr("data-id", d => idValue(d))
            .attr("opacity", 0) // Start transparent
            .style("pointer-events", "none")
            .text(d => labelValue(d));
        const combinedLabels = labels.merge(labelsEnter);
        // Measure the rendered text and flip only labels that would cross the
        // SVG's right edge. This keeps the chart centered at every viewport size.
        const rightBoundary = innerWidth + Math.max(0, margin.right - 4);
        combinedLabels.each(function (d) {
            const target = targetLabels[idValue(d)];
            const measuredWidth = typeof this.getComputedTextLength === "function"
                ? this.getComputedTextLength()
                : labelValue(d).length * 6;
            if (target.labelOffsetX >= 0
                && target.x + measuredWidth > rightBoundary) {
                target.x = target.pointX
                    - labelPadding
                    - target.extraPad
                    - target.labelOffsetX;
                target.anchor = "end";
            }
        });
        // Update + Enter: Transition both new and existing labels to final position/opacity
        const labelsUpdate = combinedLabels
            // .attr("opacity", 0) // Opacity transition handled below or by collision
            .transition("label-position").duration(duration) // Named transition
            .attr("x", d => targetLabels[idValue(d)].x)
            .attr("y", d => targetLabels[idValue(d)].y)
            .attr("text-anchor", d => targetLabels[idValue(d)].anchor)
            .attr("fill", d => {
            // if (highlightSet && !highlightSet.has(idValue(d))) {
            //   return highlightDimColor;
            // }
            let colorKey;
            if (currentColorMode === "provider") {
                colorKey = providerValue(d);
            }
            else if (currentColorMode === "version") {
                colorKey = versionValue(d);
            }
            else { // type or any other mode
                colorKey = d.modelType;
            }
            //console.log("COLOR KEY", colorKey, currentColorMapping[colorKey])
            return currentColorMapping[colorKey] || labelColor;
        });
        // .attr("opacity", 1); // Fade in/stay visible (collision might hide later)
        // --- Collision Detection (Applied after transitions conceptually) ---
        if (!labelCollisionDetection) {
            // If collision detection is disabled, ensure all are visible after transition
            // labelsUpdate.attr("opacity", 1); // Already set above
            return; // No need for further collision logic
        }
        // Run collision detection after the main position transition *ends*
        labelsUpdate.on("end.collision", () => {
            // Get all label elements *after* transition that are part of the current join
            const finalLabelElements = selection.selectAll(".point-label")
                .filter(d => labelData.some(ld => idValue(ld) === idValue(d))) // Ensure we only check currently relevant labels
                .nodes();
            if (finalLabelElements.length === 0)
                return; // No labels to check
            // Create array to track which labels to keep visible
            const labelsToKeep = new Set();
            // Only need point positions for the *visible* labels for collision checks
            const pointPositions = labelData.map(d => ({
                id: idValue(d),
                x: xScale(xValue(d)),
                y: yScale(yValue(d))
            }));
            // Sort labels (e.g., left to right) for consistent resolution
            const sortedFinalLabels = finalLabelElements
                .map(el => {
                try {
                    // Ensure element exists and has getBBox method
                    if (!el || typeof el.getBBox !== 'function') {
                        console.warn("Invalid element for BBox:", el);
                        return null;
                    }
                    const bbox = el.getBBox();
                    // Basic check for valid BBox dimensions
                    if (bbox.width <= 0 || bbox.height <= 0) {
                        console.warn("Invalid BBox dimensions for label:", el, bbox);
                        // return null; // Treat as problematic if needed
                    }
                    return {
                        element: el,
                        bbox: bbox, // Get final BBox
                        id: el.getAttribute("data-id"),
                        x: parseFloat(el.getAttribute("x")) // Use final 'x' attribute
                    };
                }
                catch (e) {
                    console.warn("Could not get BBox for label:", el, e);
                    return null; // Handle cases where BBox fails (e.g., element removed unexpectedly)
                }
            })
                .filter(l => l !== null && l.id) // Filter out problematic labels or those missing id
                .sort((a, b) => a.x - b.x);
            // Process labels for collision
            for (const label of sortedFinalLabels) {
                // Skip if label has no valid bbox
                if (!label.bbox || label.bbox.width <= 0 || label.bbox.height <= 0)
                    continue;
                let hasCollision = false;
                const labelBounds = {
                    left: label.bbox.x - 2,
                    right: label.bbox.x + label.bbox.width + 2,
                    top: label.bbox.y - 2,
                    bottom: label.bbox.y + label.bbox.height + 2
                };
                // Check collision with points *within the visible set*
                for (const point of pointPositions) {
                    if (point.id === label.id)
                        continue; // Don't collide with own point
                    if (point.x >= labelBounds.left && point.x <= labelBounds.right &&
                        point.y >= labelBounds.top && point.y <= labelBounds.bottom) {
                        hasCollision = true;
                        break;
                    }
                }
                // Check collision with already kept labels
                if (!hasCollision) {
                    for (const keptLabelId of labelsToKeep) {
                        const keptLabel = sortedFinalLabels.find(l => l.id === keptLabelId);
                        if (!keptLabel || !keptLabel.bbox || keptLabel.bbox.width <= 0 || keptLabel.bbox.height <= 0)
                            continue; // Skip invalid kept labels
                        const keptBounds = {
                            left: keptLabel.bbox.x - 2,
                            right: keptLabel.bbox.x + keptLabel.bbox.width + 2,
                            top: keptLabel.bbox.y - 2,
                            bottom: keptLabel.bbox.y + keptLabel.bbox.height + 2
                        };
                        // Simple Axis-Aligned Bounding Box (AABB) collision check
                        if (!(labelBounds.right < keptBounds.left || labelBounds.left > keptBounds.right ||
                            labelBounds.bottom < keptBounds.top || labelBounds.top > keptBounds.bottom)) {
                            hasCollision = true;
                            break;
                        }
                    }
                }
                if (!hasCollision) {
                    labelsToKeep.add(label.id);
                }
            }
            // The emphasized point's label is always shown, regardless of collisions.
            if (highlightId != null) {
                labelsToKeep.add(highlightId);
            }
            // Apply final visibility based on collision detection (no transition here, just set final state)
            selection.selectAll(".point-label")
                .filter(function () {
                const currentId = d3.select(this).attr("data-id");
                return labelsToKeep.has(currentId);
            })
                // .transition().duration(duration / 4) // Optional: Short fade in for kept labels
                // Kept labels are visible, but dimmed when not part of the subject.
                // Collision still owns which labels show (hidden ones stay at 0 below).
                .attr("opacity", function () {
                const currentId = d3.select(this).attr("data-id");
                return isSubjectId(currentId) ? 1 : dimOpacity;
            });
            selection.selectAll(".point-label")
                .filter(function () {
                const currentId = d3.select(this).attr("data-id");
                return !labelsToKeep.has(currentId);
            })
                // .transition().duration(duration / 4) // Optional: Short fade out for removed labels
                .attr("opacity", 0)
                .style("pointer-events", "none"); // Disable events on hidden labels
        });
        // --- Previous Collision Logic Removed ---
        // The complex sorting and bounding box checks are now inside the transition's "end" callback.
    }
    /**
     * Draws the scatterplot points (circles/triangles) with highlighting.
     * @param {d3.Selection} selection - The group element for points.
     * @param {Array} data - The *full* dataset.
     * @param {d3.Scale} xScale - The X scale.
     * @param {d3.Scale} yScale - The Y scale.
     * @param {number} [duration=750] - Transition duration.
     * @param {Set|null} highlightSet - Set of IDs for globally highlighted points.
     */
    function drawPoints(selection, data, xScale, yScale, duration = 750, highlightSet = null) {
        // Filter data to only include highlighted points when there's a highlight set
        const filteredData = highlightSet ? data.filter(d => highlightSet.has(idValue(d))) : data;
        const points = selection.selectAll(".point")
            .data(filteredData, d => idValue(d));
        points.exit()
            .transition("point-exit").duration(duration / 2)
            .attr("opacity", 0)
            .remove();
        const pointsEnter = points.enter().append("path")
            .attr("class", d => {
            return `point point-${versionValue(d)} provider-${providerValue(d).replace(/\s+/g, '-').toLowerCase()}`;
        })
            .attr("pointer-events", "none")
            .attr("data-id", d => idValue(d)) // Add data-id here
            .attr("d", d => pointSymbol(d, basePointSize))
            .attr("transform", d => `translate(${xScale(xValue(d))}, ${yScale(yValue(d))})`)
            .attr("opacity", 0);
        // Keep the emphasized point drawn on top of the others.
        points.merge(pointsEnter)
            .filter(d => highlightId != null && idValue(d) === highlightId)
            .raise();
        points.merge(pointsEnter)
            .transition("point-update").duration(duration)
            .attr("transform", d => `translate(${xScale(xValue(d))}, ${yScale(yValue(d))})`)
            .attr("opacity", d => subjectOpacity(d)) // visible, dimmed when not the subject
            .attr("fill", d => {
            let colorKey;
            if (currentColorMode === "provider") {
                colorKey = providerValue(d);
            }
            else if (currentColorMode === "version") {
                colorKey = versionValue(d);
            }
            else { // type or any other mode
                colorKey = d.modelType;
            }
            return currentColorMapping[colorKey] || defaultColor;
        })
            .attr("stroke", d => {
            if (hoverTarget && idValue(d) === hoverTarget)
                return hoverStrokeColor;
            if (highlightId != null && idValue(d) === highlightId)
                return highlightStrokeColor;
            return "none";
        })
            .attr("stroke-width", d => {
            if (hoverTarget && idValue(d) === hoverTarget)
                return hoverStrokeWidth;
            if (highlightId != null && idValue(d) === highlightId)
                return highlightStrokeWidth;
            return 0;
        })
            .attr("d", d => {
            const isHighlighted = highlightId != null && idValue(d) === highlightId;
            const isHovered = hoverTarget && idValue(d) === hoverTarget;
            let size = basePointSize;
            if (isHighlighted)
                size = highlightPointSize;
            else if (isHovered)
                size = basePointSize * 1.5;
            return pointSymbol(d, size);
        });
    }
    /**
     * Draws curved lines connecting points within the same model group with transitions and highlighting.
     * @param {d3.Selection} selection - The group element for lines.
     * @param {Array} data - The *full* dataset.
     * @param {d3.Scale} xScale - The X scale.
     * @param {d3.Scale} yScale - The Y scale.
     * @param {number} [duration=750] - Transition duration.
     * @param {Set|null} highlightSet - Set of IDs for globally highlighted points.
     */
    function drawModelGroups(selection, data, xScale, yScale, duration = 750, highlightSet = null) {
        const lineData = []; // Array to hold data for each line segment
        // Helper to check if a line should be fully visible in highlight mode
        const shouldShowLine = (points, hSet) => {
            if (!hSet)
                return true; // No highlight, show all
            return points.every(p => hSet.has(idValue(p)));
        };
        // If model groups config is empty, don't draw any lines
        if (Object.keys(modelGroups).length > 0) {
            // Process each data source in modelGroups
            Object.keys(modelGroups).forEach(groupDataSource => {
                // groupDataSource is the datasetId
                // Get model groups to connect for this data source
                const groupsToConnect = modelGroups[groupDataSource];
                if (!groupsToConnect || groupsToConnect.length === 0)
                    return;
                // Process each specific model group name (e.g., "GPT-4")
                groupsToConnect.forEach(modelGroupName => {
                    // Find the points using the full dataset
                    const versionPoints = data.filter(d => modelGroupValue(d) === modelGroupName && versionValue(d) === groupDataSource)
                        .sort((a, b) => compareModelReasoningLevels(a, b, xValue));
                    // Check if we have enough points for lines in each version
                    if (versionPoints.length >= 2) {
                        let colorKey;
                        if (currentColorMode === "provider") {
                            colorKey = providerValue(versionPoints[0]);
                        }
                        else if (currentColorMode === "version") {
                            colorKey = versionValue(versionPoints[0]);
                        }
                        else { // type or any other mode
                            colorKey = versionPoints[0].modelType;
                        }
                        lineData.push({
                            id: `${modelGroupName}-${groupDataSource}`,
                            points: versionPoints,
                            color: currentColorMapping[colorKey] || defaultColor,
                            groupName: modelGroupName,
                            version: groupDataSource
                        });
                    }
                });
            });
        }
        // Line generator function
        const line = d3.line()
            .defined(d => !isNoneReasoningLevel(d))
            .x(d => xScale(xValue(d)))
            .y(d => yScale(yValue(d)))
            .curve(d3.curveCardinal.tension(0.5));
        //console.log("LINE DATA", lineData)
        // Data Join for lines
        const lines = selection.selectAll(".model-group-line")
            .data(lineData, d => d.id); // Use the generated ID
        // Exit: Transition out old lines (if groups/versions change)
        lines.exit()
            .transition("line-exit").duration(duration / 2)
            .attr("opacity", 0);
        // .remove();
        // Enter: Add new lines, starting transparent
        const linesEnter = lines.enter().append("path")
            .attr("class", d => `model-group-line`)
            .attr("pointer-events", "none")
            .attr("d", d => line(d.points)) // Initial 'd' based on points
            .attr("fill", "none")
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "5,3")
            .attr("opacity", 0); // Start transparent
        // Update + Enter: Transition shape and opacity/color based on highlight
        lines.merge(linesEnter)
            .attr("data-group", d => d.groupName) // Store group name for potential hover interactions
            .attr("data-version", d => d.version)
            .transition("line-update").duration(duration)
            .attr("opacity", d => {
            // Hidden by an active selection highlight → use the legacy faint dim.
            if (!shouldShowLine(d.points, highlightSet))
                return highlightDimOpacity * 0.5;
            // Otherwise a line is full strength only when every point is a subject;
            // mixed/non-subject lines fade with the shared dimOpacity.
            const allSubject = d.points.every(p => isSubject(p));
            return allSubject ? 0.8 : 0.8 * dimOpacity;
        })
            .attr("stroke", d => shouldShowLine(d.points, highlightSet) ? d.color : highlightDimColor) // Update color
            .attr("d", d => line(d.points)); // Transition the path shape
    }
    /**
     * Sets up the quadtree and hover listeners.
     * @param {d3.Selection} svgSelection - The main SVG selection.
     * @param {Array} data - The *full* dataset.
     * @param {d3.Scale} xScale - The X scale.
     * @param {d3.Scale} yScale - The Y scale.
     * @param {number} innerWidth - Chart inner width.
     * @param {number} innerHeight - Chart inner height.
     */
    function setupQuadtreeAndHover(svgSelection, data, xScale, yScale, innerWidth, innerHeight, highlightSet = null) {
        // 1. Create Quadtree with only visible points
        const visibleData = highlightSet ? data.filter(d => highlightSet.has(idValue(d))) : data;
        quadtree = d3.quadtree()
            .x(d => xScale(xValue(d)))
            .y(d => yScale(yValue(d)))
            .extent([[0, 0], [innerWidth, innerHeight]]) // Use chart inner bounds
            .addAll(visibleData); // Add only visible data points
        // 2. Add Listener to SVG background or a dedicated hover rect
        // Using the background rect already present
        const hoverRect = g.select(".chart-background");
        // Or add a dedicated one:
        // const hoverRect = g.selectAll(".hover-capture-rect").data([null])
        //     .join("rect")
        //     .attr("class", "hover-capture-rect")
        //     .attr("width", innerWidth)
        //     .attr("height", innerHeight)
        //     .attr("fill", "none") // Make it invisible
        //     .style("pointer-events", "all"); // Ensure it captures events
        hoverRect
            .on("mousemove.tooltip", (event) => {
            const [xm, ym] = d3.pointer(event, g.node()); // Get mouse coords relative to 'g'
            // Find nearest point using quadtree
            const closest = quadtree.find(xm, ym, hoverSearchRadius); // Search within radius
            const closestId = closest ? idValue(closest) : null;
            // If the closest point changed, update hover state
            if (hoverTarget !== closestId) {
                const previousTargetId = hoverTarget;
                hoverTarget = closestId; // Update the global hover target
                // Update the previously hovered point (remove hover style)
                if (previousTargetId) {
                    updatePointHoverStyle(previousTargetId, false);
                }
                // Update the newly hovered point (add hover style)
                if (hoverTarget) {
                    updatePointHoverStyle(hoverTarget, true);
                    showTooltip(event, closest);
                }
                else {
                    hideTooltip();
                }
            }
            else if (hoverTarget) {
                // If hovering over the same point, just update tooltip position
                showTooltip(event, closest);
            }
            // Pointer cursor for points whose model group has a results
            // page (resultsUrl is populated per evaluation).
            hoverRect.style("cursor", closest && closest.resultsUrl ? "pointer" : null);
        })
            .on("mouseout.tooltip", () => {
            // If mouse leaves the chart area, clear hover state
            if (hoverTarget) {
                const previousTargetId = hoverTarget;
                hoverTarget = null;
                updatePointHoverStyle(previousTargetId, false);
                hideTooltip();
            }
            hoverRect.style("cursor", null);
        })
            .on("click.results", (event) => {
            const [xm, ym] = d3.pointer(event, g.node());
            const closest = quadtree.find(xm, ym, hoverSearchRadius);
            // Link to the model group's results page when one exists;
            // otherwise the point is not clickable.
            if (closest && closest.resultsUrl) {
                window.location.href = closest.resultsUrl;
            }
        });
    }
    /**
     * Updates the visual style of a point based on hover state.
     * @param {string} pointId - The ID of the point to update.
     * @param {boolean} isHovered - True if the point is being hovered.
     */
    function updatePointHoverStyle(pointId, isHovered) {
        const isHighlighted = highlightId != null && pointId === highlightId;
        pointsGroup.selectAll(`.point[data-id="${pointId}"]`)
            .transition("point-hover-style").duration(50) // Short transition
            .attr("stroke", isHovered ? hoverStrokeColor : (isHighlighted ? highlightStrokeColor : "none"))
            .attr("stroke-width", isHovered ? hoverStrokeWidth : (isHighlighted ? highlightStrokeWidth : 0))
            .attr("d", function (d) {
            // The emphasized point stays large; never shrink it on hover-out.
            if (isHighlighted) {
                return pointSymbol(d, highlightPointSize);
            }
            if (isHovered) {
                return pointSymbol(d, basePointSize * 1.5);
            }
            return pointSymbol(d, basePointSize);
        });
        // Also potentially highlight label?
        if (showLabels) {
            labelsGroup.selectAll(`.point-label[data-id="${pointId}"]`)
                .transition("label-hover-style").duration(50)
                .attr("font-weight", (isHovered || isHighlighted) ? "bold" : "normal");
        }
    }
    /** Shows and positions the tooltip. */
    function showTooltip(event, d) {
        tooltipDiv.transition().duration(100).style("opacity", 1);
        const isGloballyHighlighted = !currentHighlightSet || currentHighlightSet.has(idValue(d));
        const scoreDisplay = (yValue(d)).toFixed(1) + '%';
        let datasetDisplay = 'N/A';
        if (d.datasetId) {
            datasetDisplay = d.datasetDisplayName;
        }
        let xDetail;
        if (xScaleType === "time") {
            const releaseDate = xValue(d);
            const releaseDateDisplay = releaseDate instanceof Date && !Number.isNaN(releaseDate.valueOf())
                ? d3.utcFormat("%b %-d, %Y")(releaseDate)
                : "N/A";
            xDetail = `Release date: ${releaseDateDisplay}`;
        }
        else {
            let costDisplay = 'N/A';
            const costVal = xValue(d);
            if (costVal !== null && costVal !== undefined) {
                if (costVal < 0.01)
                    costDisplay = "$" + costVal.toFixed(4); // Exp for very small
                else if (costVal < 1)
                    costDisplay = "$" + costVal.toFixed(3);
                else if (costVal < 1000)
                    costDisplay = "$" + costVal.toFixed(2);
                else
                    costDisplay = "$" + (costVal / 1000).toFixed(1) + "K";
            }
            const costLabel = d.cost !== undefined && d.costPerTask === undefined ? 'Cost' : 'Cost/Task';
            xDetail = `${costLabel}: ${costDisplay}`;
        }
        tooltipDiv.html(`
            ${labelValue(d)}<br/>
            ${datasetDisplay} Score: ${scoreDisplay}<br/>
            ${xDetail}<br/>
            Author: ${providerValue(d)}<br/>
            Type: ${d.modelType}
            ${!isGloballyHighlighted ? '<br/><i>(Filtered out)</i>' : ''}
        `)
            // Position tooltip relative to the page, not the SVG element
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 10) + "px");
    }
    /** Hides the tooltip. */
    function hideTooltip() {
        tooltipDiv.transition().duration(200).style("opacity", 0);
    }
    /**
     * Highlights a subset of data points, updating axes and dimming others.
     * @param {Array|null} highlightData - An array of data objects to highlight, or null/empty to reset.
     * @param {number} [duration=750] - Transition duration.
     */
    chart.highlightPoints = function (highlightData, duration = 750) {
        if (!initialized)
            return;
        // Interrupt all running transitions to prevent overlap when switching quickly
        g.selectAll("*").interrupt();
        pointsGroup.selectAll(".point").interrupt();
        labelsGroup.selectAll(".point-label").interrupt();
        linesGroup.selectAll("*").interrupt();
        annotationsGroup.selectAll("*").interrupt();
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        let targetXDomain, targetYDomain;
        let newHighlightSet = null;
        // Check for reset condition
        if (!highlightData || highlightData.length === 0) {
            targetXDomain = originalXDomain;
            targetYDomain = originalYDomain;
            newHighlightSet = null;
        }
        else {
            newHighlightSet = new Set(highlightData.map(idValue));
            // Calculate bounds from highlightData
            let [minX, maxX] = d3.extent(highlightData, xValue);
            let [minY, maxY] = d3.extent(highlightData, yValue);
            // Calculate padded bounds in a scale-appropriate way. X zooming is
            // currently disabled below, but keeping these values valid makes
            // it safe to re-enable later for either scale type.
            const xRange = maxX - minX;
            const yRange = maxY - minY;
            if (xScaleType === "time") {
                const xPadding = Math.max(24 * 60 * 60 * 1000, xRange * 0.15);
                minX = Math.max(originalXDomain[0], +minX - xPadding);
                maxX = Math.min(originalXDomain[1], +maxX + xPadding);
            }
            else {
                // For log scale, adjust padding multiplicatively.
                minX = Math.max(originalXDomain[0], minX / 1.15);
                maxX = Math.min(originalXDomain[1], maxX * 1.15);
            }
            //console.log("minX", minX);
            //console.log("maxX", maxX);
            minY = Math.max(0, minY - yRange * 0.15); // Ensure minY doesn't go below 0
            maxY = Math.min(originalYDomain[1], maxY + yRange * 0.15); // Don't exceed original max
            //console.log("minY", minY);
            //console.log("maxY", maxY);
            if (xScaleType === "log") {
                // Prevent zero or negative range for log scale.
                if (minX <= 0)
                    minX = originalXDomain[0] * 0.1;
                if (maxX <= minX)
                    maxX = minX * 10;
            }
            else if (maxX <= minX) {
                maxX = minX + 24 * 60 * 60 * 1000;
            }
            // Ensure Y range is valid
            if (maxY <= minY) {
                maxY = minY + (originalYDomain[1] - originalYDomain[0]) * 0.1; // Add small default range if needed
            }
            // TODO: Do we want to update the X domain? Uncomment to do it, but it seems dissorienting.
            // targetXDomain = [minX, maxX];
            // targetYDomain = [minY, maxY];
            // lock the minY to 0
            // Use static Y domain when yAxisMax is explicitly set small (e.g. V3 at 10%)
            targetYDomain = originalYDomain;
        }
        // Update the global highlight set *before* drawing
        currentHighlightSet = newHighlightSet;
        // Update scales
        // x.domain(targetXDomain).nice();
        y.domain(targetYDomain).nice();
        // console.log("targetXDomain", targetXDomain);
        //console.log("targetYDomain???", targetYDomain);
        // Update Axes with transition
        g.select(".x-axis")
            .transition("x-axis-highlight").duration(duration)
            .call(xAxis
            .scale(x)
            .tickValues(getXAxisTickValues(x, innerWidth))
            .tickFormat(formatXAxisTick))
            .call(g => g.selectAll("text").attr("fill", "#9a9a9a"))
            .call(g => g.select(".domain").attr("stroke", "#555"));
        g.select(".y-axis")
            .transition("y-axis-highlight").duration(duration)
            .call(yAxis.scale(y)) // Update scale
            .call(g => g.selectAll("text").attr("fill", "#9a9a9a"))
            .call(g => g.select(".domain").attr("stroke", "#555"));
        // Redraw Grid Lines (instantly)
        drawGridLines(gridGroup, x, y, innerWidth, innerHeight);
        // Redraw Annotations, passing the new currentHighlightSet
        drawMaxAnnotation(annotationsGroup, fullData, x, y, innerWidth, currentHighlightSet, duration);
        // Redraw Points with transition, using the new highlight set
        drawPoints(pointsGroup, fullData, x, y, duration, currentHighlightSet);
        // Redraw Labels with transition, using the new highlight set
        if (showLabels) {
            drawLabels(labelsGroup, fullData, x, y, innerWidth, innerHeight, duration, currentHighlightSet);
        }
        else {
            labelsGroup.selectAll(".point-label")
                .transition("label-hide-highlight").duration(duration / 2)
                .attr("opacity", 0)
                .remove();
        }
        // Redraw Model Group Lines with transition, using the new highlight set
        drawModelGroups(linesGroup, fullData, x, y, duration, currentHighlightSet);
        // --- NEW: Update Quadtree ---
        // Rebuild quadtree because scales changed
        setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, currentHighlightSet);
        return chart;
    };
    /**
     * Draws a custom rectangle and text annotation based on config, using enter/update/exit.
     * @param {d3.Selection} selection - The group element for annotations.
     * @param {d3.Scale} xScale - The X scale.
     * @param {d3.Scale} yScale - The Y scale.
     * @param {number} [duration=0] - Transition duration.
     */
    // (Removed: custom rectangle + text annotation used for the green area)
    // --- NEW: Getter for Color Mapping ---
    chart.getColorMapping = function () {
        return { ...currentColorMapping };
    };
    chart.setColorMapping = function (colorMap, colorMode) {
        //console.log("SET COLOR MAPPING", colorMap, colorMode);
        currentColorMapping = colorMap || {};
        currentColorMode = colorMode || "provider";
        // If the chart is initialized, redraw with new colors
        if (initialized) {
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            const duration = 750;
            // Redraw all elements that need color updates
            drawPoints(pointsGroup, fullData, x, y, duration, currentHighlightSet);
            drawModelGroups(linesGroup, fullData, x, y, duration, currentHighlightSet);
            if (showLabels) {
                drawLabels(labelsGroup, fullData, x, y, innerWidth, innerHeight, duration, currentHighlightSet);
            }
        }
        return this;
    };
    // Emphasize a single point by its id (idValue). Pass null to clear.
    chart.highlightId = function (_) {
        if (!arguments.length)
            return highlightId;
        highlightId = _;
        if (initialized) {
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            const duration = 400;
            drawPoints(pointsGroup, fullData, x, y, duration, currentHighlightSet);
            if (showLabels) {
                drawLabels(labelsGroup, fullData, x, y, innerWidth, innerHeight, duration, currentHighlightSet);
            }
        }
        return chart;
    };
    // Redraw the dynamic layers (points, lines, labels) — used after changing
    // the subject set or dim opacity, which affect all three.
    function redrawSubjectLayers(duration = 400) {
        if (!initialized)
            return;
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        drawPoints(pointsGroup, fullData, x, y, duration, currentHighlightSet);
        drawModelGroups(linesGroup, fullData, x, y, duration, currentHighlightSet);
        if (showLabels) {
            drawLabels(labelsGroup, fullData, x, y, innerWidth, innerHeight, duration, currentHighlightSet);
        }
    }
    // Set the subject point id(s) — the points kept at full strength while the
    // rest of the chart (their dots, lines, and labels) fade to dimOpacity.
    // Accepts a Set, an array of ids, or null/[] to clear.
    chart.subjectIds = function (_) {
        if (!arguments.length)
            return subjectIds;
        subjectIds = _ ? (_ instanceof Set ? _ : new Set(_)) : null;
        redrawSubjectLayers();
        return chart;
    };
    // Opacity (0..1) applied to everything that is not a subject. 1 = no dimming.
    chart.dimOpacity = function (_) {
        if (!arguments.length)
            return dimOpacity;
        dimOpacity = +_;
        redrawSubjectLayers();
        return chart;
    };
    // --- Configuration Getter/Setters ---
    // Allow users to configure chart parameters after initialization
    chart.width = function (_) {
        return arguments.length ? (width = +_, chart) : width;
    };
    chart.height = function (_) {
        return arguments.length ? (height = +_, chart) : height;
    };
    chart.responsive = function (_) {
        return arguments.length ? (responsive = !!_, chart) : responsive;
    };
    chart.margin = function (_) {
        if (!arguments.length)
            return margin;
        margin.top = typeof _.top !== 'undefined' ? +_.top : margin.top;
        margin.right = typeof _.right !== 'undefined' ? +_.right : margin.right;
        margin.bottom = typeof _.bottom !== 'undefined' ? +_.bottom : margin.bottom;
        margin.left = typeof _.left !== 'undefined' ? +_.left : margin.left;
        return chart;
    };
    // Update config setters to potentially store original values if needed elsewhere
    chart.xAxisMin = function (_) {
        if (!arguments.length)
            return xAxisMin;
        xAxisMin = +_;
        originalXDomain[0] = xAxisMin; // Update original domain store
        if (initialized)
            x.domain(originalXDomain).nice(); // Update scale if initialized
        if (initialized) {
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, currentHighlightSet); // Update quadtree
        }
        return chart;
    };
    chart.xAxisMinLabel = function (_) {
        return arguments.length ? (xAxisMinLabel = _, chart) : xAxisMinLabel;
    };
    chart.xAxisMax = function (_) {
        if (!arguments.length)
            return xAxisMax;
        xAxisMax = +_;
        originalXDomain[1] = xAxisMax; // Update original domain store
        if (initialized)
            x.domain(originalXDomain).nice(); // Update scale if initialized
        if (initialized) {
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, currentHighlightSet); // Update quadtree
        }
        return chart;
    };
    // Note: yAxisMin/Max are controlled by updateYAxis or highlightPoints after initial setup
    chart.yAxisMin = function (_) {
        if (!arguments.length)
            return yAxisMin;
        yAxisMin = +_;
        originalYDomain[0] = yAxisMin; // Update original domain store
        if (initialized && !currentHighlightSet) {
            y.domain(originalYDomain).nice();
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, currentHighlightSet); // Update quadtree
        }
        return chart;
    };
    chart.yAxisMax = function (_) {
        if (!arguments.length)
            return yAxisMax;
        yAxisMax = +_;
        originalYDomain[1] = yAxisMax; // Update original domain store
        if (initialized && !currentHighlightSet) {
            y.domain(originalYDomain).nice();
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            setupQuadtreeAndHover(svg, fullData, x, y, innerWidth, innerHeight, currentHighlightSet); // Update quadtree
        }
        return chart;
    };
    chart.xAxisLabel = function (_) {
        return arguments.length ? (xAxisLabel = _, chart) : xAxisLabel;
    };
    chart.xScaleType = function (_) {
        if (!arguments.length)
            return xScaleType;
        xScaleType = _ === "time" ? "time" : "log";
        return chart;
    };
    chart.yAxisLabel = function (_) {
        return arguments.length ? (yAxisLabel = _, chart) : yAxisLabel;
    };
    chart.xValue = function (_) {
        return arguments.length ? (xValue = typeof _ === 'function' ? _ : () => _, chart) : xValue;
    };
    chart.yValue = function (_) {
        return arguments.length ? (yValue = typeof _ === 'function' ? _ : () => _, chart) : yValue;
    };
    chart.idValue = function (_) {
        return arguments.length ? (idValue = typeof _ === 'function' ? _ : () => _, chart) : idValue;
    };
    chart.versionValue = function (_) {
        return arguments.length ? (versionValue = typeof _ === 'function' ? _ : () => _, chart) : versionValue;
    };
    chart.providerValue = function (_) {
        return arguments.length ? (providerValue = typeof _ === 'function' ? _ : () => _, chart) : providerValue;
    };
    chart.modelGroupValue = function (_) {
        return arguments.length ? (modelGroupValue = typeof _ === 'function' ? _ : () => _, chart) : modelGroupValue;
    };
    // Removed dataSourceValue as it wasn't used
    // chart.dataSourceValue = function(_) {
    //   return arguments.length ? (dataSourceValue = typeof _ === 'function' ? _ : () => _, chart) : dataSourceValue;
    // };
    // --- Configuration Getter/Setters for Labels ---
    chart.showLabels = function (_) {
        if (!arguments.length)
            return showLabels;
        const previousState = showLabels;
        showLabels = !!_; // Ensure boolean
        if (initialized && previousState !== showLabels) { // Only update if state changes
            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;
            // const data = svg.datum() || []; // Use fullData
            const duration = 300; // Short transition for toggle
            if (showLabels) {
                // Draw labels with a short fade-in transition, respecting highlight
                drawLabels(labelsGroup, fullData, x, y, innerWidth, currentHighlightSet);
            }
            else {
                // Fade out and remove labels
                labelsGroup.selectAll(".point-label")
                    .transition().duration(duration)
                    .attr("opacity", 0)
                    .remove();
            }
        }
        return chart;
    };
    chart.labelCollisionDetection = function (_) {
        return arguments.length ? (labelCollisionDetection = !!_, chart) : labelCollisionDetection;
    };
    chart.labelPadding = function (_) {
        return arguments.length ? (labelPadding = +_, chart) : labelPadding;
    };
    chart.labelFontSize = function (_) {
        return arguments.length ? (labelFontSize = _, chart) : labelFontSize;
    };
    chart.labelColor = function (_) {
        return arguments.length ? (labelColor = _, chart) : labelColor;
    };
    return chart;
}
