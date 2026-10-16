#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const readline = require("readline");
const vm = require("vm");

function usage() {
  console.error(
    "Usage: node stanford_gamemaster_engine.js <rules_path> [epilog_js_path]"
  );
}

const rulesPath = process.argv[2];
const epilogPath =
  process.argv[3] ||
  path.resolve(path.dirname(rulesPath || "."), "..", "assets", "epilog.js");

if (!rulesPath) {
  usage();
  process.exit(2);
}

if (!fs.existsSync(rulesPath)) {
  console.error(`Rules file not found: ${rulesPath}`);
  process.exit(2);
}

if (!fs.existsSync(epilogPath)) {
  console.error(`Stanford epilog.js not found: ${epilogPath}`);
  process.exit(2);
}

vm.runInThisContext(fs.readFileSync(epilogPath, "utf8"), { filename: epilogPath });

indexing = false;
dataindexing = false;
ruleindexing = true;

let library = [];
let roles = [];
let state = [];
let moveHistory = [];

function simulate(move, currentState, rules) {
  const deltas = compexpand(move, currentState, rules);
  const additions = [];
  const deletions = [];
  for (let i = 0; i < deltas.length; i += 1) {
    if (symbolp(deltas[i])) {
      additions.push(deltas[i]);
      continue;
    }
    if (deltas[i][0] === "not") {
      deletions.push(deltas[i][1]);
      continue;
    }
    additions.push(deltas[i]);
  }
  const newState = [];
  for (let i = 0; i < currentState.length; i += 1) {
    if (find(currentState[i], additions)) {
      continue;
    }
    if (find(currentState[i], deletions)) {
      continue;
    }
    newState.push(currentState[i]);
  }
  return newState.concat(additions);
}

function findroles(rules) {
  return compfinds("R", seq("role", "R"), seq(), rules);
}

function findinits(rules) {
  return compfinds("P", seq("init", "P"), seq(), rules);
}

function findcontrol(facts, rules) {
  return compfindx("X", seq("control", "X"), facts, rules);
}

function findlegalp(move, facts, rules) {
  return compfindp(seq("legal", move), facts, rules);
}

function findlegals(facts, rules) {
  return compfinds("X", seq("legal", "X"), facts, rules);
}

function findlegalx(facts, rules) {
  return compfindx("X", seq("legal", "X"), facts, rules);
}

function findreward(role, facts, rules) {
  const value = compfindx("R", seq("goal", role, "R"), facts, rules);
  if (value) {
    return value;
  }
  return 0;
}

function findterminalp(facts, rules) {
  return compfindp("terminal", facts, rules);
}

function findindices(rules) {
  return compfinds("I", seq("index", "I"), seq(), rules).map((value) => jsonAtom(value));
}

function sortStrings(values) {
  return values.slice().sort((left, right) => left.localeCompare(right));
}

function normalizeScore(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : value;
}

function jsonAtom(value) {
  if (typeof value !== "string") {
    return value;
  }
  if (/^-?\d+$/.test(value)) {
    return Number(value);
  }
  return value;
}

function rawJsonTerm(term) {
  if (symbolp(term)) {
    return term;
  }
  return term.map((item) => rawJsonTerm(item));
}

function jsonTerm(term) {
  if (symbolp(term)) {
    return jsonAtom(term);
  }
  return term.map((item) => jsonTerm(item));
}

function buildRelations(facts) {
  const relations = {};
  for (const fact of facts) {
    const term = jsonTerm(fact);
    if (Array.isArray(term)) {
      const relation = String(term[0]);
      const args = term.slice(1);
      if (!relations[relation]) {
        relations[relation] = [];
      }
      relations[relation].push(args);
      continue;
    }
    const relation = String(term);
    if (!relations[relation]) {
      relations[relation] = [];
    }
    relations[relation].push([]);
  }
  return relations;
}

function sortedNumericOrString(values) {
  return values.slice().sort((left, right) => {
    if (typeof left === "number" && typeof right === "number") {
      return left - right;
    }
    return String(left).localeCompare(String(right));
  });
}

