// Models excluded from the tournament (src/experimental/model_ignore.json) are kept off the site:
// their bots are left out of the game manifests here and out of the build by angular.json.
const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..', '..', '..');
const blacklistFile = path.join(projectRoot, 'experimental', 'model_ignore.json');
const angularJsonFile = path.resolve(__dirname, '..', 'angular.json');

function loadModelBlacklist() {
  const parsed = JSON.parse(fs.readFileSync(blacklistFile, 'utf8'));
  return new Set(parsed.model_ignore ?? []);
}

/** Model of a bot file like game_arena/<game>/examples/<world>/<model>/<nnn>/..., else null. */
function modelOfExamplePath(relPath) {
  const parts = relPath.split(/[\\/]/);
  return parts[0] === 'game_arena' && parts[2] === 'examples' && parts.length > 5 ? parts[4] : null;
}

/** Warn when angular.json would still copy a blacklisted model's code files into the build. */
function checkAngularIgnores(blacklist) {
  const config = fs.readFileSync(angularJsonFile, 'utf8');
  const missing = [...blacklist].filter((model) => !config.includes(`"**/examples/*/${model}/**"`));
  if (missing.length) {
    console.warn(`[manifest] angular.json asset ignores are missing blacklisted models: ${missing.join(', ')}`);
  }
}

module.exports = { loadModelBlacklist, modelOfExamplePath, checkAngularIgnores };
