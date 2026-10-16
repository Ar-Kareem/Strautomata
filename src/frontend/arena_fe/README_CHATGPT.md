# STOP: Check Node Before Running npm

If `npm run start` fails with old JS syntax errors (`Unexpected token ...`), Node is probably coming from conda (`v6`) instead of nvm (`v22`).

## Always do this first

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
export PATH="$NVM_DIR/versions/node/v22.22.0/bin:$PATH"
hash -r

which node
node -v
which npm
npm -v
```

Expected:
- `node` points to `~/.nvm/versions/node/v22.22.0/bin/node`
- `node -v` is `v22.22.0`

## Start dev server

```bash
npm run start -- --port 4199
```

Notes:
- Project `start` script already sets a default port, so passing another port can print a duplicate-port warning. That is normal; the last one wins.
- If you see `listen EPERM ...:4199`, that is environment/sandbox port-binding permission, not an app compile error.

## Quick compile check (no server bind)

```bash
npx ng build --configuration development
```
