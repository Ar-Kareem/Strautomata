"use strict";

(function () {
  var app = {
    worker: null,
    workerRequestId: 0,
    pendingRequests: new Map(),
    manifest: {},
    gameStatsManifest: {},
    bots: [],
    botsById: Object.create(null),
    botsByRouteKey: Object.create(null),
    gameStatsByBotId: Object.create(null),
    loadedBotIds: Object.create(null),
    botSourceCache: Object.create(null),
    botOutputCache: Object.create(null),
    matchMode: "human_vs_llm",
    humanRole: null,
    humanVsBot: null,
    llmVsLlmBotA: null,
    llmVsLlmBotB: null,
    llmVsLlmDelayMs: 500,
    llmVsLlmPlaying: true,
    llmThinking: false,
    autoMoveTimer: null,
    hooksInstalled: false,
    controlsMounted: false,
    selectionRevision: 0,
    originalInitialize: null,
    originalPerform: null,
    originalUp: null,
    originalDn: null,
    panelNode: null,
    statusNode: null,
    roleSelect: null,
    humanBotSelect: null,
    llmBotASelect: null,
    llmBotBSelect: null,
    modeInputs: [],
    humanControlsNode: null,
    llmVsLlmControlsNode: null,
    llmVsLlmSpeedNode: null,
    llmVsLlmHintNode: null,
    llmBotALabelNode: null,
    llmBotBLabelNode: null,
    llmVsLlmSpeedSlider: null,
    llmVsLlmSpeedValueNode: null,
    playPauseButton: null,
    resetButton: null,
    moveNowButton: null,
    gameStatsNode: null,
    warningNode: null,
    humanBotCodeButton: null,
    llmBotACodeButton: null,
    llmBotBCodeButton: null,
    codeModalNode: null,
    codeModalTitleNode: null,
    codeModalContentNode: null,
    codeModalCloseButton: null,
  };

  var CONFIG = window.VS_LLM_CONFIG || {};
  var WORKER_URL = "/assets/vs_llm.worker.js";
  var MANIFEST_URL = "/assets/vs_llm_bots.json";
  var GAME_STATS_URL = "/assets/vs_llm_game_stats.json";
  var MOVE_TIMEOUT_MS = 10000;
  var LOAD_TIMEOUT_MS = 20000;
  var DEFAULT_LLM_VS_LLM_DELAY_MS = 500;
  var MAX_LLM_VS_LLM_DELAY_MS = 10000;
  var MIN_LLM_VS_LLM_SPEED = 0.1;
  var MAX_LLM_VS_LLM_SPEED = 6.7;
  var MIN_LLM_VS_LLM_DELAY_MS = 1000 / MAX_LLM_VS_LLM_SPEED;
  var LLM_VS_LLM_SPEED_STEP = 0.1;

  function setStatus(message, tone) {
    if (!app.statusNode) {
      return;
    }
    app.statusNode.textContent = message;
    var color = "#1f2937";
    if (tone === "error") {
      color = "#b91c1c";
    } else if (tone === "loading") {
      color = "#1d4ed8";
    } else if (tone === "ready") {
      color = "#047857";
    }
    app.statusNode.style.color = color;
  }

  function normalizeError(error) {
    if (error instanceof Error) {
      return error.message;
    }
    return String(error);
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function codeIconSvg(size) {
    var resolvedSize = size || 18;
    return (
      "<svg viewBox='0 0 24 24' width='" +
      resolvedSize +
      "' height='" +
      resolvedSize +
      "' aria-hidden='true' focusable='false'>" +
      "<path d='M8 8L3 12L8 16' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'></path>" +
      "<path d='M16 8L21 12L16 16' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'></path>" +
      "<path d='M14 5L10 19' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'></path>" +
      "</svg>"
    );
  }

  function sourcePathToOutputPath(sourcePath) {
    if (!sourcePath) {
      return "";
    }
    return String(sourcePath).replace(/\/2\.python_code\.py$/, "/1.output.txt");
  }

  function getRoles() {
    return Array.isArray(window.roles) ? window.roles.slice() : [];
  }

  function currentControlRole() {
    try {
      return window.findcontrol(window.state, window.library);
    } catch (_error) {
      return null;
    }
  }

  function isTerminalState() {
    try {
      return Boolean(window.findterminalp(window.state, window.library));
    } catch (_error) {
      return false;
    }
  }

  function isLatestPosition() {
    return window.movenum === window.movelog.length;
  }

  function supportsLlmVsLlm() {
    return getRoles().length === 2;
  }

  function getBotById(botId) {
    return botId ? app.botsById[String(botId)] || null : null;
  }

  function getBotByRouteKey(routeKey) {
    return routeKey ? app.botsByRouteKey[String(routeKey)] || null : null;
  }

  function parseNoBlameScore(bot) {
    if (!bot || bot.no_blame_score === undefined || bot.no_blame_score === null || bot.no_blame_score === "") {
      return null;
    }
    var value = Number(bot.no_blame_score);
    return Number.isFinite(value) ? value : null;
  }

  function parseBotElo(bot) {
    if (!bot || bot.elo === undefined || bot.elo === null || bot.elo === "") {
      return Number.NEGATIVE_INFINITY;
    }
    var value = Number(bot.elo);
    return Number.isFinite(value) ? value : Number.NEGATIVE_INFINITY;
  }

  function rankBotsForDefaultSelection() {
    var preferredBots = app.bots.filter(function (bot) {
      return bot && bot.bot_id !== "random";
    });
    var fallbackBots = preferredBots.length ? preferredBots : app.bots.slice();
    return fallbackBots.slice().sort(function (left, right) {
      var eloDelta = parseBotElo(right) - parseBotElo(left);
      if (eloDelta !== 0) {
        return eloDelta;
      }
      return String(left.label || left.bot_id || "").localeCompare(String(right.label || right.bot_id || ""));
    });
  }

  function getSelectedBotIds() {
    var selected = Object.create(null);
    if (app.matchMode === "llm_vs_llm") {
      [app.llmVsLlmBotA, app.llmVsLlmBotB].forEach(function (bot) {
        if (bot && bot.bot_id) {
          selected[String(bot.bot_id)] = true;
        }
      });
      return selected;
    }
    if (app.humanVsBot && app.humanVsBot.bot_id) {
      selected[String(app.humanVsBot.bot_id)] = true;
    }
    return selected;
  }

  function currentAutoMoveDelayMs() {
    if (app.matchMode === "llm_vs_llm") {
      return app.llmVsLlmDelayMs;
    }
    return 50;
  }

  function formatSpeed(delayMs) {
    if (!delayMs || delayMs <= 0) {
      return "0 moves/s";
    }
    return (1000 / delayMs).toFixed(2).replace(/0$/, "").replace(/\.$/, "") + " moves/s";
  }

  function delayMsToSliderSpeed(delayMs) {
    if (!delayMs || delayMs <= 0) {
      return MAX_LLM_VS_LLM_SPEED;
    }
    var speed = 1000 / delayMs;
    if (speed < MIN_LLM_VS_LLM_SPEED) {
      return MIN_LLM_VS_LLM_SPEED;
    }
    if (speed > MAX_LLM_VS_LLM_SPEED) {
      return MAX_LLM_VS_LLM_SPEED;
    }
    return speed;
  }

  function sliderSpeedToDelayMs(sliderValue) {
    var speed = Number(sliderValue);
    if (!Number.isFinite(speed) || speed <= 0) {
      return DEFAULT_LLM_VS_LLM_DELAY_MS;
    }
    var delayMs = 1000 / speed;
    if (delayMs < MIN_LLM_VS_LLM_DELAY_MS) {
      return MIN_LLM_VS_LLM_DELAY_MS;
    }
    if (delayMs > MAX_LLM_VS_LLM_DELAY_MS) {
      return MAX_LLM_VS_LLM_DELAY_MS;
    }
    return delayMs;
  }

  function currentRoutePath() {
    return "/vs_llm/" + encodeURIComponent(window.game) + "/";
  }

  function currentRouteSearch() {
    var params = new URLSearchParams();
    var roles = getRoles();
    params.set("mode", app.matchMode);
    if (app.matchMode === "llm_vs_llm") {
      if (app.llmVsLlmBotA) {
        params.set("a", app.llmVsLlmBotA.route_key);
      }
      if (app.llmVsLlmBotB) {
        params.set("b", app.llmVsLlmBotB.route_key);
      }
      if (app.llmVsLlmDelayMs !== DEFAULT_LLM_VS_LLM_DELAY_MS) {
        params.set("delay", String(app.llmVsLlmDelayMs));
      }
    } else {
      if (app.humanVsBot) {
        params.set("bot", app.humanVsBot.route_key);
      }
      if (roles.length && app.humanRole && app.humanRole !== roles[0]) {
        params.set("role", app.humanRole);
      }
    }
    var query = params.toString();
    return query ? "?" + query : "";
  }

  function syncBrowserRoute() {
    var nextPath = currentRoutePath();
    var nextSearch = currentRouteSearch();
    window.VS_LLM_CONFIG = window.VS_LLM_CONFIG || {};
    window.VS_LLM_CONFIG.currentPath = nextPath;
    var currentUrl = window.location.pathname + window.location.search;
    var nextUrl = nextPath + nextSearch;
    if (currentUrl !== nextUrl && window.history && window.history.replaceState) {
      window.history.replaceState({}, "", nextUrl);
    }
  }

  function automatedBotForRole(role) {
    if (!role) {
      return null;
    }
    if (app.matchMode === "human_vs_llm") {
      if (!app.humanVsBot) {
        return null;
      }
      return role === app.humanRole ? null : app.humanVsBot;
    }
    if (!supportsLlmVsLlm()) {
      return null;
    }
    var roles = getRoles();
    if (role === roles[0]) {
      return app.llmVsLlmBotA;
    }
    if (role === roles[1]) {
      return app.llmVsLlmBotB;
    }
    return null;
  }

  function shouldHumanControlTurn() {
    if (isTerminalState()) {
      return false;
    }
    if (app.matchMode !== "human_vs_llm") {
      return false;
    }
    if (!app.humanVsBot) {
      return true;
    }
    var control = currentControlRole();
    if (!control) {
      return true;
    }
    return control === app.humanRole;
  }

  function updateActionChooser() {
    var holder = document.getElementById("actionholder");
    var select = holder ? holder.querySelector("select") : null;
    if (select) {
      var enabled = isLatestPosition() && shouldHumanControlTurn() && !app.llmThinking;
      select.disabled = !enabled;
    }
    if (app.moveNowButton) {
      var control = currentControlRole();
      var canMove =
        isLatestPosition() &&
        !isTerminalState() &&
        !app.llmThinking &&
        Boolean(automatedBotForRole(control));
      app.moveNowButton.disabled = !canMove;
    }
  }

  function clearPendingRequests() {
    app.pendingRequests.forEach(function (pending) {
      clearTimeout(pending.timeoutId);
      pending.reject(new Error("Pyodide worker was reset"));
    });
    app.pendingRequests.clear();
  }

  function resetWorker() {
    if (app.worker) {
      app.worker.terminate();
      app.worker = null;
    }
    app.loadedBotIds = Object.create(null);
    clearPendingRequests();
  }

  function ensureWorker() {
    if (app.worker) {
      return;
    }
    app.worker = new Worker(WORKER_URL);
    app.worker.onmessage = function (event) {
      var message = event.data || {};
      if (message.kind === "status") {
        setStatus(message.message || "Worker update", message.tone || "loading");
        return;
      }
      if (message.kind !== "response") {
        return;
      }
      var pending = app.pendingRequests.get(message.id);
      if (!pending) {
        return;
      }
      clearTimeout(pending.timeoutId);
      app.pendingRequests.delete(message.id);
      if (message.ok) {
        pending.resolve(message.data);
      } else {
        pending.reject(new Error(message.error || "Unknown worker error"));
      }
    };
    app.worker.onerror = function () {
      setStatus("Pyodide worker crashed", "error");
      resetWorker();
    };
  }

  function workerRequest(type, payload, timeoutMs) {
    ensureWorker();
    return new Promise(function (resolve, reject) {
      var id = app.workerRequestId + 1;
      app.workerRequestId = id;
      var timeoutId = window.setTimeout(function () {
        app.pendingRequests.delete(id);
        resetWorker();
        reject(new Error("Timed out waiting for Pyodide worker"));
      }, timeoutMs);
      app.pendingRequests.set(id, {
        resolve: resolve,
        reject: reject,
        timeoutId: timeoutId,
      });
      app.worker.postMessage(Object.assign({ id: id, type: type }, payload || {}));
    });
  }

  function deepCopyState() {
    return JSON.parse(JSON.stringify(window.state || []));
  }

  function currentLegalMoveStrings() {
    try {
      return window.findlegals(window.state, window.library).map(function (move) {
        return window.grind(move);
      });
    } catch (_error) {
      return [];
    }
  }

  async function fetchJson(url) {
    var response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Failed to load " + url);
    }
    return await response.json();
  }

  async function fetchText(url) {
    var response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Failed to load " + url);
    }
    return await response.text();
  }

  function refreshRoleOptions() {
    if (!app.roleSelect) {
      return;
    }
    var roles = getRoles();
    var previousValue = app.humanRole;
    app.roleSelect.innerHTML = "";
    roles.forEach(function (roleName) {
      var option = document.createElement("option");
      option.value = roleName;
      option.textContent = roleName;
      app.roleSelect.appendChild(option);
    });
    if (!roles.length) {
      app.humanRole = null;
      return;
    }
    if (previousValue && roles.indexOf(previousValue) >= 0) {
      app.roleSelect.value = previousValue;
      app.humanRole = previousValue;
    } else {
      app.roleSelect.value = roles[0];
      app.humanRole = roles[0];
    }
  }

  function refreshBotSelect(select, placeholderText, selectedBot) {
    if (!select) {
      return;
    }
    select.innerHTML = "";
    var placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = placeholderText;
    select.appendChild(placeholder);
    app.bots.forEach(function (bot) {
      var option = document.createElement("option");
      option.value = bot.bot_id;
      option.textContent = bot.dropdown_label || bot.label;
      option.title = bot.source_path;
      select.appendChild(option);
    });
    select.value = selectedBot ? selectedBot.bot_id : "";
  }

  function refreshBotOptions() {
    refreshBotSelect(app.humanBotSelect, "Play manually", app.humanVsBot);
    refreshBotSelect(app.llmBotASelect, "Choose LLM", app.llmVsLlmBotA);
    refreshBotSelect(app.llmBotBSelect, "Choose LLM", app.llmVsLlmBotB);
    renderGameStats();
    updateSelectionWarning();
    updateCodeButtons();
  }

  function updateSpeedUi() {
    if (app.llmVsLlmSpeedSlider) {
      app.llmVsLlmSpeedSlider.value = String(delayMsToSliderSpeed(app.llmVsLlmDelayMs));
    }
    if (app.llmVsLlmSpeedValueNode) {
      app.llmVsLlmSpeedValueNode.textContent = formatSpeed(app.llmVsLlmDelayMs);
    }
  }

  function updatePlayPauseUi() {
    if (!app.playPauseButton) {
      return;
    }
    var visible = app.matchMode === "llm_vs_llm";
    app.playPauseButton.style.display = visible ? "inline-flex" : "none";
    if (!visible) {
      return;
    }
    app.playPauseButton.textContent = app.llmVsLlmPlaying ? "Pause" : "Play";
    app.playPauseButton.disabled = !supportsLlmVsLlm();
    app.playPauseButton.style.opacity = app.playPauseButton.disabled ? "0.55" : "1";
  }

  function selectionSignature() {
    return JSON.stringify({
      matchMode: app.matchMode,
      humanVsBotId: app.humanVsBot ? app.humanVsBot.bot_id : null,
      llmVsLlmBotAId: app.llmVsLlmBotA ? app.llmVsLlmBotA.bot_id : null,
      llmVsLlmBotBId: app.llmVsLlmBotB ? app.llmVsLlmBotB.bot_id : null,
    });
  }

  function updateModeInputs() {
    app.modeInputs.forEach(function (input) {
      input.checked = input.value === app.matchMode;
    });
  }

  function updateRoleBotLabels() {
    var roles = getRoles();
    if (app.llmBotALabelNode) {
      app.llmBotALabelNode.textContent = "LLM for " + (roles[0] || "Role 1");
    }
    if (app.llmBotBLabelNode) {
      app.llmBotBLabelNode.textContent = "LLM for " + (roles[1] || "Role 2");
    }
    if (app.llmVsLlmHintNode) {
      if (!supportsLlmVsLlm()) {
        app.llmVsLlmHintNode.textContent = "LLM vs LLM requires exactly two roles.";
        app.llmVsLlmHintNode.style.color = "#b91c1c";
      } else {
        app.llmVsLlmHintNode.textContent = "";
        app.llmVsLlmHintNode.style.color = "#475569";
      }
    }
  }

  function updateModeUi() {
    updateModeInputs();
    updateRoleBotLabels();
    if (app.humanControlsNode) {
      app.humanControlsNode.style.display = app.matchMode === "human_vs_llm" ? "flex" : "none";
    }
    if (app.llmVsLlmControlsNode) {
      app.llmVsLlmControlsNode.style.display = app.matchMode === "llm_vs_llm" ? "flex" : "none";
    }
    if (app.llmVsLlmSpeedNode) {
      app.llmVsLlmSpeedNode.style.display = app.matchMode === "llm_vs_llm" ? "flex" : "none";
    }
    var llmVsLlmDisabled = !supportsLlmVsLlm();
    if (app.llmBotASelect) {
      app.llmBotASelect.disabled = llmVsLlmDisabled;
    }
    if (app.llmBotBSelect) {
      app.llmBotBSelect.disabled = llmVsLlmDisabled;
    }
    if (app.roleSelect) {
      app.roleSelect.disabled = app.matchMode !== "human_vs_llm";
    }
    updatePlayPauseUi();
    updateCodeButtons();
  }

  function readSelectionsFromInputs() {
    if (app.roleSelect) {
      app.humanRole = app.roleSelect.value || null;
    }
    if (app.humanBotSelect) {
      app.humanVsBot = getBotById(app.humanBotSelect.value);
    }
    if (app.llmBotASelect) {
      app.llmVsLlmBotA = getBotById(app.llmBotASelect.value);
    }
    if (app.llmBotBSelect) {
      app.llmVsLlmBotB = getBotById(app.llmBotBSelect.value);
    }
    app.modeInputs.forEach(function (input) {
      if (input.checked) {
        app.matchMode = input.value;
      }
    });
  }

  function buildReadyStatus() {
    if (app.matchMode === "human_vs_llm") {
      if (!app.humanVsBot) {
        return "No LLM selected. You can play both sides manually.";
      }
      return app.humanVsBot.label + " is ready. You control " + (app.humanRole || "your chosen role") + ".";
    }
    if (!supportsLlmVsLlm()) {
      return "LLM vs LLM requires exactly two roles.";
    }
    if (!app.llmVsLlmBotA || !app.llmVsLlmBotB) {
      return "Choose one LLM for each role.";
    }
    var roles = getRoles();
    return (
      app.llmVsLlmBotA.label +
      " controls " +
      roles[0] +
      "; " +
      app.llmVsLlmBotB.label +
      " controls " +
      roles[1] +
      "."
    );
  }

  function codeButtonTitle(bot) {
    if (!bot) {
      return "Choose a bot to view its code";
    }
    return "Show code for " + bot.label;
  }

  function updateCodeButton(button, bot) {
    if (!button) {
      return;
    }
    button.disabled = !bot;
    button.title = codeButtonTitle(bot);
    if (button.disabled) {
      button.style.opacity = "0.45";
      button.style.cursor = "default";
      button.style.background = "#f8fafc";
      button.style.borderColor = "#e2e8f0";
      return;
    }
    button.style.opacity = "1";
    button.style.cursor = "pointer";
    button.style.background = "#ffffff";
    button.style.borderColor = "#cbd5e1";
  }

  function installCodeButtonHover(button) {
    if (!button) {
      return;
    }
    function applyHoverState(active) {
      if (button.disabled) {
        return;
      }
      button.style.background = active ? "#e2e8f0" : "#ffffff";
      button.style.borderColor = active ? "#94a3b8" : "#cbd5e1";
    }
    button.addEventListener("mouseenter", function () {
      applyHoverState(true);
    });
    button.addEventListener("mouseleave", function () {
      applyHoverState(false);
    });
    button.addEventListener("focus", function () {
      applyHoverState(true);
    });
    button.addEventListener("blur", function () {
      applyHoverState(false);
    });
  }

  function wireGameStatsCodeButtons() {
    if (!app.gameStatsNode) {
      return;
    }
    Array.prototype.slice
      .call(app.gameStatsNode.querySelectorAll("[data-vs-llm-view-bot]"))
      .forEach(function (button) {
        installCodeButtonHover(button);
        button.addEventListener("click", function () {
          var botId = button.getAttribute("data-vs-llm-view-bot") || "";
          void openBotCode(getBotById(botId));
        });
      });
  }

  function updateCodeButtons() {
    updateCodeButton(app.humanBotCodeButton, app.humanVsBot);
    updateCodeButton(app.llmBotACodeButton, app.llmVsLlmBotA);
    updateCodeButton(app.llmBotBCodeButton, app.llmVsLlmBotB);
  }

  function closeCodeModal() {
    if (!app.codeModalNode) {
      return;
    }
    app.codeModalNode.style.display = "none";
  }

  function formatStrategyText(text) {
    return escapeHtml(text || "").replace(/\n/g, "<br>");
  }

  function highlightPython(codeText) {
    var code = String(codeText || "");
    var tokenRe =
      /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#.*$)|\b(class|def|return|if|elif|else|for|while|import|from|as|try|except|finally|raise|with|in|is|not|and|or|lambda|yield|pass|break|continue|True|False|None|global|nonlocal|assert|del|await|async)\b|\b(\d+(?:\.\d+)?)\b|\b([A-Z][A-Z0-9_]*)\b|\b(list|dict|tuple|set|frozenset|str|int|float|bool|object|bytes|bytearray|memoryview|complex|range|enumerate|zip|map|filter|sum|min|max|len|sorted|reversed|abs|all|any|print|open|isinstance|issubclass|iter|next|super|type|staticmethod|classmethod|property|Exception|ValueError|TypeError|RuntimeError|KeyError|IndexError|AttributeError|StopIteration|NotImplementedError|self|cls)\b|(@[A-Za-z_][A-Za-z0-9_\.]*)|(\.[A-Za-z_][A-Za-z0-9_]*)/gm;
    var lastIndex = 0;
    var htmlParts = [];
    var match;
    while ((match = tokenRe.exec(code)) !== null) {
      if (match.index > lastIndex) {
        htmlParts.push(escapeHtml(code.slice(lastIndex, match.index)));
      }
      if (match[1] !== undefined) {
        var tokenText = match[1];
        var tokenStyle = tokenText.startsWith("#")
          ? "color:#c586c0"
          : "color:#86efac";
        htmlParts.push("<span style='" + tokenStyle + "'>" + escapeHtml(tokenText) + "</span>");
      } else if (match[2] !== undefined) {
        htmlParts.push("<span style='color:#93c5fd;font-weight:600'>" + escapeHtml(match[2]) + "</span>");
      } else if (match[3] !== undefined) {
        htmlParts.push("<span style='color:#fca5a5'>" + escapeHtml(match[3]) + "</span>");
      } else if (match[4] !== undefined) {
        htmlParts.push("<span style='color:#ef4444;font-weight:600'>" + escapeHtml(match[4]) + "</span>");
      } else if (match[5] !== undefined) {
        htmlParts.push("<span style='color:#fcd34d'>" + escapeHtml(match[5]) + "</span>");
      } else if (match[6] !== undefined) {
        htmlParts.push("<span style='color:#67e8f9'>" + escapeHtml(match[6]) + "</span>");
      } else if (match[7] !== undefined) {
        htmlParts.push("<span style='color:#60a5fa'>" + escapeHtml(match[7]) + "</span>");
      }
      lastIndex = tokenRe.lastIndex;
    }
    if (lastIndex < code.length) {
      htmlParts.push(escapeHtml(code.slice(lastIndex)));
    }
    return htmlParts.join("");
  }

  function parseBotOutput(outputText, fallbackCode) {
    var text = String(outputText || "").trim();
    var fallback = String(fallbackCode || "");
    if (!text) {
      return {
        strategy: "No saved strategy text was found for this bot.",
        code: fallback,
      };
    }
    var codeMatch = text.match(/<code>\s*([\s\S]*?)\s*<\/code>/i);
    if (!codeMatch) {
      return {
        strategy: text,
        code: fallback,
      };
    }
    var strategyText = text.replace(/<code>[\s\S]*<\/code>/i, "").trim();
    if (!strategyText) {
      strategyText = "No separate strategy text was found for this bot.";
    }
    return {
      strategy: strategyText,
      code: codeMatch[1].trim() || fallback,
    };
  }

  function showCodeModal(title, strategyText, codeText) {
    if (!app.codeModalNode || !app.codeModalTitleNode || !app.codeModalContentNode) {
      return;
    }
    app.codeModalTitleNode.textContent = title;
    app.codeModalContentNode.innerHTML = [
      "<div style='padding:14px 16px;border-bottom:1px solid #1e293b;background:#111827;color:#e5e7eb'>",
      "  <div style='font-size:13px;font-weight:600;letter-spacing:0.02em;color:#93c5fd;margin-bottom:8px'>Strategy</div>",
      "  <div style='white-space:pre-wrap;font-size:13px;line-height:1.6'>" + formatStrategyText(strategyText) + "</div>",
      "</div>",
      "<div style='padding:14px 16px'>",
      "  <div title='Code' style='display:inline-flex;align-items:center;justify-content:center;color:#93c5fd;margin-bottom:8px'>" + codeIconSvg(18) + "</div>",
      "  <pre style='margin:0;white-space:pre-wrap;word-break:break-word;color:#e2e8f0;font-size:12px;line-height:1.55'><code>" + highlightPython(codeText) + "</code></pre>",
      "</div>",
    ].join("");
    app.codeModalNode.style.display = "flex";
  }

  async function openBotCode(bot) {
    if (!bot) {
      return;
    }
    var cacheKey = String(bot.source_path || "");
    if (!cacheKey) {
      showCodeModal(bot.label, "No source path is available for this bot.", "");
      return;
    }
    showCodeModal(bot.label, "Loading strategy...", "Loading code...");
    try {
      if (!Object.prototype.hasOwnProperty.call(app.botSourceCache, cacheKey)) {
        app.botSourceCache[cacheKey] = await fetchText("/" + cacheKey);
      }
      var outputPath = sourcePathToOutputPath(cacheKey);
      if (outputPath && !Object.prototype.hasOwnProperty.call(app.botOutputCache, outputPath)) {
        app.botOutputCache[outputPath] = await fetchText("/" + outputPath).catch(function () {
          return "";
        });
      }
      var parsed = parseBotOutput(
        outputPath ? app.botOutputCache[outputPath] : "",
        app.botSourceCache[cacheKey]
      );
      showCodeModal("Strategy Code: " + bot.label, parsed.strategy, parsed.code);
    } catch (error) {
      showCodeModal(
        "Strategy Code: " + bot.label,
        "Failed to load strategy/code.",
        "Error: " + normalizeError(error)
      );
    }
  }

  function updateSelectionWarning() {
    if (!app.warningNode) {
      return;
    }
    var riskyBots = [];
    var seen = Object.create(null);

    function maybeAdd(bot) {
      if (!bot || seen[bot.bot_id]) {
        return;
      }
      seen[bot.bot_id] = true;
      var noBlameScore = parseNoBlameScore(bot);
      if (noBlameScore !== null && noBlameScore < 0.5) {
        riskyBots.push({ label: bot.label, noBlameScore: noBlameScore });
      }
    }

    if (app.matchMode === "human_vs_llm") {
      maybeAdd(app.humanVsBot);
    } else {
      maybeAdd(app.llmVsLlmBotA);
      maybeAdd(app.llmVsLlmBotB);
    }

    if (!riskyBots.length) {
      app.warningNode.style.display = "none";
      app.warningNode.textContent = "";
      return;
    }

    var message;
    if (riskyBots.length === 1) {
      message =
        riskyBots[0].label +
        " has low No Blame Score of " +
        riskyBots[0].noBlameScore.toFixed(2) +
        " thus it will most likely cause errors / illegal moves.";
    } else {
      message =
        riskyBots
          .map(function (entry) {
            return (
              entry.label +
              " has low No Blame Score of " +
              entry.noBlameScore.toFixed(2) +
              " thus it will most likely cause errors / illegal moves."
            );
          })
          .join(" ");
    }

    app.warningNode.style.display = "block";
    app.warningNode.textContent = message;
  }

  function renderGameStats() {
    if (!app.gameStatsNode) {
      return;
    }
    var entries = Object.entries(app.gameStatsByBotId || {});
    if (!entries.length) {
      app.gameStatsNode.innerHTML =
        "<div style='border:1px solid #e2e8f0;background:#ffffff;padding:10px 12px;color:#64748b;font-size:13px'>No archived game stats found for this game.</div>";
      return;
    }

    var selectedBotIds = getSelectedBotIds();
    entries.sort(function (left, right) {
      var leftElo = Number((left[1] && left[1].ELO) || Number.NEGATIVE_INFINITY);
      var rightElo = Number((right[1] && right[1].ELO) || Number.NEGATIVE_INFINITY);
      if (leftElo !== rightElo) {
        return rightElo - leftElo;
      }
      return String(left[0]).localeCompare(String(right[0]));
    });

    var rowsHtml = entries
      .map(function (entry) {
        var botId = String(entry[0]);
        var stats = entry[1] || {};
        var bot = getBotById(botId);
        var label = bot ? bot.label : botId;
        var highlighted = Boolean(selectedBotIds[botId]);
        var rowStyle = highlighted ? "background:#ecfccb;" : "";
        var labelStyle = highlighted ? "font-weight:600;" : "";
        var viewButtonHtml = bot && bot.bot_id !== "random"
          ? "<button data-vs-llm-view-bot='" + escapeHtml(botId) + "' type='button' title='Show strategy and code for " + escapeHtml(label) + "' style='display:inline-flex;align-items:center;justify-content:center;width:32px;height:28px;padding:0;border:1px solid #cbd5e1;background:#ffffff;color:#334155;transition:background 120ms ease,border-color 120ms ease,opacity 120ms ease'>" + codeIconSvg(16) + "</button>"
          : "";
        return [
          "<tr style='" + rowStyle + "'>",
          "  <td style='padding:4px 8px;" + labelStyle + "'>" + escapeHtml(label) + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.ELO || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.win || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.loss || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.draw || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.error || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.timeout || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.done || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:right'>" + escapeHtml(stats.No_Blame_Score || "") + "</td>",
          "  <td style='padding:4px 8px;text-align:center'>" + viewButtonHtml + "</td>",
          "</tr>",
        ].join("");
      })
      .join("");

    app.gameStatsNode.innerHTML = [
      "<div style='border:1px solid #cbd5e1;background:#ffffff'>",
      "  <div style='padding:8px 10px;border-bottom:1px solid #e2e8f0;background:#f8fafc'>",
      "    <div style='font-size:14px;color:#0f172a;font-weight:600'>Archived Game Stats</div>",
      "  </div>",
      "  <div>",
      "    <table style='width:100%;border-collapse:collapse;font-size:12px'>",
      "      <thead>",
      "        <tr style='background:#f8fafc;color:#475569'>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:left'>Bot</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>ELO Rating</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Wins</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Losses</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Draws</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Errors</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Timeouts</th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>Done <span title='Every match is counted as either done or as an error/timeout caused by one of the two bots.' style='display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;margin-left:4px;border:1px solid #94a3b8;border-radius:999px;font-size:10px;line-height:1;color:#475569;cursor:help'>i</span></th>",
      "          <th style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:right'>No Blame <span title='No Blame Score = done / (done + error). Timeouts are excluded. A value of 1 means the bot never caused an error; 0 means it always caused an error.' style='display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;margin-left:4px;border:1px solid #94a3b8;border-radius:999px;font-size:10px;line-height:1;color:#475569;cursor:help'>i</span></th>",
      "          <th title='Code' style='position:sticky;top:0;background:#f8fafc;padding:5px 8px;text-align:center'><span style='display:inline-flex;align-items:center;justify-content:center;color:#475569'>" + codeIconSvg(16) + "</span></th>",
      "        </tr>",
      "      </thead>",
      "      <tbody>",
      rowsHtml,
      "      </tbody>",
      "    </table>",
      "  </div>",
      "</div>",
    ].join("");
    wireGameStatsCodeButtons();
  }

  function buildPanel() {
    if (app.controlsMounted) {
      return;
    }
    var stateholder = document.getElementById("stateholder");
    if (!stateholder || !stateholder.parentNode) {
      return;
    }

    var panel = document.createElement("div");
    panel.style.maxWidth = "860px";
    panel.style.margin = "0 auto 24px auto";
    panel.style.padding = "14px 16px";
    panel.style.border = "1px solid #cbd5e1";
    panel.style.background = "#f8fafc";
    panel.style.fontFamily = "sans-serif";
    panel.style.textAlign = "left";

    panel.innerHTML = [
      "<style>",
      "  #vs-llm-speed-slider {",
      "    -webkit-appearance: none;",
      "    appearance: none;",
      "    width: 220px;",
      "    height: 6px;",
      "    border-radius: 999px;",
      "    background: #cbd5e1;",
      "    outline: none;",
      "  }",
      "  #vs-llm-speed-slider::-webkit-slider-runnable-track {",
      "    height: 6px;",
      "    border-radius: 999px;",
      "    background: #cbd5e1;",
      "  }",
      "  #vs-llm-speed-slider::-webkit-slider-thumb {",
      "    -webkit-appearance: none;",
      "    appearance: none;",
      "    width: 16px;",
      "    height: 16px;",
      "    margin-top: -5px;",
      "    border: 2px solid #ffffff;",
      "    border-radius: 999px;",
      "    background: #2563eb;",
      "    box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.28);",
      "    cursor: pointer;",
      "  }",
      "  #vs-llm-speed-slider::-moz-range-track {",
      "    height: 6px;",
      "    border: 0;",
      "    border-radius: 999px;",
      "    background: #cbd5e1;",
      "  }",
      "  #vs-llm-speed-slider::-moz-range-thumb {",
      "    width: 16px;",
      "    height: 16px;",
      "    border: 2px solid #ffffff;",
      "    border-radius: 999px;",
      "    background: #2563eb;",
      "    box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.28);",
      "    cursor: pointer;",
      "  }",
      "</style>",
      "<div id='vs-llm-game-stats' style='margin-bottom:12px'></div>",
      "<div style='display:flex;flex-wrap:wrap;gap:16px;align-items:center;margin-bottom:12px'>",
      "  <span style='font-size:14px;color:#334155'>Match Mode</span>",
      "  <label style='display:flex;align-items:center;gap:6px;color:#334155;font-size:14px'>",
      "    <input type='radio' name='vs-llm-mode' value='human_vs_llm' checked />",
      "    <span>Human vs LLM</span>",
      "  </label>",
      "  <label style='display:flex;align-items:center;gap:6px;color:#334155;font-size:14px'>",
      "    <input type='radio' name='vs-llm-mode' value='llm_vs_llm' />",
      "    <span>LLM vs LLM</span>",
      "  </label>",
      "</div>",
      "<div id='vs-llm-human-controls' style='display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end'>",
      "  <label style='display:flex;flex-direction:column;gap:4px;color:#334155;font-size:14px'>",
      "    <span>Human Role</span>",
      "    <select id='vs-llm-human-role' style='min-width:160px;padding:6px 8px'></select>",
      "  </label>",
      "  <div style='display:flex;flex-direction:column;gap:4px;color:#334155;font-size:14px'>",
      "    <span>LLM Bot</span>",
      "    <div style='display:flex;gap:8px;align-items:center'>",
      "      <select id='vs-llm-human-bot' style='min-width:280px;padding:6px 8px'></select>",
      "      <button id='vs-llm-human-bot-code' type='button' title='Show selected bot code' style='display:inline-flex;align-items:center;justify-content:center;width:36px;height:34px;padding:0;border:1px solid #cbd5e1;background:#ffffff;color:#334155;transition:background 120ms ease,border-color 120ms ease,opacity 120ms ease'>" + codeIconSvg(18) + "</button>",
      "    </div>",
      "  </div>",
      "</div>",
      "<div id='vs-llm-llm-controls' style='display:none;flex-wrap:wrap;gap:12px;align-items:flex-end'>",
      "  <div style='display:flex;flex-direction:column;gap:4px;color:#334155;font-size:14px'>",
      "    <span id='vs-llm-bot-a-label'>LLM for Role 1</span>",
      "    <div style='display:flex;gap:8px;align-items:center'>",
      "      <select id='vs-llm-bot-a' style='min-width:280px;padding:6px 8px'></select>",
      "      <button id='vs-llm-bot-a-code' type='button' title='Show selected bot code' style='display:inline-flex;align-items:center;justify-content:center;width:36px;height:34px;padding:0;border:1px solid #cbd5e1;background:#ffffff;color:#334155;transition:background 120ms ease,border-color 120ms ease,opacity 120ms ease'>" + codeIconSvg(18) + "</button>",
      "    </div>",
      "  </div>",
      "  <div style='display:flex;flex-direction:column;gap:4px;color:#334155;font-size:14px'>",
      "    <span id='vs-llm-bot-b-label'>LLM for Role 2</span>",
      "    <div style='display:flex;gap:8px;align-items:center'>",
      "      <select id='vs-llm-bot-b' style='min-width:280px;padding:6px 8px'></select>",
      "      <button id='vs-llm-bot-b-code' type='button' title='Show selected bot code' style='display:inline-flex;align-items:center;justify-content:center;width:36px;height:34px;padding:0;border:1px solid #cbd5e1;background:#ffffff;color:#334155;transition:background 120ms ease,border-color 120ms ease,opacity 120ms ease'>" + codeIconSvg(18) + "</button>",
      "    </div>",
      "  </div>",
      "</div>",
      "<div id='vs-llm-speed-controls' style='display:none;align-items:center;gap:12px;margin-top:10px'>",
      "  <label style='display:flex;align-items:center;gap:10px;color:#334155;font-size:14px'>",
      "    <span>Speed</span>",
      "    <input id='vs-llm-speed-slider' type='range' title='' min='" + MIN_LLM_VS_LLM_SPEED + "' max='" + MAX_LLM_VS_LLM_SPEED + "' step='" + LLM_VS_LLM_SPEED_STEP + "' value='" + delayMsToSliderSpeed(DEFAULT_LLM_VS_LLM_DELAY_MS) + "' />",
      "  </label>",
      "  <span id='vs-llm-speed-value' style='color:#0f172a;font-size:14px;min-width:44px'></span>",
      "</div>",
      "<div id='vs-llm-llm-hint' style='margin-top:8px;font-size:13px;color:#475569'></div>",
      "<div id='vs-llm-warning' style='display:none;margin-top:10px;padding:10px 12px;border:1px solid #f59e0b;background:#fef3c7;color:#92400e;font-size:13px'></div>",
      "<div style='display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-top:12px'>",
      "  <button id='vs-llm-play-pause' type='button' style='display:none;padding:7px 12px'>Pause</button>",
      "  <button id='vs-llm-reset' type='button' style='padding:7px 12px'>Restart Game</button>",
      "  <button id='vs-llm-move-now' type='button' style='padding:7px 12px'>Let LLM Move</button>",
      "</div>",
      "<div id='vs-llm-status' style='margin-top:10px;font-size:14px;color:#1f2937'></div>",
      "<div id='vs-llm-code-modal' style='display:none;position:fixed;inset:0;z-index:9999;background:rgba(15,23,42,0.65);align-items:center;justify-content:center;padding:24px'>",
      "  <div style='width:min(960px,100%);max-height:85vh;background:#ffffff;border:1px solid #cbd5e1;box-shadow:0 20px 50px rgba(15,23,42,0.25);display:flex;flex-direction:column'>",
      "    <div style='display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid #e2e8f0;background:#f8fafc'>",
      "      <div id='vs-llm-code-modal-title' style='font-size:15px;font-weight:600;color:#0f172a'>Strategy Code</div>",
      "      <button id='vs-llm-code-modal-close' type='button' style='padding:6px 10px'>Close</button>",
      "    </div>",
      "    <div id='vs-llm-code-modal-body' style='overflow:auto;background:#0f172a;color:#e2e8f0;font-size:12px;line-height:1.5;flex:1'></div>",
      "  </div>",
      "</div>",
      "</div>",
    ].join("");

    stateholder.parentNode.insertBefore(panel, stateholder);
    app.panelNode = panel;
    app.statusNode = panel.querySelector("#vs-llm-status");
    app.roleSelect = panel.querySelector("#vs-llm-human-role");
    app.humanBotSelect = panel.querySelector("#vs-llm-human-bot");
    app.llmBotASelect = panel.querySelector("#vs-llm-bot-a");
    app.llmBotBSelect = panel.querySelector("#vs-llm-bot-b");
    app.humanBotCodeButton = panel.querySelector("#vs-llm-human-bot-code");
    app.llmBotACodeButton = panel.querySelector("#vs-llm-bot-a-code");
    app.llmBotBCodeButton = panel.querySelector("#vs-llm-bot-b-code");
    app.modeInputs = Array.prototype.slice.call(panel.querySelectorAll("input[name='vs-llm-mode']"));
    app.humanControlsNode = panel.querySelector("#vs-llm-human-controls");
    app.llmVsLlmControlsNode = panel.querySelector("#vs-llm-llm-controls");
    app.llmVsLlmSpeedNode = panel.querySelector("#vs-llm-speed-controls");
    app.llmVsLlmHintNode = panel.querySelector("#vs-llm-llm-hint");
    app.llmBotALabelNode = panel.querySelector("#vs-llm-bot-a-label");
    app.llmBotBLabelNode = panel.querySelector("#vs-llm-bot-b-label");
    app.llmVsLlmSpeedSlider = panel.querySelector("#vs-llm-speed-slider");
    app.llmVsLlmSpeedValueNode = panel.querySelector("#vs-llm-speed-value");
    app.playPauseButton = panel.querySelector("#vs-llm-play-pause");
    app.resetButton = panel.querySelector("#vs-llm-reset");
    app.moveNowButton = panel.querySelector("#vs-llm-move-now");
    app.gameStatsNode = panel.querySelector("#vs-llm-game-stats");
    app.warningNode = panel.querySelector("#vs-llm-warning");
    app.codeModalNode = panel.querySelector("#vs-llm-code-modal");
    app.codeModalTitleNode = panel.querySelector("#vs-llm-code-modal-title");
    app.codeModalContentNode = panel.querySelector("#vs-llm-code-modal-body");
    app.codeModalCloseButton = panel.querySelector("#vs-llm-code-modal-close");
    installCodeButtonHover(app.humanBotCodeButton);
    installCodeButtonHover(app.llmBotACodeButton);
    installCodeButtonHover(app.llmBotBCodeButton);
    updateSpeedUi();
    renderGameStats();
    updateSelectionWarning();
    updateCodeButtons();

    app.modeInputs.forEach(function (input) {
      input.addEventListener("change", function () {
        void handleControlsChange({ restartOnBotChange: true });
      });
    });
    app.roleSelect.addEventListener("change", function () {
      void handleControlsChange({ restartOnBotChange: false });
    });
    app.humanBotSelect.addEventListener("change", function () {
      void handleControlsChange({ restartOnBotChange: true });
    });
    app.llmBotASelect.addEventListener("change", function () {
      void handleControlsChange({ restartOnBotChange: true });
    });
    app.llmBotBSelect.addEventListener("change", function () {
      void handleControlsChange({ restartOnBotChange: true });
    });
    app.llmVsLlmSpeedSlider.addEventListener("input", function () {
      app.llmVsLlmDelayMs = sliderSpeedToDelayMs(app.llmVsLlmSpeedSlider.value);
      updateSpeedUi();
      if (app.matchMode === "llm_vs_llm" && app.autoMoveTimer !== null && !app.llmThinking) {
        scheduleMaybeAutoMove(currentAutoMoveDelayMs());
      }
    });
    app.playPauseButton.addEventListener("click", function () {
      app.llmVsLlmPlaying = !app.llmVsLlmPlaying;
      if (!app.llmVsLlmPlaying && app.autoMoveTimer !== null) {
        window.clearTimeout(app.autoMoveTimer);
        app.autoMoveTimer = null;
      }
      updatePlayPauseUi();
      if (app.llmVsLlmPlaying) {
        scheduleMaybeAutoMove(currentAutoMoveDelayMs());
      }
    });
    app.resetButton.addEventListener("click", function () {
      if (typeof window.initialize === "function") {
        window.initialize();
      }
    });
    app.moveNowButton.addEventListener("click", function () {
      scheduleMaybeAutoMove(0, true);
    });
    app.humanBotCodeButton.addEventListener("click", function () {
      void openBotCode(app.humanVsBot);
    });
    app.llmBotACodeButton.addEventListener("click", function () {
      void openBotCode(app.llmVsLlmBotA);
    });
    app.llmBotBCodeButton.addEventListener("click", function () {
      void openBotCode(app.llmVsLlmBotB);
    });
    app.codeModalCloseButton.addEventListener("click", function () {
      closeCodeModal();
    });
    app.codeModalNode.addEventListener("click", function (event) {
      if (event.target === app.codeModalNode) {
        closeCodeModal();
      }
    });
    window.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && app.codeModalNode && app.codeModalNode.style.display !== "none") {
        closeCodeModal();
      }
    });

    app.controlsMounted = true;
  }

  async function loadManifest() {
    var loaded = await Promise.all([
      fetchJson(MANIFEST_URL),
      fetchJson(GAME_STATS_URL).catch(function () {
        return {};
      }),
    ]);
    var manifest = loaded[0];
    var gameStatsManifest = loaded[1];
    app.manifest = manifest || {};
    app.gameStatsManifest = gameStatsManifest || {};
    app.bots = Array.isArray(app.manifest[window.game]) ? app.manifest[window.game] : [];
    app.botsById = Object.create(null);
    app.botsByRouteKey = Object.create(null);
    app.gameStatsByBotId = app.gameStatsManifest[window.game] || {};
    app.bots.forEach(function (bot) {
      bot.route_model_slug = String(bot.route_model_slug || "");
      bot.route_run_slug = String(bot.route_run_slug || bot.run_id || "");
      bot.route_key = String(bot.route_key || (bot.route_model_slug + "/" + bot.route_run_slug));
      bot.requires_legal_moves = Boolean(bot.requires_legal_moves);
      bot.no_blame_score = String(bot.no_blame_score || "");
      app.botsById[bot.bot_id] = bot;
      app.botsByRouteKey[bot.route_key] = bot;
    });
    refreshBotOptions();
    renderGameStats();
  }

  function applyInitialConfig() {
    var params = new URLSearchParams(window.location.search || "");
    var modeParam = params.get("mode");
    if (modeParam === "llm_vs_llm" && supportsLlmVsLlm()) {
      app.matchMode = "llm_vs_llm";
    } else if (modeParam === "human_vs_llm") {
      app.matchMode = "human_vs_llm";
    } else if (CONFIG.defaultMode === "llm_vs_llm" && supportsLlmVsLlm()) {
      app.matchMode = "llm_vs_llm";
    } else {
      app.matchMode = "human_vs_llm";
    }
    app.humanVsBot = getBotByRouteKey(params.get("bot") || CONFIG.defaultHumanBotRoute);
    app.llmVsLlmBotA = getBotByRouteKey(params.get("a") || CONFIG.defaultLlmBotARoute);
    app.llmVsLlmBotB = getBotByRouteKey(params.get("b") || CONFIG.defaultLlmBotBRoute);
    var rankedDefaultBots = rankBotsForDefaultSelection();
    if (!app.humanVsBot && rankedDefaultBots.length) {
      app.humanVsBot = rankedDefaultBots[0];
    }
    if (!app.llmVsLlmBotA && rankedDefaultBots.length) {
      app.llmVsLlmBotA = rankedDefaultBots[0];
    }
    if (!app.llmVsLlmBotB && rankedDefaultBots.length) {
      app.llmVsLlmBotB = rankedDefaultBots.find(function (bot) {
        return !app.llmVsLlmBotA || bot.bot_id !== app.llmVsLlmBotA.bot_id;
      }) || rankedDefaultBots[0];
    }
    app.llmVsLlmDelayMs = DEFAULT_LLM_VS_LLM_DELAY_MS;
    var delayParam = Number(params.get("delay"));
    if (!Number.isNaN(delayParam) && delayParam >= MIN_LLM_VS_LLM_DELAY_MS && delayParam <= MAX_LLM_VS_LLM_DELAY_MS) {
      app.llmVsLlmDelayMs = delayParam;
    }
    refreshBotOptions();
    updateSpeedUi();
    updateModeUi();
    var requestedHumanRole = params.get("role");
    if (requestedHumanRole && app.roleSelect) {
      var roleOptions = getRoles();
      if (roleOptions.indexOf(requestedHumanRole) >= 0) {
        app.roleSelect.value = requestedHumanRole;
        app.humanRole = requestedHumanRole;
      }
    }
    syncBrowserRoute();
  }

  async function ensureBotLoaded(bot) {
    if (!bot) {
      return;
    }
    if (app.loadedBotIds[bot.bot_id]) {
      return;
    }
    setStatus("Loading " + bot.label + " in Pyodide...", "loading");
    try {
      var source = await fetchText("/" + bot.source_path);
      await workerRequest("init", {}, LOAD_TIMEOUT_MS);
      await workerRequest(
        "loadBot",
        {
          botId: bot.bot_id,
          source: source,
        },
        LOAD_TIMEOUT_MS
      );
      app.loadedBotIds[bot.bot_id] = true;
    } catch (error) {
      throw new Error(bot.label + " failed to load: " + normalizeError(error));
    }
  }

  function selectedBotsToLoad() {
    var seen = Object.create(null);
    var selected = [];
    function addBot(bot) {
      if (!bot || seen[bot.bot_id]) {
        return;
      }
      seen[bot.bot_id] = true;
      selected.push(bot);
    }
    if (app.matchMode === "human_vs_llm") {
      addBot(app.humanVsBot);
      return selected;
    }
    addBot(app.llmVsLlmBotA);
    addBot(app.llmVsLlmBotB);
    return selected;
  }

  async function handleControlsChange(options) {
    var settings = options || {};
    app.selectionRevision += 1;
    var revision = app.selectionRevision;
    var previousSelectionSignature = selectionSignature();
    readSelectionsFromInputs();
    updateModeUi();
    syncBrowserRoute();
    updateActionChooser();
    renderGameStats();
    updateSelectionWarning();

    try {
      var botsToLoad = selectedBotsToLoad();
      for (var index = 0; index < botsToLoad.length; index += 1) {
        await ensureBotLoaded(botsToLoad[index]);
        if (revision !== app.selectionRevision) {
          return;
        }
      }
      if (revision !== app.selectionRevision) {
        return;
      }
      if (settings.restartOnBotChange && previousSelectionSignature !== selectionSignature()) {
        if (typeof window.initialize === "function") {
          window.initialize();
        }
      }
      setStatus(buildReadyStatus(), "ready");
      updateActionChooser();
      renderGameStats();
      updateSelectionWarning();
      scheduleMaybeAutoMove(currentAutoMoveDelayMs());
    } catch (error) {
      if (revision !== app.selectionRevision) {
        return;
      }
      setStatus("Failed to load selected LLM: " + normalizeError(error), "error");
      updateActionChooser();
    }
  }

  function installHooks() {
    if (app.hooksInstalled) {
      return;
    }
    app.originalInitialize = window.initialize;
    app.originalPerform = window.perform;
    app.originalUp = window.up;
    app.originalDn = window.dn;

    window.initialize = function () {
      var result = app.originalInitialize.apply(this, arguments);
      app.llmThinking = false;
      refreshRoleOptions();
      updateModeUi();
      setStatus(buildReadyStatus(), "ready");
      updateActionChooser();
      renderGameStats();
      updateSelectionWarning();
      scheduleMaybeAutoMove(currentAutoMoveDelayMs());
      return result;
    };

    window.perform = function () {
      var result = app.originalPerform.apply(this, arguments);
      updateActionChooser();
      renderGameStats();
      updateSelectionWarning();
      scheduleMaybeAutoMove(currentAutoMoveDelayMs());
      return result;
    };

    window.up = function () {
      var result = app.originalUp.apply(this, arguments);
      updateActionChooser();
      return result;
    };

    window.dn = function () {
      var result = app.originalDn.apply(this, arguments);
      updateActionChooser();
      return result;
    };

    app.hooksInstalled = true;
  }

  function scheduleMaybeAutoMove(delayMs, force) {
    if (app.autoMoveTimer !== null) {
      window.clearTimeout(app.autoMoveTimer);
    }
    if (!force && app.matchMode === "llm_vs_llm" && !app.llmVsLlmPlaying) {
      app.autoMoveTimer = null;
      return;
    }
    app.autoMoveTimer = window.setTimeout(function () {
      app.autoMoveTimer = null;
      void maybeAutoMove(Boolean(force));
    }, typeof delayMs === "number" ? delayMs : 0);
  }

  async function maybeAutoMove(force) {
    if (app.llmThinking) {
      return;
    }
    if (!force && app.matchMode === "llm_vs_llm" && !app.llmVsLlmPlaying) {
      updateActionChooser();
      return;
    }
    if (!isLatestPosition()) {
      setStatus("Navigate back to the latest position before letting an LLM move.", "error");
      updateActionChooser();
      return;
    }
    if (isTerminalState()) {
      setStatus("Game over.", "ready");
      updateActionChooser();
      return;
    }

    var control = currentControlRole();
    if (!control) {
      setStatus("This page does not expose a single control role.", "error");
      updateActionChooser();
      return;
    }
    if (!force && app.matchMode === "human_vs_llm" && control === app.humanRole) {
      updateActionChooser();
      return;
    }

    var bot = automatedBotForRole(control);
    if (!bot) {
      if (app.matchMode === "llm_vs_llm") {
        setStatus("Choose an LLM for " + control + " to continue.", "error");
      }
      updateActionChooser();
      return;
    }

    app.llmThinking = true;
    updateActionChooser();
    setStatus(bot.label + " is choosing a move for " + control + "...", "loading");

    try {
      await ensureBotLoaded(bot);
      var response = await workerRequest(
        "getMove",
        {
          botId: bot.bot_id,
          state: deepCopyState(),
          role: control,
          legalMoves: bot.requires_legal_moves ? currentLegalMoveStrings() : [],
        },
        MOVE_TIMEOUT_MS
      );
      var moveText = response && typeof response.move === "string" ? response.move.trim() : "";
      if (!moveText) {
        throw new Error(bot.label + " returned an empty move");
      }
      var actionTerm = window.read(moveText);
      if (!window.findlegalp(actionTerm, window.state, window.library)) {
        throw new Error(bot.label + " returned an illegal move: " + moveText);
      }
      setStatus(bot.label + " played " + moveText, "ready");
      app.originalPerform(actionTerm);
      updateActionChooser();
      scheduleMaybeAutoMove(currentAutoMoveDelayMs());
    } catch (error) {
      setStatus(bot.label + " failed: " + normalizeError(error), "error");
      updateActionChooser();
    } finally {
      app.llmThinking = false;
      updateActionChooser();
    }
  }

  async function initializeVsLlmPage() {
    buildPanel();
    installHooks();
    refreshRoleOptions();
    updateModeUi();
    updateActionChooser();
    setStatus("Loading available Stanford example bots...", "loading");
    try {
      await loadManifest();
      if (!app.bots.length) {
        setStatus("No Stanford example bots were found for " + window.game + ".", "error");
        return;
      }
      applyInitialConfig();
      await handleControlsChange();
    } catch (error) {
      setStatus("Failed to load VS_LLM manifest: " + normalizeError(error), "error");
    }
  }

  window.addEventListener("load", function () {
    void initializeVsLlmPage();
  });
})();