function buildCellData(relations, indexValues = []) {
  const cells = relations.cell;
  if (!Array.isArray(cells) || cells.length === 0) {
    return null;
  }
  const arities = new Set(cells.map((args) => args.length));
  if (arities.size !== 1) {
    return null;
  }
  const arity = cells[0].length;
  if (arity < 3) {
    return null;
  }
  const xs = [];
  const ys = [];
  const values = {};
  for (const args of cells) {
    const [x, y, value] = args;
    xs.push(x);
    ys.push(y);
    values[`${x},${y}`] = value;
  }
  const domain = sortedNumericOrString([...new Set(indexValues)]);
  const xValues = domain.length > 0 ? domain : sortedNumericOrString([...new Set(xs)]);
  const yValues = domain.length > 0 ? domain : sortedNumericOrString([...new Set(ys)]);
  const rowsTopDown = yValues
    .slice()
    .reverse()
    .map((y) => xValues.map((x) => (Object.prototype.hasOwnProperty.call(values, `${x},${y}`) ? values[`${x},${y}`] : null)));
  return {
    relation: "cell",
    arity,
    x_values: xValues,
    y_values: yValues,
    by_coord: values,
    rows_top_down: rowsTopDown,
  };
}

function snapshot(includeLegals = true) {
  const terminal = Boolean(findterminalp(state, library));
  const control = terminal ? null : findcontrol(state, library);
  const scores = {};
  for (const role of roles) {
    scores[String(role)] = normalizeScore(findreward(role, state, library));
  }
  const stateTerms = state.map((fact) => rawJsonTerm(fact));
  const stateFacts = sortStrings(state.map((fact) => grind(fact)));
  const legalMoves =
    !includeLegals || terminal
      ? null
      : sortStrings(findlegals(state, library).map((move) => grind(move)));
  return {
    roles: roles.map((role) => String(role)),
    control: control === false || control == null ? null : String(control),
    terminal,
    legal_moves: legalMoves,
    state: stateTerms,
    state_facts: stateFacts,
    scores,
    move_history: moveHistory.slice(),
  };
}

function reset() {
  library = [];
  definerules(library, readdata(fs.readFileSync(rulesPath, "utf8")));
  roles = findroles(library);
  state = findinits(library);
  moveHistory = [];
}

function reply(payload) {
  process.stdout.write(JSON.stringify(payload) + "\n");
}

function handleApply(moveText) {
  if (findterminalp(state, library)) {
    return reply({ ok: false, error: "Game is already terminal.", snapshot: snapshot(false) });
  }
  if (typeof moveText !== "string" || moveText.trim() === "") {
    return reply({ ok: false, error: "apply requires a non-empty move string." });
  }
  let move;
  try {
    move = read(moveText);
  } catch (error) {
    return reply({ ok: false, error: `Could not parse move: ${moveText}` });
  }
  if (!findlegalp(move, state, library)) {
    return reply({ ok: false, error: `Illegal move: ${moveText}`, snapshot: snapshot(false) });
  }
  state = simulate(move, state, library);
  moveHistory.push(moveText);
  return reply({ ok: true, snapshot: snapshot(false) });
}

reset();

const rl = readline.createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

rl.on("line", (line) => {
  if (!line.trim()) {
    return;
  }
  let request;
  try {
    request = JSON.parse(line);
  } catch (error) {
    return reply({ ok: false, error: `Invalid JSON request: ${error.message}` });
  }
  switch (request.cmd) {
    case "meta":
      return reply({
        ok: true,
        roles: roles.map((role) => String(role)),
        rules_path: path.resolve(rulesPath),
        epilog_path: path.resolve(epilogPath),
      });
    case "snapshot":
      return reply({
        ok: true,
        snapshot: snapshot(Boolean(request.include_legals)),
      });
    case "legalx": {
      if (findterminalp(state, library)) {
        return reply({ ok: true, move: null });
      }
      const move = findlegalx(state, library);
      return reply({
        ok: true,
        move: move === false || move == null ? null : grind(move),
      });
    }
    case "apply":
      return handleApply(request.move);
    case "reset":
      reset();
      return reply({ ok: true, snapshot: snapshot(false) });
    case "quit":
      reply({ ok: true });
      process.exit(0);
      return;
    default:
      return reply({ ok: false, error: `Unknown command: ${request.cmd}` });
  }
});
