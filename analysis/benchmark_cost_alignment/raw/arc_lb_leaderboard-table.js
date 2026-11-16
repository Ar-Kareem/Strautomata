"use strict";
// @ts-nocheck
// -----------------------------------------
// Refactored Table Generator using new data structures
// -----------------------------------------
function createLeaderboardTable(containerId) {
    // Get container and add class using D3
    const container = d3.select(`#${containerId}`)
        .classed('leaderboard-table', true);
    // Check if data is already loaded
    if (evaluations && evaluations.length > 0) {
        processAndBuildTable();
    }
    else {
        // If data is not yet loaded, load it
        loadAllData().then(() => {
            processAndBuildTable();
        }).catch(err => {
            console.error("Error loading evaluation data:", err);
        });
    }
    // Process data and build the table
    function processAndBuildTable() {
        // Group evaluations by modelId and dataset version
        const modelEvaluations = {};
        evaluations.forEach(evaluation => {
            const modelId = evaluation.modelId;
            const datasetId = evaluation.datasetId;
            // Skip evaluations that don't match our semi-private datasets
            if (!versions.includes(datasetId)) {
                return;
            }
            // Initialize if first time seeing this model
            if (!modelEvaluations[modelId]) {
                modelEvaluations[modelId] = {
                    modelId: modelId,
                    model: modelsById[modelId] || {},
                    provider: modelsById[modelId] ? providersById[modelsById[modelId].providerId] : {},
                    evaluations: {}
                };
            }
            // Store evaluation by dataset version
            modelEvaluations[modelId].evaluations[datasetId] = evaluation;
        });
        //console.log("modelEvaluations", modelEvaluations)
        // Convert to array and filter for display
        const tableData = Object.values(modelEvaluations).filter(item => {
            // Provider Adapter results are displayed beside the corresponding
            // standard Astra row instead of as separate models.
            if (item.model.modelGroup === "openai-gpt-6-astra-provider-adapter") {
                return false;
            }
            // Always show specific models
            if (points_to_show_on_table.includes(item.modelId)) {
                return true;
            }
            return true;
        });
        tableData.forEach(item => {
            if (item.model.modelGroup !== "openai-gpt-6-astra")
                return;
            const providerAdapter = modelEvaluations[`${item.modelId}-provider-adapter`];
            item.providerAdapterEvaluation = providerAdapter === null || providerAdapter === void 0 ? void 0 : providerAdapter.evaluations[versions[2]];
        });
        // Sort data by model release date (newest first)
        tableData.sort((a, b) => {
            const dateA = a.model.modelReleaseDate || "";
            const dateB = b.model.modelReleaseDate || "";
            return dateB.localeCompare(dateA);
        });
        // Build the table using D3
        buildTableWithD3(tableData);
    }
    // Build the table using D3
    function buildTableWithD3(data) {
        // Clear container
        container.html("");
        // Define columns
        const columns = [
            { key: "model", label: "AI System", sortable: true },
            { key: "score-1", label: "ARC-AGI-1", sortable: true },
            { key: "score-2", label: "ARC-AGI-2", sortable: true },
            {
                key: "score-3",
                label: "ARC-AGI-3",
                sortable: true
            }
        ];
        // Create table structure
        const table = container.append("table")
            .attr("class", "data-table table table-striped");
        const thead = table.append("thead");
        const tbody = table.append("tbody");
        // Create header row
        thead.append("tr")
            .selectAll("th")
            .data(columns)
            .enter()
            .append("th")
            .text(d => d.label)
            .attr("data-sort", d => d.sortable ? d.key : null)
            .style("cursor", d => d.sortable ? "pointer" : null)
            .style("text-align", "left")
            .style("vertical-align", "top")
            .style("color", null);
        // A row links to its model group's results page when any of its
        // evaluations carries a resultsUrl; otherwise the row is not clickable.
        const rowResultsUrl = (d) => {
            for (const v of versions) {
                const u = d.evaluations[v] && d.evaluations[v].resultsUrl;
                if (u)
                    return u;
            }
            return null;
        };
        // Create rows
        const rows = tbody.selectAll("tr")
            .data(data)
            .enter()
            .append("tr")
            .attr("data-model-id", d => d.modelId)
            .style("cursor", d => rowResultsUrl(d) ? "pointer" : "default")
            .on("mouseover", function (event, d) {
            if (window.leaderboardDots && window.leaderboardDots[d.modelId]) {
                // Implement hover effect here
            }
        })
            .on("click", function (event, d) {
            const url = rowResultsUrl(d);
            if (url) {
                window.location.href = url;
            }
        });
        // Add cells to each row
        rows.each(function (d) {
            const row = d3.select(this);
            const model = d.model;
            const v1Eval = d.evaluations[versions[0]];
            const v2Eval = d.evaluations[versions[1]];
            const v3Eval = d.evaluations[versions[2]];
            const providerAdapterEval = d.providerAdapterEvaluation;
            // Extract data
            const modelName = model.displayName || model.id || "N/A";
            // Format v1 score
            let finalScoreV1 = "N/A";
            if (v1Eval && v1Eval.score !== null) {
                const score = v1Eval.score;
                const displayScore = (score > 0 && score <= 1) ? score * 100 : score;
                finalScoreV1 = displayScore.toFixed(1) + "%";
            }
            // Format v2 score
            let finalScoreV2 = "N/A";
            if (v2Eval && v2Eval.score !== null) {
                const score = v2Eval.score;
                const displayScore = (score > 0 && score <= 1) ? score * 100 : score;
                finalScoreV2 = displayScore.toFixed(1) + "%";
            }
            // Format v3 score
            let finalScoreV3 = "N/A";
            if (v3Eval && v3Eval.score !== null) {
                const score = v3Eval.score;
                const displayScore = (score > 0 && score <= 1) ? score * 100 : score;
                finalScoreV3 = displayScore.toFixed(1) + "%";
            }
            // Format provider adapter v3 score
            let finalProviderAdapterScoreV3 = "N/A";
            if (providerAdapterEval && providerAdapterEval.score !== null) {
                const score = providerAdapterEval.score;
                const displayScore = (score > 0 && score <= 1) ? score * 100 : score;
                finalProviderAdapterScoreV3 = displayScore.toFixed(1) + "%";
            }
            // Format cost/task for v1 and v2 separately.
            const formatCostPerTask = (cost) => {
                if (cost === null || cost === undefined)
                    return "N/A";
                if (cost < 1) {
                    return "$" + cost.toFixed(3);
                }
                if (cost < 1000) {
                    return "$" + cost.toFixed(2);
                }
                return "$" + (cost / 1000).toFixed(1) + "K";
            };
            const finalCostV1 = formatCostPerTask(v1Eval === null || v1Eval === void 0 ? void 0 : v1Eval.costPerTask);
            const finalCostV2 = formatCostPerTask(v2Eval === null || v2Eval === void 0 ? void 0 : v2Eval.costPerTask);
            // Format cost (v3 - total cost, not per task)
            let finalCostV3 = "N/A";
            let costV3 = v3Eval === null || v3Eval === void 0 ? void 0 : v3Eval.cost;
            if (costV3 !== null && costV3 !== undefined) {
                if (costV3 < 1) {
                    finalCostV3 = "$" + costV3.toFixed(3);
                }
                else if (costV3 < 1000) {
                    finalCostV3 = "$" + costV3.toFixed(2);
                }
                else {
                    finalCostV3 = "$" + (costV3 / 1000).toFixed(1) + "K";
                }
            }
            // Format provider adapter v3 cost
            let finalProviderAdapterCostV3 = "N/A";
            let providerAdapterCostV3 = providerAdapterEval === null || providerAdapterEval === void 0 ? void 0 : providerAdapterEval.cost;
            if (providerAdapterCostV3 !== null && providerAdapterCostV3 !== undefined) {
                if (providerAdapterCostV3 < 1) {
                    finalProviderAdapterCostV3 = "$" + providerAdapterCostV3.toFixed(3);
                }
                else if (providerAdapterCostV3 < 1000) {
                    finalProviderAdapterCostV3 = "$" + providerAdapterCostV3.toFixed(2);
                }
                else {
                    finalProviderAdapterCostV3 = "$" + (providerAdapterCostV3 / 1000).toFixed(1) + "K";
                }
            }
            const combineScoreAndCost = (score, cost, perTask = false) => {
                if (score === "N/A" && cost === "N/A")
                    return "N/A";
                const displayedCost = perTask && cost !== "N/A" ? `${cost}/task` : cost;
                return `${score}, ${displayedCost}`;
            };
            const finalV1Result = combineScoreAndCost(finalScoreV1, finalCostV1, true);
            const finalV2Result = combineScoreAndCost(finalScoreV2, finalCostV2, true);
            const finalV3Result = combineScoreAndCost(finalScoreV3, finalCostV3);
            const finalProviderAdapterV3Result = combineScoreAndCost(finalProviderAdapterScoreV3, finalProviderAdapterCostV3);
            const finalCombinedV3Result = providerAdapterEval
                ? `${finalV3Result} (Standard) · ${finalProviderAdapterV3Result} (Provider Adapter)`
                : finalV3Result === "N/A"
                    ? "N/A"
                    : `${finalV3Result} (Standard)`;
            // Add model cell with color styling
            row.append("td")
                .text(modelName)
                .style("color", () => {
                if (window.leaderboardColors && model.modelGroup) {
                    return window.leaderboardColors[model.modelGroup] || '';
                }
                return null;
            });
            // Add combined score and cost cells.
            row.append("td").text(finalV1Result);
            row.append("td").text(finalV2Result);
            row.append("td").text(finalCombinedV3Result);
        });
    }
}
