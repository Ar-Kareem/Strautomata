"use strict";

(function () {
  var LOCAL_PYODIDE_BASE = new URL("pyodide/", self.location.href).toString();
  var CDN_PYODIDE_BASE = "https://cdn.jsdelivr.net/pyodide/v0.26.2/full/";
  var pyodidePromise = null;
  var activeBaseUrl = null;

  function postStatus(tone, message) {
    self.postMessage({ kind: "status", tone: tone, message: message });
  }

  function postResponse(id, ok, data, error) {
    if (ok) {
      self.postMessage({ kind: "response", id: id, ok: true, data: data });
      return;
    }
    self.postMessage({ kind: "response", id: id, ok: false, error: error || "Unknown error" });
  }

  function normalizeError(error) {
    if (error && typeof error.message === "string" && error.message.trim()) {
      return error.message.trim();
    }
    if (error instanceof Error) {
      return error.stack || error.message;
    }
    return String(error);
  }

  function tryImportPyodide(baseUrl) {
    self.importScripts(baseUrl + "pyodide.js");
    return baseUrl;
  }

  async function initPyodide(preferredBaseUrl) {
    postStatus("loading", "Loading Pyodide runtime");
    var loadBase = preferredBaseUrl || null;
    if (typeof self.loadPyodide !== "function") {
      var candidates = [];
      if (loadBase) {
        candidates.push(loadBase);
      }
      if (!candidates.includes(LOCAL_PYODIDE_BASE)) {
        candidates.push(LOCAL_PYODIDE_BASE);
      }
      if (!candidates.includes(CDN_PYODIDE_BASE)) {
        candidates.push(CDN_PYODIDE_BASE);
      }

      var lastError = null;
      for (var i = 0; i < candidates.length; i += 1) {
        var candidate = candidates[i];
        try {
          loadBase = tryImportPyodide(candidate);
          break;
        } catch (error) {
          lastError = error;
        }
      }
      if (typeof self.loadPyodide !== "function") {
        throw new Error("Failed to load Pyodide loader: " + normalizeError(lastError));
      }
    }

    if (!loadBase) {
      loadBase = preferredBaseUrl || CDN_PYODIDE_BASE;
    }
    activeBaseUrl = loadBase;
    var pyodide = await self.loadPyodide({ indexURL: loadBase });
    await pyodide.runPythonAsync(
      [
        "import inspect",
        "import traceback",
        "_VS_LLM_BOTS = {}",
        "def _vs_llm_load_bot(bot_id, source):",
        "    try:",
        "        namespace = {}",
        "        exec(source, namespace)",
        "        policy = namespace.get('policy')",
        "        if not callable(policy):",
        "            raise RuntimeError('Bot must define callable policy(state, role)')",
        "        _VS_LLM_BOTS[bot_id] = policy",
        "    except Exception as exc:",
        "        raise RuntimeError(traceback.format_exc()) from exc",
        "",
        "def _vs_llm_call_bot(bot_id, state, role, legal_moves):",
        "    try:",
        "        policy = _VS_LLM_BOTS[bot_id]",
        "        try:",
        "            signature = inspect.signature(policy)",
        "            positional = [",
        "                parameter",
        "                for parameter in signature.parameters.values()",
        "                if parameter.kind in (",
        "                    inspect.Parameter.POSITIONAL_ONLY,",
        "                    inspect.Parameter.POSITIONAL_OR_KEYWORD,",
        "                )",
        "            ]",
        "            has_varargs = any(",
        "                parameter.kind == inspect.Parameter.VAR_POSITIONAL",
        "                for parameter in signature.parameters.values()",
        "            )",
        "            if len(positional) >= 3 or has_varargs:",
        "                return policy(state, role, legal_moves)",
        "            if len(positional) >= 2:",
        "                return policy(state, role)",
        "            return policy(state)",
        "        except ValueError:",
        "            return policy(state, role, legal_moves)",
        "    except Exception as exc:",
        "        raise RuntimeError(traceback.format_exc()) from exc",
      ].join("\n")
    );
    postStatus("ready", "Pyodide ready");
    return pyodide;
  }

  async function ensurePyodide(preferredBaseUrl) {
    if (!pyodidePromise) {
      pyodidePromise = initPyodide(preferredBaseUrl);
    }
    return pyodidePromise;
  }

  async function loadBot(botId, source, preferredBaseUrl) {
    var pyodide = await ensurePyodide(preferredBaseUrl);
    pyodide.globals.set("VS_LLM_BOT_ID", botId);
    pyodide.globals.set("VS_LLM_BOT_SOURCE", source);
    try {
      await pyodide.runPythonAsync("_vs_llm_load_bot(VS_LLM_BOT_ID, VS_LLM_BOT_SOURCE)");
    } finally {
      pyodide.globals.delete("VS_LLM_BOT_ID");
      pyodide.globals.delete("VS_LLM_BOT_SOURCE");
    }
    return { bot_id: botId, base_url: activeBaseUrl };
  }

  async function getMove(botId, state, role, legalMoves, preferredBaseUrl) {
    var pyodide = await ensurePyodide(preferredBaseUrl);
    var stateProxy = pyodide.toPy(state);
    var legalMovesProxy = pyodide.toPy(legalMoves || []);
    pyodide.globals.set("VS_LLM_STATE", stateProxy);
    pyodide.globals.set("VS_LLM_ROLE", role);
    pyodide.globals.set("VS_LLM_LEGAL_MOVES", legalMovesProxy);
    pyodide.globals.set("VS_LLM_BOT_ID", botId);
    try {
      var result = await pyodide.runPythonAsync(
        "_vs_llm_call_bot(VS_LLM_BOT_ID, VS_LLM_STATE, VS_LLM_ROLE, VS_LLM_LEGAL_MOVES)"
      );
      var move = result && typeof result.toJs === "function" ? result.toJs() : result;
      if (result && typeof result.destroy === "function") {
        result.destroy();
      }
      return { move: String(move || "").trim() };
    } finally {
      if (stateProxy && typeof stateProxy.destroy === "function") {
        stateProxy.destroy();
      }
      if (legalMovesProxy && typeof legalMovesProxy.destroy === "function") {
        legalMovesProxy.destroy();
      }
      pyodide.globals.delete("VS_LLM_STATE");
      pyodide.globals.delete("VS_LLM_ROLE");
      pyodide.globals.delete("VS_LLM_LEGAL_MOVES");
      pyodide.globals.delete("VS_LLM_BOT_ID");
    }
  }

  self.onmessage = function (event) {
    var message = event.data || {};
    var id = message.id;
    Promise.resolve()
      .then(async function () {
        if (message.type === "init") {
          var pyodide = await ensurePyodide(message.pyodideBaseUrl || null);
          return { ready: Boolean(pyodide), base_url: activeBaseUrl };
        }
        if (message.type === "loadBot") {
          return await loadBot(
            String(message.botId || ""),
            String(message.source || ""),
            message.pyodideBaseUrl || null
          );
        }
        if (message.type === "getMove") {
          return await getMove(
            String(message.botId || ""),
            message.state || [],
            String(message.role || ""),
            Array.isArray(message.legalMoves) ? message.legalMoves : [],
            message.pyodideBaseUrl || null
          );
        }
        throw new Error("Unknown worker message type: " + message.type);
      })
      .then(function (data) {
        postResponse(id, true, data, null);
      })
      .catch(function (error) {
        postResponse(id, false, null, normalizeError(error));
      });
  };
})();
