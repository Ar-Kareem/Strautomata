
import numpy as np

def evaluate(you: np.ndarray, opp: np.ndarray) -> int:
    """Return our piece advantage: number of our pieces minus number of opponent pieces."""
    return int(np.sum(you)) - int(np.sum(opp))

def opponent_best(board_you: np.ndarray, board_opp: np.ndarray) -> int:
    """Simulate the opponent's optimal move (minimising our advantage) and return the resulting value."""
    you_arr = np.array(board_you, dtype=int)
    opp_arr = np.array(board_opp, dtype=int)

    min_val = None
    for r0 in range(5):
        for c0 in range(6):
            if opp_arr[r0, c0] == 1:
                for dr, dc, dir_char in [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]:
                    r1 = r0 + dr
                    c1 = c0 + dc
                    if 0 <= r1 < 5 and 0 <= c1 < 6 and you_arr[r1, c1] == 1:
                        n_you = you_arr.copy()
                        n_opp = opp_arr.copy()
                        n_you[r0, c0] = 0      # remove captured opponent piece
                        n_you[r1, c1] = 1      # place our piece at destination
                        n_opp[r1, c1] = 0      # opponent piece disappears
                        val = evaluate(n_you, n_opp)
                        if (min_val is None) or (val < min_val):
                            min_val = val

    if min_val is None:          # opponent has no legal move – cannot reply
        return evaluate(you_arr, opp_arr)
    return min_val

def capture_options(you: np.ndarray, opp: np.ndarray) -> list:
    """Enumerate all legal captures for the player with the `you` pieces."""
    candidates = []
    dirs = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    for r0 in range(5):
        for c0 in range(6):
            if you[r0, c0] == 1:
                for dr, dc, dir_char in dirs:
                    r1 = r0 + dr
                    c1 = c0 + dc
                    if 0 <= r1 < 5 and 0 <= c1 < 6 and opp[r1, c1] == 1:
                        candidates.append((r0, c0, r1, c1, dir_char))
    return candidates

def policy(you: list[int], opponent: list[int]) -> str:
    """Return the next move in the format 'row,col,dir'."""
    you_arr = np.array(you, dtype=int)
    opp_arr = np.array(opponent, dtype=int)

    best_score = -float('inf')
    best_move = None
    best_second = None   # tie‑breaker: number of opponent pieces adjacent to our new piece
    best_third = None    # tie‑breaker: Manhattan distance of the captured piece to the centre

    for (r0, c0, r1, c1, dir_char) in capture_options(you_arr, opp_arr):
        # Simulate our capture
        new_you = you_arr.copy()
        new_opp = opp_arr.copy()
        new_you[r0, c0] = 0
        new_you[r1, c1] = 1
        new_opp[r1, c1] = 0

        # Minimax value after opponent's best reply
        eval_after = opponent_best(new_you, new_opp)

        # Secondary metrics for tie‑breaking
        # 1) How many opponent pieces now threaten our newly placed piece?
        adj_threat = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            rr = r1 + dr
            cc = c1 + dc
            if 0 <= rr < 5 and 0 <= cc < 6:
                adj_threat += new_opp[rr, cc]

        # 2) Distance of the captured opponent square from the board centre (2,2)
        centre_row, centre_col = 2, 2
        manhattan = abs(r1 - centre_row) + abs(c1 - centre_col)

        # Update best move according to our selection criteria
        if eval_after > best_score:
            best_score = eval_after
            best_move = (r0, c0, dir_char)          # start row, start col, direction
            best_second = adj_threat
            best_third = manhattan
        elif eval_after == best_score:
            if adj_threat < best_second:
                best_move = (r0, c0, dir_char)
                best_second = adj_threat
                best_third = manhattan
            elif adj_threat == best_second and manhattan < best_third:
                best_move = (r0, c0, dir_char)

    # Fallback – the arena guarantees at least one legal move,
    # but keep a harmless default for completeness.
    if best_move is None:
        return "0,0,R"

    row, col, dir_char = best_move
    return f"{row},{col},{dir_char}"
