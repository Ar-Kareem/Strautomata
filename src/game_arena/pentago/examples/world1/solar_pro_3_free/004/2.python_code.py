
import numpy as np

INF_WIN = 10**9          # Huge positive value for a win
INF_LOSE = -10**9        # Huge negative value for a loss
DEPTH_LIMIT = 1          # One ply look‑ahead (our move + opponent reply)

def apply_move(you, opponent, r, c, quad, dir, is_our_turn):
    """Place a marble on the board and rotate the chosen quadrant."""
    nyou = np.copy(you)
    nopp = np.copy(opponent)

    # Place the marble
    if is_our_turn:
        nyou[r, c] = 1
    else:
        nopp[r, c] = 1

    # Determine the top‑left corner of the quadrant
    rows_start = (quad // 2) * 3
    cols_start = (quad % 2) * 3
    quadrant = nyou[rows_start:rows_start+3, cols_start:cols_start+3]

    # Rotate
    if dir == 'L':
        rotated = np.rot90(quadrant, 1)   # anticlockwise
    elif dir == 'R':
        rotated = np.rot90(quadrant, -1)  # clockwise
    else:
        raise ValueError('Direction must be L or R')

    # Apply the rotation to both players
    nyou[rows_start:rows_start+3, cols_start:cols_start+3] = rotated
    nopp[rows_start:rows_start+3, cols_start:cols_start+3] = rotated
    return nyou, nopp


def check_winner(you, opponent):
    """Return 0 if you have a 5‑in‑a‑row, 2 if opponent does, -1 otherwise."""
    # Horizontal
    for r in range(6):
        for c in (0, 1):                # start columns 0 or 1 give length‑5 runs
            cnt_y = np.sum(you[r, c:c+5])
            cnt_o = np.sum(opponent[r, c:c+5])
            if cnt_y == 5:
                return 0
            if cnt_o == 5:
                return 2
    # Vertical
    for c in range(6):
        for r in (0, 1):
            cnt_y = np.sum(you[r:r+5, c])
            cnt_o = np.sum(opponent[r:r+5, c])
            if cnt_y == 5:
                return 0
            if cnt_o == 5:
                return 2
    # Main diagonal
    for sr in (0, 1):
        for sc in (0, 1):
            cnt_y = np.sum(you[sr:sr+5, sc:sc+5])
            cnt_o = np.sum(opponent[sr:sr+5, sc:sc+5])
            if cnt_y == 5:
                return 0
            if cnt_o == 5:
                return 2
    # Anti‑diagonal
    for sr in (0, 1):
        for sc in (4, 5):
            cnt_y = np.sum(you[sr:sr+5, sc:sc-5:-1])
            cnt_o = np.sum(opponent[sr:sr+5, sc:sc-5:-1])
            if cnt_y == 5:
                return 0
            if cnt_o == 5:
                return 2
    return -1


def heuristic(you, opponent):
    """Static evaluation: big bonus for 5‑in‑a‑row, small bonus for 4, penalties otherwise."""
    score = 0

    # Horizontal
    for r in range(6):
        for c in (0, 1):
            cnt_y = np.sum(you[r, c:c+5])
            cnt_o = np.sum(opponent[r, c:c+5])
            if cnt_y == 5:
                score += 100
            elif cnt_y >= 4:
                score += 1
            if cnt_o == 5:
                score -= 100
            elif cnt_o >= 4:
                score -= 1

    # Vertical
    for c in range(6):
        for r in (0, 1):
            cnt_y = np.sum(you[r:r+5, c])
            cnt_o = np.sum(opponent[r:r+5, c])
            if cnt_y == 5:
                score += 100
            elif cnt_y >= 4:
                score += 1
            if cnt_o == 5:
                score -= 100
            elif cnt_o >= 4:
                score -= 1

    # Main diagonal
    for sr in (0, 1):
        for sc in (0, 1):
            cnt_y = np.sum(you[sr:sr+5, sc:sc+5])
            cnt_o = np.sum(opponent[sr:sr+5, sc:sc+5])
            if cnt_y == 5:
                score += 100
            elif cnt_y >= 4:
                score += 1
            if cnt_o == 5:
                score -= 100
            elif cnt_o >= 4:
                score -= 1

    # Anti‑diagonal
    for sr in (0, 1):
        for sc in (4, 5):
            cnt_y = np.sum(you[sr:sr+5, sc:sc-5:-1])
            cnt_o = np.sum(opponent[sr:sr+5, sc:sc-5:-1])
            if cnt_y == 5:
                score += 100
            elif cnt_y >= 4:
                score += 1
            if cnt_o == 5:
                score -= 100
            elif cnt_o >= 4:
                score -= 1
    return score


def generate_moves(you, opponent):
    """All legal moves on the given board, sorted for deterministic order."""
    empty = [(r, c) for r in range(6) for c in range(6) if you[r, c] == 0 and opponent[r, c] == 0]
    moves = [(r, c, quad, dir) for r, c in empty
             for quad in range(4) for dir in ('L', 'R')]
    moves.sort()
    return moves


def opponent_minimax(you_board, opponent_board):
    """Opponent’s one‑ply look‑ahead: return their best move and the score from our view."""
    moves = generate_moves(you_board, opponent_board)
    if not moves:                     # shouldn't happen when policy is called
        return None, heuristic(opponent_board, you_board)

    best_score = float('inf')
    best_move = None
    for mv in moves:
        n_you, n_opp = apply_move(you_board, opponent_board, *mv, False)   # opponent places
        winner = check_winner(n_you, n_opp)
        if winner == 0:               # opponent wins
            score = INF_LOSE
        else:
            # Evaluate from our perspective (our board is n_opp)
            score = heuristic(n_opp, n_you)
        if score < best_score:
            best_score = score
            best_move = mv
    # Fallback if something went wrong
    if best_move is None:
        best_move = moves[0] if moves else (0, 0, 0, 'L')
    return best_move, best_score


def policy(you, opponent):
    """Return the next move as a string: row,col,quad,dir (1‑indexed)."""
    you_np = np.asarray(you, dtype=int)
    opp_np = np.asarray(opponent, dtype=int)

    # 1. Immediate win detection
    candidates = generate_moves(you_np, opp_np)
    for mv in candidates:
        nyou, nopp = apply_move(you_np, opp_np, *mv, True)   # our turn
        if check_winner(nyou, nopp) == 0:                  # we win
            return f"{mv[0]+1},{mv[1]+1},{mv[2]},{mv[3]}"

    # 2. Look‑ahead against opponent’s best reply
    best_move = None
    best_score = -float('inf')
    for mv in candidates:
        nyou, nopp = apply_move(you_np, opp_np, *mv, True)

        # Does the opponent already win after our move?
        if check_winner(nyou, nopp) == 2:
            score = INF_LOSE
        else:
            # opponent's optimal reply
            _, opp_score = opponent_minimax(nopp, nyou)
            score = opp_score

        if score > best_score:
            best_score = score
            best_move = mv

    # 3. Fallback – guaranteed legal move
    if best_move is None:
        best_move = candidates[0] if candidates else (0, 0, 0, 'L')
    return f"{best_move[0]+1},{best_move[1]+1},{best_move[2]},{best_move[3]}"
