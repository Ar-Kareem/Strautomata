"use strict";
// @ts-nocheck
// Declare scatterplot in a broader scope
let scatterplot;
// --- Setup Filter State Management ---
const filterState = {
    version: null, // Will be set to versions[0] after data loads
    providers: [],
    modelTypes: [],
    models: [],
    xAxisMode: "cost",
    colorMode: "provider" // Default to color by provider
};
// Add color mapping for versions and types
const colorMappings = {
    provider: {},
    version: {},
    type: {
        "Base LLM": "#1e93ffff",
        "CoT": "#4ecc30ff",
        "CoT + Synthesis": "#f93c32ff",
        "Custom": "#ff841cff"
    }
};
async function runLeaderboard() {
    const chartRoot = document.getElementById("reusable-scatterplot-container");
    if (!chartRoot)
        return;
    if (chartRoot.dataset.leaderboardInitialized === "true")
        return;
    chartRoot.dataset.leaderboardInitialized = "true";
    const startTime = performance.now();
    // Map pill keys and version ids to major-version file names.
    const majorVersionByIndex = ["v1", "v2", "v3"];
    // Phase 2 (filters + table) kicked off in parallel with chart load.
    // The chart only waits on the small version file below.
    const fullDataPromise = loadAllData();
    // Set initial version state to ARC-AGI-3 BEFORE creating chart
    filterState.version = versions[2];
    // Phase 1: fetch only the current version's pre-joined rows. This is
    // the critical path for first paint.
    let currentVersionRows = await loadVersionData("v3");
    // Seed color mappings from the rows we have right now so the initial
    // render is colored correctly even before providers.json arrives.
    currentVersionRows.forEach(row => {
        if (row.providerDisplayName && !(row.providerDisplayName in colorMappings.provider)) {
            colorMappings.provider[row.providerDisplayName] = row.providerColor;
        }
    });
    colorMappings.provider["Other"] = "#ffdc00ff";
    colorMappings.version[versions[0]] = "#1e93ffff";
    colorMappings.version[versions[1]] = "#f93c32ff";
    colorMappings.version[versions[2]] = "#ffdc00ff";
    // Use compact chart geometry on mobile so the plot keeps enough usable
    // width instead of spending most of it on desktop margins.
    const getChartLayout = () => {
        const container = document.getElementById("chart-wrapper");
        const isMobile = window.innerWidth <= 768;
        const containerWidth = container ? container.clientWidth : 978;
        return {
            width: isMobile
                ? containerWidth
                : Math.min(978, Math.max(600, containerWidth - 48)),
            height: isMobile ? 360 : 500,
            margin: isMobile
                ? { top: 14, right: 20, bottom: 44, left: 50 }
                : { top: 20, right: 65, bottom: 40, left: 105 }
        };
    };
    const initialChartLayout = getChartLayout();
    // --- Instantiate the reusable chart ---
    scatterplot = reusableScatterplot()
        .width(initialChartLayout.width)
        .height(initialChartLayout.height)
        .margin(initialChartLayout.margin)
        .yAxisMin(0)
        .yAxisMax(100)
        .setColorMapping(colorMappings[filterState.colorMode], filterState.colorMode);
    const releaseDateValue = row => {
        if (!row.modelReleaseDate)
            return null;
        const date = new Date(row.modelReleaseDate);
        return Number.isNaN(date.valueOf()) ? null : date;
    };
    const releaseDateDomainMin = Date.UTC(2019, 10, 1);
    function getRenderableRows() {
        return currentVersionRows.filter(row => {
            if (!row.display)
                return false;
            return filterState.xAxisMode !== "release-date" || releaseDateValue(row);
        });
    }
    function configureXAxis(rows) {
        if (filterState.xAxisMode === "release-date") {
            const releaseDates = rows.map(releaseDateValue).filter(Boolean);
            const [minDate, maxDate] = d3.extent(releaseDates);
            const day = 24 * 60 * 60 * 1000;
            const range = minDate && maxDate ? +maxDate - +minDate : 0;
            const padding = Math.max(14 * day, range * 0.04);
            const domainMax = maxDate ? +maxDate + padding : Date.now() + 30 * day;
            scatterplot
                .xValue(releaseDateValue)
                .xScaleType("time")
                .xAxisMin(releaseDateDomainMin)
                .xAxisMinLabel(null)
                .xAxisMax(domainMax)
                .xAxisLabel("MODEL RELEASE DATE");
            return;
        }
        const isV3 = filterState.version === versions[2];
        scatterplot
            .xValue(isV3 ? (d => d.cost) : (d => d.costPerTask))
            .xScaleType("log")
            .xAxisMin(isV3 ? 1 : 0.001)
            .xAxisMinLabel(isV3 ? null : "$0.001")
            .xAxisMax(isV3 ? 100000 : 100)
            .xAxisLabel(isV3 ? "COST ($)" : "COST PER TASK ($)");
    }
    // Function to apply filters based on current state.
    // Works off currentVersionRows + denormalized fields — no global lookups.
    function applyFilters(animationDuration = 750) {
        let filteredPoints = getRenderableRows();
        // Exclude Human rows (kept from original behavior)
        filteredPoints = filteredPoints.filter(d => d.providerDisplayName !== "Human");
        if (filterState.providers.length > 0) {
            filteredPoints = filteredPoints.filter(d => filterState.providers.includes(d.providerDisplayName));
        }
        if (filterState.modelTypes.length > 0) {
            filteredPoints = filteredPoints.filter(d => filterState.modelTypes.includes(d.modelType));
        }
        if (filterState.models.length > 0) {
            filteredPoints = filteredPoints.filter(d => filterState.models.includes(d.modelId));
        }
        scatterplot.highlightPoints(filteredPoints, animationDuration);
    }
    function renderCurrentVersion(animationDuration = 750) {
        const renderableRows = getRenderableRows();
        configureXAxis(renderableRows);
        d3.select("#reusable-scatterplot-container")
            .datum(renderableRows)
            .call(scatterplot);
        applyFilters(animationDuration);
    }
    // Render the default cost view immediately after chart creation.
    renderCurrentVersion(0);
    // Add download chart functionality
    document.getElementById("download-chart").addEventListener("click", async () => {
        if (window.posthog && typeof window.posthog.capture === "function") {
            posthog.capture("download_leaderboard_chart", { location: window.location.pathname });
        }
        const node = document.getElementById("chart-wrapper");
        // Convert SVG images to data URLs for html2canvas compatibility
        const svgImages = node.querySelectorAll("image[href]");
        const originalHrefs = new Map();
        for (const img of svgImages) {
            const href = img.getAttribute("href");
            if (href && !href.startsWith("data:") && href.endsWith(".svg")) {
                originalHrefs.set(img, href);
                try {
                    const response = await fetch(href);
                    const svgText = await response.text();
                    const svgBlob = new Blob([svgText], { type: "image/svg+xml;charset=utf-8" });
                    const dataUrl = await new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(svgBlob);
                    });
                    img.setAttribute("href", dataUrl);
                }
                catch (e) {
                    console.warn("Failed to convert SVG to data URL:", e);
                }
            }
        }
        // Wait a moment for images to render
        await new Promise(resolve => setTimeout(resolve, 100));
        html2canvas(node, {
            backgroundColor: "#000",
            scale: 2,
            logging: false,
            useCORS: true
        }).then(canvas => {
            // Restore original hrefs
            originalHrefs.forEach((href, img) => {
                img.setAttribute("href", href);
            });
            const link = document.createElement("a");
            link.download = "arc-prize-leaderboard.png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        });
    });
    // --- Setup Pill Toggle for Version Selection ---
    const defaultFilterColor = "#ffdc00ff";
    // Initialize pill toggle
    const pillToggle = document.getElementById("prize-filter");
    const pillOptions = pillToggle.querySelectorAll(".pill-option");
    const leaderboardTitle = document.getElementById("leaderboard-title");
    // Set UI state to match the already-initialized filterState.version (ARC-AGI-3)
    const initialVersionKey = "arc-agi-3";
    pillToggle.setAttribute("data-active", initialVersionKey);
    pillOptions.forEach((opt, index) => {
        if (opt.getAttribute("data-version") === initialVersionKey) {
            opt.classList.add("active");
            pillToggle.style.setProperty("--pill-active-index", String(index));
        }
    });
    // Add click handlers to pill options with debounce to handle rapid switching
    let versionSwitchRAF = null;
    pillOptions.forEach((option, index) => {
        option.addEventListener("click", () => {
            const versionKey = option.getAttribute("data-version");
            // Update visual state immediately (pill slider animation)
            pillOptions.forEach(opt => opt.classList.remove("active"));
            option.classList.add("active");
            pillToggle.setAttribute("data-active", versionKey);
            pillToggle.style.setProperty("--pill-active-index", String(index));
            // Immediately clear all datapoints, labels, and lines from the chart
            const chartG = d3.select("#reusable-scatterplot-container svg g");
            chartG.selectAll(".point").interrupt().attr("opacity", 0);
            chartG.selectAll(".point-label").interrupt().attr("opacity", 0);
            chartG.selectAll(".model-group-line").interrupt().attr("opacity", 0);
            chartG.selectAll(".annotations-group *").interrupt().attr("opacity", 0);
            // Cancel any pending version switch so only the latest one runs
            if (versionSwitchRAF) {
                cancelAnimationFrame(versionSwitchRAF);
            }
            versionSwitchRAF = requestAnimationFrame(async () => {
                versionSwitchRAF = null;
                // Update version state and title.
                let targetMajor;
                if (versionKey === "arc-agi-1") {
                    filterState.version = versions[0];
                    targetMajor = "v1";
                    leaderboardTitle.textContent = "ARC-AGI-1 Leaderboard";
                }
                else if (versionKey === "arc-agi-2") {
                    filterState.version = versions[1];
                    targetMajor = "v2";
                    leaderboardTitle.textContent = "ARC-AGI-2 Leaderboard";
                }
                else {
                    filterState.version = versions[2];
                    targetMajor = "v3";
                    leaderboardTitle.textContent = "ARC-AGI-3 Leaderboard";
                }
                // Fetch the target version's rows (cached after first fetch).
                // Only the requested version's data is loaded — other versions stay idle.
                currentVersionRows = await loadVersionData(targetMajor);
                renderCurrentVersion();
            });
        });
    });
    // --- Setup X-axis Toggle ---
    const xAxisToggle = document.getElementById("x-axis-filter");
    const xAxisOptions = xAxisToggle.querySelectorAll(".pill-option");
    xAxisToggle.setAttribute("data-active", filterState.xAxisMode);
    xAxisOptions.forEach((option, index) => {
        const isActive = option.getAttribute("data-axis-mode") === filterState.xAxisMode;
        option.classList.toggle("active", isActive);
        option.setAttribute("aria-pressed", String(isActive));
        if (isActive) {
            xAxisToggle.style.setProperty("--pill-active-index", String(index));
        }
        option.addEventListener("click", () => {
            const axisMode = option.getAttribute("data-axis-mode");
            if (axisMode === filterState.xAxisMode)
                return;
            filterState.xAxisMode = axisMode;
            xAxisToggle.setAttribute("data-active", axisMode);
            xAxisToggle.style.setProperty("--pill-active-index", String(index));
            xAxisOptions.forEach(axisOption => {
                const optionIsActive = axisOption === option;
                axisOption.classList.toggle("active", optionIsActive);
                axisOption.setAttribute("aria-pressed", String(optionIsActive));
            });
            renderCurrentVersion();
        });
    });
    // Phase 2: wait for full raw data before building filter dropdowns and
    // the leaderboard table, upgrading the color mapping with the
    // authoritative provider list along the way.
    const tidiedData = await fullDataPromise;
    providers.forEach(provider => {
        colorMappings.provider[provider.displayName] = provider.color;
    });
    colorMappings.provider["Other"] = "#ffdc00ff";
    // Reapply the color mapping so points that already rendered pick up
    // the authoritative provider colors.
    scatterplot.setColorMapping(colorMappings[filterState.colorMode], filterState.colorMode);
    applyFilters(0);
    const appendSelectionCheckmark = (svg, swatchColor) => {
        const normalizedColor = swatchColor.trim().toLowerCase();
        const checkmarkColor = ["#fff", "#ffffff", "#ffffffff", "white"].includes(normalizedColor)
            ? "black"
            : "white";
        const checkmark = document.createElementNS("http://www.w3.org/2000/svg", "path");
        checkmark.setAttribute("class", "selection-checkmark");
        checkmark.setAttribute("d", "M5.5 10l3 3 6-6");
        checkmark.setAttribute("fill", "none");
        checkmark.setAttribute("stroke", checkmarkColor);
        checkmark.setAttribute("stroke-width", "2");
        checkmark.setAttribute("stroke-linecap", "round");
        checkmark.setAttribute("stroke-linejoin", "round");
        svg.appendChild(checkmark);
    };
    // --- Create the leaderboard table ---
    createLeaderboardTable("leaderboard-table");
    // --- Provider Multi-Select Dropdown ---
    const uniqueProviders = [
        ...new Set(tidiedData
            .map(d => providersById[modelsById[d.modelId].providerId].displayName)
            .filter(name => name !== "Human"))
    ];
    const providerFilters = uniqueProviders.sort().map(provider => ({
        id: `provider-filter-${provider.replace(/\s+/g, "-").toLowerCase()}`,
        provider: provider,
        color: colorMappings.provider[provider] || defaultFilterColor
    }));
    const providerTrigger = document.getElementById("provider-trigger");
    const providerDropdown = document.getElementById("provider-dropdown");
    const providerOptionsContainer = document.getElementById("provider-options");
    const providerLabel = providerTrigger.querySelector(".multiselect-label");
    // Create "All" option at the top
    const allProviderOption = document.createElement("div");
    allProviderOption.className = "multiselect-option";
    allProviderOption.style.borderBottom = "1px solid rgba(255, 255, 255, 0.1)";
    allProviderOption.style.marginBottom = "4px";
    allProviderOption.style.paddingBottom = "12px";
    const allProviderLabel = document.createElement("span");
    allProviderLabel.className = "label";
    allProviderLabel.textContent = "All Authors";
    allProviderLabel.style.fontWeight = "bold";
    allProviderOption.appendChild(allProviderLabel);
    allProviderOption.addEventListener("click", e => {
        e.stopPropagation();
        // Clear all selections
        filterState.providers = [];
        providerDropdown.querySelectorAll(".multiselect-option").forEach(opt => {
            opt.classList.remove("selected");
        });
        updateMultiselectLabel(providerLabel, filterState.providers, "All Authors");
        applyFilters();
    });
    providerOptionsContainer.appendChild(allProviderOption);
    // Create dropdown options
    providerFilters.forEach(filter => {
        const option = document.createElement("div");
        option.className = "multiselect-option";
        option.dataset.provider = filter.provider;
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "20");
        svg.setAttribute("height", "20");
        svg.setAttribute("viewBox", "0 0 20 20");
        svg.setAttribute("class", "icon");
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", "2");
        rect.setAttribute("y", "2");
        rect.setAttribute("width", "16");
        rect.setAttribute("height", "16");
        rect.setAttribute("rx", "3");
        rect.setAttribute("fill", filter.color);
        svg.appendChild(rect);
        appendSelectionCheckmark(svg, filter.color);
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = filter.provider;
        const onlyBtn = document.createElement("span");
        onlyBtn.className = "only-btn";
        onlyBtn.textContent = "only";
        option.appendChild(svg);
        option.appendChild(label);
        option.appendChild(onlyBtn);
        // "Only" button click handler
        onlyBtn.addEventListener("click", e => {
            e.stopPropagation();
            // Clear all selections
            filterState.providers = [filter.provider];
            providerDropdown.querySelectorAll(".multiselect-option").forEach(opt => {
                opt.classList.remove("selected");
            });
            option.classList.add("selected");
            updateMultiselectLabel(providerLabel, filterState.providers, "All Authors");
            applyFilters();
        });
        // Regular option click handler
        option.addEventListener("click", e => {
            e.stopPropagation();
            const isSelected = filterState.providers.includes(filter.provider);
            if (isSelected) {
                filterState.providers = filterState.providers.filter(p => p !== filter.provider);
                option.classList.remove("selected");
            }
            else {
                filterState.providers.push(filter.provider);
                option.classList.add("selected");
            }
            updateMultiselectLabel(providerLabel, filterState.providers, "All Authors");
            applyFilters();
        });
        providerOptionsContainer.appendChild(option);
    });
    // Toggle dropdown
    providerTrigger.addEventListener("click", e => {
        e.stopPropagation();
        const isOpen = providerDropdown.classList.contains("open");
        // Close all dropdowns first
        document.querySelectorAll(".multiselect-dropdown").forEach(dd => dd.classList.remove("open"));
        document.querySelectorAll(".multiselect-trigger").forEach(t => t.classList.remove("open"));
        if (!isOpen) {
            providerDropdown.classList.add("open");
            providerTrigger.classList.add("open");
        }
    });
    // --- Type Multi-Select Dropdown ---
    const uniqueModelTypes = [
        ...new Set(tidiedData.map(d => modelsById[d.modelId].modelType).filter(type => type !== null))
    ];
    const typeFilters = uniqueModelTypes.sort().map(type => ({
        id: `type-filter-${type.replace(/\s+/g, "-").toLowerCase()}`,
        type: type,
        color: "#808080"
    }));
    const typeTrigger = document.getElementById("type-trigger");
    const typeDropdown = document.getElementById("type-dropdown");
    const typeOptionsContainer = document.getElementById("type-options");
    const typeLabel = typeTrigger.querySelector(".multiselect-label");
    // Create "All" option at the top
    const allTypeOption = document.createElement("div");
    allTypeOption.className = "multiselect-option";
    allTypeOption.style.borderBottom = "1px solid rgba(255, 255, 255, 0.1)";
    allTypeOption.style.marginBottom = "4px";
    allTypeOption.style.paddingBottom = "12px";
    const allTypeLabel = document.createElement("span");
    allTypeLabel.className = "label";
    allTypeLabel.textContent = "All Types";
    allTypeLabel.style.fontWeight = "bold";
    allTypeOption.appendChild(allTypeLabel);
    allTypeOption.addEventListener("click", e => {
        e.stopPropagation();
        // Clear all selections
        filterState.modelTypes = [];
        typeDropdown.querySelectorAll(".multiselect-option").forEach(opt => {
            opt.classList.remove("selected");
        });
        updateMultiselectLabel(typeLabel, filterState.modelTypes, "All Types");
        applyFilters();
    });
    typeOptionsContainer.appendChild(allTypeOption);
    // Create dropdown options
    typeFilters.forEach(filter => {
        const option = document.createElement("div");
        option.className = "multiselect-option";
        option.dataset.type = filter.type;
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "20");
        svg.setAttribute("height", "20");
        svg.setAttribute("viewBox", "0 0 20 20");
        svg.setAttribute("class", "icon");
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", "2");
        rect.setAttribute("y", "2");
        rect.setAttribute("width", "16");
        rect.setAttribute("height", "16");
        rect.setAttribute("rx", "3");
        rect.setAttribute("fill", filter.color);
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("class", "type-icon-glyph");
        path.setAttribute("d", "M6,6 H14 V8 H11 V14 H9 V8 H6 Z");
        path.setAttribute("fill", "white");
        svg.appendChild(rect);
        svg.appendChild(path);
        appendSelectionCheckmark(svg, filter.color);
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = filter.type;
        const onlyBtn = document.createElement("span");
        onlyBtn.className = "only-btn";
        onlyBtn.textContent = "only";
        option.appendChild(svg);
        option.appendChild(label);
        option.appendChild(onlyBtn);
        // "Only" button click handler
        onlyBtn.addEventListener("click", e => {
            e.stopPropagation();
            // Clear all selections
            filterState.modelTypes = [filter.type];
            typeDropdown.querySelectorAll(".multiselect-option").forEach(opt => {
                opt.classList.remove("selected");
            });
            option.classList.add("selected");
            updateMultiselectLabel(typeLabel, filterState.modelTypes, "All Types");
            applyFilters();
        });
        // Regular option click handler
        option.addEventListener("click", e => {
            e.stopPropagation();
            const isSelected = filterState.modelTypes.includes(filter.type);
            if (isSelected) {
                filterState.modelTypes = filterState.modelTypes.filter(t => t !== filter.type);
                option.classList.remove("selected");
            }
            else {
                filterState.modelTypes.push(filter.type);
                option.classList.add("selected");
            }
            updateMultiselectLabel(typeLabel, filterState.modelTypes, "All Types");
            applyFilters();
        });
        typeOptionsContainer.appendChild(option);
    });
    // Toggle dropdown
    typeTrigger.addEventListener("click", e => {
        e.stopPropagation();
        const isOpen = typeDropdown.classList.contains("open");
        // Close all dropdowns first
        document.querySelectorAll(".multiselect-dropdown").forEach(dd => dd.classList.remove("open"));
        document.querySelectorAll(".multiselect-trigger").forEach(t => t.classList.remove("open"));
        if (!isOpen) {
            typeDropdown.classList.add("open");
            typeTrigger.classList.add("open");
        }
    });
    // --- Model Multi-Select Dropdown with Search ---
    const uniqueModels = [
        ...new Set(tidiedData
            .map(d => d.modelId)
            .filter(modelId => {
            const provider = providersById[modelsById[modelId].providerId];
            return provider && provider.displayName !== "Human";
        }))
    ];
    // Sort models by provider first, then by model name
    const modelFilters = uniqueModels
        .map(modelId => {
        const model = modelsById[modelId];
        const provider = providersById[model.providerId];
        return {
            id: `model-filter-${modelId.replace(/\s+/g, "-").toLowerCase()}`,
            modelId: modelId,
            modelName: model.displayName || modelId,
            providerName: provider.displayName,
            color: colorMappings.provider[provider.displayName] || "#808080"
        };
    })
        .sort((a, b) => {
        // Sort by provider first, then by model name
        if (a.providerName !== b.providerName) {
            return a.providerName.localeCompare(b.providerName);
        }
        return a.modelName.localeCompare(b.modelName);
    });
    const modelTrigger = document.getElementById("model-trigger");
    const modelDropdown = document.getElementById("model-dropdown");
    const modelLabel = modelTrigger.querySelector(".multiselect-label");
    const modelSearch = document.getElementById("model-search");
    const modelOptionsContainer = document.getElementById("model-options");
    // Create "All" option at the top
    const allModelOption = document.createElement("div");
    allModelOption.className = "multiselect-option";
    allModelOption.style.borderBottom = "1px solid rgba(255, 255, 255, 0.1)";
    allModelOption.style.marginBottom = "4px";
    allModelOption.style.paddingBottom = "12px";
    const allModelLabel = document.createElement("span");
    allModelLabel.className = "label";
    allModelLabel.textContent = "All Models";
    allModelLabel.style.fontWeight = "bold";
    allModelOption.appendChild(allModelLabel);
    allModelOption.addEventListener("click", e => {
        e.stopPropagation();
        // Clear all selections
        filterState.models = [];
        modelOptionsContainer.querySelectorAll(".multiselect-option").forEach(opt => {
            opt.classList.remove("selected");
        });
        updateMultiselectLabel(modelLabel, filterState.models, "All Models");
        applyFilters();
    });
    modelOptionsContainer.appendChild(allModelOption);
    // Store all model options for search filtering
    const allModelOptions = [];
    // Create dropdown options
    modelFilters.forEach(filter => {
        const option = document.createElement("div");
        option.className = "multiselect-option";
        option.dataset.modelId = filter.modelId;
        option.dataset.modelName = filter.modelName.toLowerCase();
        option.dataset.providerName = filter.providerName.toLowerCase();
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "20");
        svg.setAttribute("height", "20");
        svg.setAttribute("viewBox", "0 0 20 20");
        svg.setAttribute("class", "icon");
        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", "2");
        rect.setAttribute("y", "2");
        rect.setAttribute("width", "16");
        rect.setAttribute("height", "16");
        rect.setAttribute("rx", "3");
        rect.setAttribute("fill", filter.color);
        svg.appendChild(rect);
        appendSelectionCheckmark(svg, filter.color);
        const label = document.createElement("span");
        label.className = "label";
        label.textContent = filter.modelName;
        const onlyBtn = document.createElement("span");
        onlyBtn.className = "only-btn";
        onlyBtn.textContent = "only";
        option.appendChild(svg);
        option.appendChild(label);
        option.appendChild(onlyBtn);
        // "Only" button click handler
        onlyBtn.addEventListener("click", e => {
            e.stopPropagation();
            // Clear all selections
            filterState.models = [filter.modelId];
            modelOptionsContainer.querySelectorAll(".multiselect-option").forEach(opt => {
                opt.classList.remove("selected");
            });
            option.classList.add("selected");
            updateMultiselectLabel(modelLabel, filterState.models.map(id => modelsById[id].displayName || id), "All Models");
            applyFilters();
        });
        // Regular option click handler
        option.addEventListener("click", e => {
            e.stopPropagation();
            const isSelected = filterState.models.includes(filter.modelId);
            if (isSelected) {
                filterState.models = filterState.models.filter(m => m !== filter.modelId);
                option.classList.remove("selected");
            }
            else {
                filterState.models.push(filter.modelId);
                option.classList.add("selected");
            }
            updateMultiselectLabel(modelLabel, filterState.models.map(id => modelsById[id].displayName || id), "All Models");
            applyFilters();
        });
        allModelOptions.push(option);
        modelOptionsContainer.appendChild(option);
    });
    // Search functionality
    modelSearch.addEventListener("input", e => {
        const searchTerm = e.target.value.toLowerCase();
        allModelOptions.forEach(option => {
            const modelName = option.dataset.modelName;
            const providerName = option.dataset.providerName;
            if (modelName.includes(searchTerm) || providerName.includes(searchTerm)) {
                option.style.display = "";
            }
            else {
                option.style.display = "none";
            }
        });
    });
    // Prevent dropdown from closing when clicking on search input
    modelSearch.addEventListener("click", e => {
        e.stopPropagation();
    });
    // Toggle dropdown
    modelTrigger.addEventListener("click", e => {
        e.stopPropagation();
        const isOpen = modelDropdown.classList.contains("open");
        // Close all dropdowns first
        document.querySelectorAll(".multiselect-dropdown").forEach(dd => dd.classList.remove("open"));
        document.querySelectorAll(".multiselect-trigger").forEach(t => t.classList.remove("open"));
        if (!isOpen) {
            modelDropdown.classList.add("open");
            modelTrigger.classList.add("open");
            // Focus search input when opening
            setTimeout(() => modelSearch.focus(), 100);
        }
    });
    // Helper function to update multiselect label
    function updateMultiselectLabel(labelElement, selectedItems, defaultText) {
        if (selectedItems.length === 0) {
            labelElement.textContent = defaultText;
        }
        else if (selectedItems.length === 1) {
            labelElement.textContent = selectedItems[0];
        }
        else {
            labelElement.textContent = `${selectedItems.length} Selected`;
        }
    }
    // Close dropdowns when clicking outside
    document.addEventListener("click", () => {
        document.querySelectorAll(".multiselect-dropdown").forEach(dd => dd.classList.remove("open"));
        document.querySelectorAll(".multiselect-trigger").forEach(t => t.classList.remove("open"));
    });
    // After creating the scatterplot, set the initial color mapping
    // Add color mode filter handlers
    const colorModeFilter = d3
        .select("#color-mode-filter")
        .selectAll(".filter-item")
        .on("click", function () {
        // Update UI
        d3.selectAll("#color-mode-filter .filter-item").classed("active", false);
        d3.select(this).classed("active", true);
        // Get the selected color mode from data attribute
        const newColorMode = d3.select(this).attr("data-mode");
        // Update state
        filterState.colorMode = newColorMode;
        // Update the scatterplot's color mapping
        scatterplot.setColorMapping(colorMappings[newColorMode], newColorMode);
        // Apply filters (uses updated color mapping)
        applyFilters();
        // Update the filter sections to reflect the new color scheme
        updateFilterColors();
    });
    // Function to update filter section colors based on selected color mode
    function updateFilterColors() {
        // Update provider dropdown option colors
        const providerOptions = providerDropdown.querySelectorAll(".multiselect-option");
        providerOptions.forEach(option => {
            const provider = option.dataset.provider;
            const rect = option.querySelector("svg rect");
            if (rect) {
                if (filterState.colorMode === "provider") {
                    rect.setAttribute("fill", colorMappings.provider[provider] || "#ffdc00ff");
                }
                else {
                    rect.setAttribute("fill", "#808080");
                }
            }
        });
        // Update type dropdown option colors
        const typeOptions = typeDropdown.querySelectorAll(".multiselect-option");
        typeOptions.forEach(option => {
            const type = option.dataset.type;
            const rect = option.querySelector("svg rect");
            if (rect) {
                if (filterState.colorMode === "type") {
                    rect.setAttribute("fill", colorMappings.type[type] || "#808080");
                }
                else {
                    rect.setAttribute("fill", "#808080");
                }
            }
        });
    }
    // Initial color update
    updateFilterColors();
    // Add resize handler for responsive chart
    let resizeTimeout;
    window.addEventListener("resize", () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const nextChartLayout = getChartLayout();
            scatterplot
                .width(nextChartLayout.width)
                .height(nextChartLayout.height)
                .margin(nextChartLayout.margin);
            renderCurrentVersion(0);
        }, 250); // Debounce resize events
    });
    const endTime = performance.now();
    const loadTime = endTime - startTime;
}
// Wait for dependencies and required DOM nodes before running.
// During client-side navigation, scripts can execute before page nodes mount.
function waitForDependencies(callback, timeoutMs = 30000, intervalMs = 100) {
    const startedAt = Date.now();
    const checkDependencies = () => {
        const missing = [];
        if (typeof d3 === "undefined")
            missing.push("d3");
        if (typeof loadAllData !== "function")
            missing.push("loadAllData");
        if (typeof reusableScatterplot !== "function")
            missing.push("reusableScatterplot");
        if (!document.getElementById("chart-wrapper"))
            missing.push("#chart-wrapper");
        if (!document.getElementById("reusable-scatterplot-container")) {
            missing.push("#reusable-scatterplot-container");
        }
        if (!document.getElementById("download-chart"))
            missing.push("#download-chart");
        if (!document.getElementById("x-axis-filter"))
            missing.push("#x-axis-filter");
        if (missing.length === 0) {
            callback();
            return;
        }
        if (Date.now() - startedAt < timeoutMs) {
            setTimeout(checkDependencies, intervalMs);
            return;
        }
        console.error(`Leaderboard dependencies failed to load: ${missing.join(", ")}`);
    };
    checkDependencies();
}
function initLeaderboard() {
    waitForDependencies(runLeaderboard);
}
window.initLeaderboard = initLeaderboard;
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLeaderboard);
}
else {
    initLeaderboard();
}
