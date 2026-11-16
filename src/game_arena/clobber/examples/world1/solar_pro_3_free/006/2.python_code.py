
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Policy for the game Clobber on a 5×6 board.

    Parameters
    ----------
    you : list[int]
        Flat list (30 entries) indicating the cells occupied by my pieces (1 = occupied).
    opponent : list[int]
        Flat list (30 entries) indicating the cells occupied by the opponent pieces.

    Returns
    -------
    str
        A legal capture move in the form "row,col,dir", where
        row∈{0,…,4}, col∈{0,…,5} and dir∈{'U','R','D','L'}.
    """
    # ----- board preparation -------------------------------------------------
    # Convert the flat lists into 2‑D numpy arrays with the conventional layout:
    # rows increase fastest, then columns.
    you_board = np.array(you, dtype=int).reshape(5, 6)
    opp_board = np.array(opponent, dtype=int).reshape(5, 6)

    # Directions (Δrow, Δcol, direction character) ordered deterministically.
    DIRECTIONS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    # ----- find all legal capture moves --------------------------------------
    candidates = []                     # each element = (sr, sc, dir)
    for idx in range(30):
        if you_board[idx] != 1:
            continue                  # not my piece
        r, c = idx // 6, idx % 6
        for dr, dc, dir in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 5 and 0 <= nc < 6:
                dest_idx = nr * 6 + nc
                if opp_board[dest_idx] == 1:          # legal capture
                    candidates.append((r, c, dir))

    # The arena should always give us at least one capture; otherwise we raise.
    if not candidates:
        raise RuntimeError("No legal capture found – the player has no moves.")

    # ----- heuristic: evaluate future capture opportunities --------------------
    def future_capture(y, o):
        """
        Count how many pieces of player 'y' are orthogonally adjacent to at least one
        opponent piece 'o'.  This is the number of moves I will have on the next turn.
        """
        count = 0
        for r in range(5):
            for c in range(6):
                if y[r, c] == 0:
                    continue
                # Any of the four orthogonal neighbours belonging to opponent?
                if r > 0 and o[r - 1, c] == 1:
                    count += 1
                    break
                elif c < 5 and o[r, c + 1] == 1:
                    count += 1
                    break
                elif r < 4 and o[r + 1, c] == 1:
                    count += 1
                    break
                elif c > 0 and o[r, c - 1] == 1:
                    count += 1
                    break
        return count

    # ----- choose the move with the best heuristic ----------------------------
    best_move = None
    best_score = -1

    for (sr, sc, dir) in candidates:
        # Simulate the capture on copies of the boards
        y_sim = you_board.copy()
        o_sim = opp_board.copy()
        y_sim[sr, sc] = 0                # remove my piece from the start
        y_sim[sr + DIRECTIONS[dir][0], sr % 6 + DIRECTIONS[dir][1]] = 1   # place it at the destination
        # Destination coordinates derived from direction
        dr, dc = DIRECTIONS[dir][0], DIRECTIONS[dir][1]
        y_sim[sr + dr, sc + dc] = 1
        o_sim[sr + dr, sc + dc] = 0      # opponent piece is removed

        score = future_capture(y_sim, o_sim)

        # Tie‑break by preferring the move that appears first in the fixed scan order
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = (sr, sc, dir)

    sr, sc, dir = best_move
    # Return the move in the required string format
    return f"{sr},{sc},{dir}"
