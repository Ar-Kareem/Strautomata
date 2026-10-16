This chess heuristic uses the Leela Chess Zero engine from the official GitHub
repository: https://github.com/LeelaChessZero/lc0 (Lc0 v0.20.2)
Release commit: `9e8cf10aa965c675da86d40bd7f3ef4be5f5566e`

The installer no longer hand-picks a specific legacy network URL. Instead it
extracts the default network SHA from the official `v0.20.2` `appveyor.yml`
and downloads it via LCZero's upstream selector endpoint:
`http://lczero.org/get_network?sha=<sha>`.
For `v0.20.2`, that upstream SHA is
`7170f639ba1cdc407283b8e52377283e36845b954788c6ada8897937637ef032`.

At runtime the wrapper does not pass `--weights` unless
`CHESS_LC0_0_20_WEIGHTS` is set. That matches lc0's upstream default:
`WeightsFile=<autodiscover>`, which searches the binary directory and its
`networks/` subdirectory for the newest valid weights file.

Local modifications:

- Added an arena-specific `passthrough.py` UCI wrapper.
- Added an installer that clones the official `v0.20.2` source tag with
  submodules, builds a CPU-only BLAS backend, and downloads the network chosen
  by upstream `appveyor.yml`.
- Added a persistent lc0 subprocess with conservative per-move time limits.
- Reconstructed FEN from arena `pieces` / `to_play` state and the optional
  legal-move debug hook.
- Added a legal fallback to the first arena-provided move if the external
  engine is unavailable.
