const fs = require('fs');
const path = require('path');
const { loadModelBlacklist, modelOfExamplePath, checkAngularIgnores } = require('./model_blacklist.cjs');
const { spawn } = require('child_process');

const arenaRoot = path.resolve(__dirname, '..');
const projectRoot = path.resolve(arenaRoot, '..', '..');
const gameArenaRoot = path.join(projectRoot, 'game_arena');
const outDir = path.join(arenaRoot, 'public', 'py');
const cacheDir = path.join(outDir, 'game_arena_cache');
const gameWorldsCacheFile = path.join(outDir, 'game_worlds.json');

const POLL_INTERVAL_MS = 3000;

const MODEL_BLACKLIST = loadModelBlacklist();
checkAngularIgnores(MODEL_BLACKLIST);

function shouldInclude(filePath) {
  const parts = filePath.split(path.sep);
  if (parts.includes('__pycache__')) {
    return false;
  }
  const basename = path.basename(filePath);
  const ext = path.extname(filePath);
  const hasExamples = parts.includes('examples');
  const rel = path.relative(projectRoot, filePath);
  const relParts = rel.split(path.sep);
  const isCloneWars = relParts[0] === 'game_arena' && relParts[1] === 'clone_wars';
  const isDrqHuman = isCloneWars && relParts.includes('drq') && relParts.includes('human_warriors');
  const isCorewarWarriors = isCloneWars && relParts.includes('corewar') && relParts.includes('warriors');
  const isCorewarGptWarriors = isCloneWars && relParts.includes('corewar') && relParts.includes('gpt_warriors');

  if (MODEL_BLACKLIST.has(modelOfExamplePath(rel))) {
    return false;
  }
  if (ext === '.py') {
    if (hasExamples) {
      return basename === '2.python_code.py';
    }
    return true;
  }

  if (basename === 'config.json' && hasExamples) {
    return true;
  }

  if (ext === '.red') {
    return isDrqHuman || isCorewarWarriors || isCorewarGptWarriors;
  }

  return false;
}

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const entryName = typeof entry === 'string' ? entry : entry.name;
    const fullPath = path.join(dir, entryName);
    const isDir = typeof entry === 'string' ? fs.statSync(fullPath).isDirectory() : entry.isDirectory();
    const isFile = typeof entry === 'string' ? fs.statSync(fullPath).isFile() : entry.isFile();
    if (isDir) {
      if (entryName === '__pycache__') {
        continue;
      }
      walk(fullPath, files);
    } else if (isFile) {
      if (shouldInclude(fullPath)) {
        files.push(fullPath);
      }
    }
  }
  return files;
}

function toRelative(filePath) {
  return path.relative(projectRoot, filePath).split(path.sep).join('/');
}

function buildEntries(files) {
  return files
    .map((filePath) => ({ absPath: filePath, relPath: toRelative(filePath) }))
    .sort((a, b) => a.relPath.localeCompare(b.relPath));
}

function getGameId(relPath) {
  if (!relPath.startsWith('game_arena/')) {
    return null;
  }
  const parts = relPath.split('/');
  if (parts.length < 3) {
    return null;
  }
  return parts[1] || null;
}

function buildSignature(files) {
  return files
    .map((filePath) => {
      const stat = fs.statSync(filePath);
      return `${filePath}:${stat.size}:${stat.mtimeMs}`;
    })
    .join('|');
}

function getWorldInfo(relPath) {
  if (!relPath.startsWith('game_arena/')) {
    return null;
  }
  const parts = relPath.split('/');
  if (parts.length < 4) {
    return null;
  }
  if (parts[2] !== 'examples') {
    return null;
  }
  const gameId = parts[1];
  const worldId = parts[3];
  if (!gameId || !worldId) {
    return null;
  }
  return { gameId, worldId };
}

function writeCacheFile(targetPath, entries) {
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir);
  }
  fs.writeFileSync(
    targetPath,
    JSON.stringify({ files: entries.map((entry) => entry.relPath) }, null, 2)
  );
}

function writeGameWorlds(entries) {
  const seen = new Map();
  const configs = {};

  for (const entry of entries) {
    const info = getWorldInfo(entry.relPath);
    if (!info) {
      continue;
    }
    const key = `${info.gameId}/${info.worldId}`;
    if (!seen.has(key)) {
      seen.set(key, {
        'gameId': info.gameId,
        'worldId': info.worldId,
      });
    }
    if (entry.relPath.endsWith('/config.json')) {  // handle worlds with config
      const raw = fs.readFileSync(entry.absPath, 'utf8');
      configs[key] = {
        'gameId': info.gameId,
        'worldId': info.worldId,
        'config': raw
      }
    }
  }
  for (const [key, value] of seen.entries()) {  // handle worlds without config
    if (!(key in configs)) {
      configs[key] = {
        'gameId': value.gameId,
        'worldId': value.worldId,
        'config': null
      }
    }
  }

  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir);
  }
  fs.writeFileSync(
    gameWorldsCacheFile,
    JSON.stringify({ configs }, null, 2)
  );
  console.log(`[manifest] Updated game_worlds with ${configs.length} pairs.`);
}

function writeCaches(entries) {
  const mainEntries = [];
  const byGame = new Map();

  for (const entry of entries) {
    const gameId = getGameId(entry.relPath);
    if (gameId) {
      if (!byGame.has(gameId)) {
        byGame.set(gameId, []);
      }
      byGame.get(gameId).push(entry);
    } else {
      mainEntries.push(entry);
    }
  }

  if (mainEntries.length > 0) {  // don't need main files
    // writeCacheFile(mainCacheFile, mainEntries);
  }

  for (const [gameId, gameEntries] of byGame.entries()) {
    writeCacheFile(path.join(cacheDir, `${gameId}.json`), gameEntries);
  }

  writeGameWorlds(entries);

  console.log(
    `[manifest] Cached ${byGame.size} games and ${mainEntries.length} main files.`
  );
}

function refreshManifest(state) {
  if (!fs.existsSync(gameArenaRoot)) {
    console.error(`[manifest] game_arena not found at ${gameArenaRoot}`);
    return state;
  }
  const files = walk(gameArenaRoot);
  const signature = buildSignature(files);
  if (signature !== state.signature) {
    const entries = buildEntries(files);
    writeCaches(entries);
    return { ...state, signature };
  }
  return state;
}

function startWatcher() {
  let state = { signature: '' };
  state = refreshManifest(state);
  setInterval(() => {
    state = refreshManifest(state);
  }, POLL_INTERVAL_MS);
}

function startChild(commandArgs) {
  if (!commandArgs.length) {
    return null;
  }
  const child = spawn(commandArgs.join(' '), {
    shell: true,
    stdio: 'inherit'
  });
  return child;
}

function main() {
  const separatorIndex = process.argv.indexOf('--');
  const commandArgs = separatorIndex === -1 ? [] : process.argv.slice(separatorIndex + 1);
  const child = startChild(commandArgs);
  startWatcher();

  const shutdown = () => {
    if (child) {
      child.kill('SIGINT');
    }
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main();
