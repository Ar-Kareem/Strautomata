This chess heuristic uses the Stockfish engine from the official GitHub repository:
https://github.com/official-stockfish/Stockfish

Default upstream ref:

- Tag: `sf_1.2`
- Archive URL: `https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_1.2.tar.gz`

Installer notes:

- `install_stockfish.sh` defaults to the official `sf_1.2` tag.
- To pin a specific historical commit instead, set `STOCKFISH_1_2_REF=<40-char-commit-hash>`
  before running the installer.

Local modifications:

- Added an arena-specific `passthrough.py` UCI wrapper.
- Added an installer that downloads the official source archive and compiles a local Linux binary.
- Added a persistent Stockfish subprocess with import-time prewarming capped at 30 seconds.
- Reconstructed FEN from arena `pieces` / `to_play` state using memory-based castling tracking.
