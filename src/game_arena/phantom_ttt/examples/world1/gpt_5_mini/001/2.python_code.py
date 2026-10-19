
from typing import List, Tuple

# Precompute the 8 winning lines in 3x3 tic-tac-toe as indices 0..8
_WIN_LINES = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]

# Mapping index to (row, col)
def _idx_to_rc(i: int) -> Tuple[int, int]:
    return (i // 3, i % 3)

def policy(board: List[List[int]], legal_moves: List[int]):
    """
    Choose a move for Phantom Tic Tac Toe.

    - board: 3x3 list of ints. 1 => confirmed our mark; 0 => unknown (empty or opponent).
    - legal_moves: list of ints 0..8 that are currently allowed.
    Returns: (row, col) tuple.
    """
    # Flatten board values into index->value mapping (0 or 1)
    flat = []
    try:
        for r in range(3):
            for c in range(3):
                flat.append(int(board[r][c]))
    except Exception:
        # If board not indexable as expected, fallback to default move
        i = legal_moves[0]
        return _idx_to_rc(i)

    legal_set = set(int(x) for x in legal_moves)

    # Prefer legal moves that are not confirmed ours (board[idx] != 1)
    candidates = [i for i in legal_moves if flat[i] != 1]
    if not candidates:
        # If all legal moves are cells we already own (rare), just pick first legal
        chosen = int(legal_moves[0])
        return _idx_to_rc(chosen)

    # Helper: count how many of the indices in a line are our confirmed marks
    def count_ours_in_line(line):
        return sum(1 for idx in line if flat[idx] == 1)

    # 1) Immediate winning move: if there is a line where we have 2 confirmed marks and the third cell is unknown and legal, pick it.
    for line in _WIN_LINES:
        if count_ours_in_line(line) == 2:
            # find the third index in that line
            for idx in line:
                if flat[idx] != 1:
                    if idx in legal_set and idx in candidates:
                        return _idx_to_rc(idx)

    # 2) Evaluate candidates by heuristic score:
    #    - High score for moves that create multiple immediate-two-in-a-row threats (forks).
    #    - Secondary preference: center > corner > side.
    #    - Deterministic tie-breaker: smaller index.
    def move_score(idx):
        # simulate having our mark at idx
        sim_ours = set(i for i, v in enumerate(flat) if v == 1)
        sim_ours.add(idx)

        # Count lines where after move we would have exactly 2 of our marks and the third is unknown and legal
        fork_count = 0
        for line in _WIN_LINES:
            ours_in_line = sum(1 for j in line if j in sim_ours)
            # third must not already be our mark; and must be unknown (flat==0) and legal (we can try it later)
            if ours_in_line == 2:
                # find the third index
                for j in line:
                    if j not in sim_ours:
                        # only count if that third is currently unknown (flat[j] == 0)
                        # and potentially available (in legal_set). The opponent may be occupying it, but heuristic uses unknowns.
                        if flat[j] == 0 and j in legal_set:
                            fork_count += 1
                        break

        # positional preference
        center_bonus = 3 if idx == 4 else 0
        corner_bonus = 2 if idx in (0, 2, 6, 8) else 0
        side_bonus = 1 if idx in (1, 3, 5, 7) else 0

        # Combine into score; forks are most valuable
        score = fork_count * 100 + center_bonus * 10 + corner_bonus * 5 + side_bonus
        return score

    # Compute scores
    best = None
    best_score = None
    for idx in sorted(candidates):  # sorted for deterministic tie-breaker
        sc = move_score(idx)
        if best is None or sc > best_score:
            best = idx
            best_score = sc

    if best is None:
        # Fallback: pick center if possible, else pick smallest legal candidate
        if 4 in candidates:
            best = 4
        else:
            best = candidates[0]

    return _idx_to_rc(int(best))