#!/usr/bin/env node
// Warns (never fails) when public/history/ is out of date:
//  - WEBSITE_PKL in the repo's .env names a different pickle than the export used
//  - an input of the export (pickle, matches JSON) changed since sources.json was written
//  - public/history/replays/ does not match replays.lock.json
// replays/ is gitignored: it is written by src/frontend/export_history.py and published as a
// release asset of the public repo. Hash rule mirrors tree_hash() in src/frontend/replay_format.py.
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const REPO = path.join(__dirname, '..', '..', '..', '..');
const HISTORY = path.join(__dirname, '..', 'public', 'history');
const REPLAYS = path.join(HISTORY, 'replays');
const LOCK = path.join(HISTORY, 'replays.lock.json');
const SOURCES = path.join(HISTORY, 'sources.json');
const RELEASES = 'https://github.com/Ar-Kareem/Strautomata/releases';
const EXPORT_CMD = 'cd src && python -m frontend.export_history --out frontend/arena_fe/public/';

const sha256 = (data) => crypto.createHash('sha256').update(data).digest('hex');
const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));

function treeHash(root) {
  const lines = [];
  const walk = (dir) => {
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()) {
        walk(full);
      } else if (ent.isFile()) {
        const rel = path.relative(root, full).split(path.sep).join('/');
        lines.push(`${rel}\0${sha256(fs.readFileSync(full))}\n`);
      }
    }
  };
  walk(root);
  return sha256(lines.sort().join('')).slice(0, 16);
}

function fileSha256(file) {
  const hash = crypto.createHash('sha256');
  const fd = fs.openSync(file, 'r');
  const buf = Buffer.alloc(1 << 24);
  try {
    let n;
    while ((n = fs.readSync(fd, buf, 0, buf.length, null)) > 0) {
      hash.update(buf.subarray(0, n));
    }
  } finally {
    fs.closeSync(fd);
  }
  return hash.digest('hex');
}

function envValue(key) {
  const file = path.join(REPO, '.env');
  if (!fs.existsSync(file)) {
    return null;
  }
  for (const line of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (m && m[1] === key) {
      return m[2].replace(/^(['"])(.*)\1$/, '$2');
    }
  }
  return null;
}

/** null when the file is unchanged or absent (clones without results), else why it differs.
 * mtime+size first, sha256 only on mismatch. */
function changed(fp) {
  const file = path.resolve(REPO, fp.path);
  if (!fs.existsSync(file)) {
    return null;
  }
  const st = fs.statSync(file, { bigint: true });
  if (st.size.toString() === String(fp.size) && st.mtimeNs.toString() === fp.mtime_ns) {
    return null;
  }
  return fileSha256(file) === fp.sha256 ? null : 'changed';
}

function sourceProblems() {
  if (!fs.existsSync(SOURCES)) {
    return [];
  }
  const sources = readJson(SOURCES);
  const problems = [];
  const pinned = envValue('WEBSITE_PKL');
  if (pinned && path.resolve(REPO, pinned) !== path.resolve(REPO, sources.pkl.path)) {
    problems.push(`.env WEBSITE_PKL is ${pinned}, but the export used ${sources.pkl.path}`);
  } else {
    const why = changed(sources.pkl);
    if (why) {
      problems.push(`${sources.pkl.path} ${why} since the export`);
    }
  }
  for (const [game, inputs] of Object.entries(sources.games)) {
    for (const fp of inputs) {
      const why = changed(fp);
      if (why) {
        problems.push(`${game}: ${path.basename(fp.path)} ${why} since the export`);
      }
    }
  }
  return problems;
}

function replayProblem() {
  if (!fs.existsSync(LOCK)) {
    return null;
  }
  const { hash } = readJson(LOCK);
  const problem = !fs.existsSync(REPLAYS) ? 'are missing' : treeHash(REPLAYS) !== hash ? 'do not match replays.lock.json' : null;
  if (!problem) {
    return null;
  }
  return [
    `Match replay files ${problem} (expected replays-${hash}).`,
    '  The Match Viewer will list matches but cannot open their replays.',
    '  Re-run the export, or download the asset from',
    `  ${RELEASES}/tag/replays-${hash}`,
    `  and extract it into ${path.relative(process.cwd(), HISTORY) || '.'}/`
  ].join('\n');
}

const stale = sourceProblems();
const replays = replayProblem();
if (stale.length || replays) {
  const lines = ['', 'WARNING: website data is out of date.'];
  if (stale.length) {
    lines.push('Results on disk differ from the exported history:', ...stale.map((s) => `  ${s}`));
  }
  if (replays) {
    lines.push(replays);
  }
  lines.push(`Re-export with: ${EXPORT_CMD}`, '');
  console.warn(lines.join('\n'));
}
