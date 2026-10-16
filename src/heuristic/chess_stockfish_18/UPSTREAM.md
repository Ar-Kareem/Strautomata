This chess heuristic uses the Stockfish engine from the official GitHub repository: https://github.com/official-stockfish/Stockfish (Stockfish 18)
Release date: 2026-01-31

Local modifications:

- Added an arena-specific `passthrough.py` UCI wrapper.
- Added a persistent Stockfish subprocess with conservative per-move time limits.
- Reconstructed FEN from arena `pieces` / `to_play` state and the optional legal-move debug hook.
- Added a legal fallback to the first arena-provided move if the external engine is unavailable.
