This chess heuristic uses the Stockfish engine from the official GitHub repository: https://github.com/official-stockfish/Stockfish (Stockfish 9)
Release commit: `378c8bdbb8f930472fc4316aa6c417802294bbad`

Local modifications:

- Added an arena-specific `passthrough.py` UCI wrapper.
- Added an installer that downloads the official `sf_9` source archive and compiles a local Linux binary.
- Added a persistent Stockfish subprocess with conservative per-move time limits.
- Reconstructed FEN from arena `pieces` / `to_play` state and the optional legal-move debug hook.
- Added a legal fallback to the first arena-provided move if the external engine is unavailable.
