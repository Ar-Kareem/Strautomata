import copy

ROWS = 6
COLS = 7

def _drop(board, col, player):
    """Return a new board with player dropped in col; return None if col full."""
    if board[0][col] != 0:
        return None
    newb = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if newb[r][col] == 0:
            newb[r][col] = player
            return newb
    return None

def _is_win(board, player):
    """Check if player has 4 in a row."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player:
                return True
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if board[r][c] == player and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player:
                return True
    # Diagonal down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player:
                return True
    # Diagonal up-right
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if board[r][c] == player and board[r-1][c+1] == player and board[r-2][c+2] == player and board[r-3][c+3] == player:
                return True
    return False

def _count_patterns(board, player, length):
    """Count occurrences of contiguous segments of exactly 'length' all equal to player (may count overlapping)."""
    cnt = 0
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - length + 1):
            ok = True
            for k in range(length):
                if board[r][c+k] != player:
                    ok = False
                    break
            if ok:
                cnt += 1
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - length + 1):
            ok = True
            for k in range(length):
                if board[r+k][c] != player:
                    ok = False
                    break
            if ok:
                cnt += 1
    # Diagonal down-right
    for r in range(ROWS - length + 1):
        for c in range(COLS - length + 1):
            ok = True
            for k in range(length):
                if board[r+k][c+k] != player:
                    ok = False
                    break
            if ok:
                cnt += 1
    # Diagonal up-right
    for r in range(length - 1, ROWS):
        for c in range(COLS - length + 1):
            ok = True
            for k in range(length):
                if board[r-k][c+k] != player:
                    ok = False
                    break
            if ok:
                cnt += 1
    return cnt

def policy(board: list[list[int]]) -> int:
    """
    Choose a column index (0-6) to drop the current player's disc (1).
    Basic strategy:
    1) If we can win immediately, play that move.
    2) If opponent can win immediately, block (if single threat).
    3) Avoid moves that allow opponent an immediate win on their next turn.
    4) Choose among safe moves by heuristic: prefer center and moves creating 3-in-a-rows.
    """
    # Valid columns (not full)
    valid_cols = [c for c in range(COLS) if board[0][c] == 0]
    if not valid_cols:
        return 0  # should not happen but safe fallback

    me = 1
    opp = -1

    # 1) Immediate winning move for us
    for c in valid_cols:
        nb = _drop(board, c, me)
        if nb is None:
            continue
        if _is_win(nb, me):
            return c

    # 2) Immediate opponent winning moves (threats)
    opp_threats = []
    for c in valid_cols:
        nb = _drop(board, c, opp)
        if nb is None:
            continue
        if _is_win(nb, opp):
            opp_threats.append(c)
    if len(opp_threats) == 1:
        # block the single threat by playing that column
        block_col = opp_threats[0]
        if board[0][block_col] == 0:
            return block_col
    # If multiple threats (len >= 2) we likely cannot block both; fall through to try best move.

    # 3) Filter out moves that allow opponent immediate win after our move
    safe_moves = []
    for c in valid_cols:
        nb = _drop(board, c, me)
        if nb is None:
            continue
        # If after we play c, opponent has a winning move anywhere, then c is unsafe.
        opp_can_win = False
        for oc in range(COLS):
            if nb[0][oc] != 0:
                continue
            nb2 = _drop(nb, oc, opp)
            if nb2 is None:
                continue
            if _is_win(nb2, opp):
                opp_can_win = True
                break
        if not opp_can_win:
            safe_moves.append(c)

    # If we have safe moves, choose best among them; else fallback to any valid move.
    candidates = safe_moves if safe_moves else valid_cols

    # Heuristic ordering preference: center first, then near center
    preference = [3, 2, 4, 1, 5, 0, 6]

    # Evaluate candidates: prefer moves that create more 3-in-a-row and 2-in-a-row for us.
    best_score = None
    best_col = None
    for c in preference:
        if c not in candidates:
            continue
        nb = _drop(board, c, me)
        if nb is None:
            continue
        cnt3 = _count_patterns(nb, me, 3)
        cnt2 = _count_patterns(nb, me, 2)
        # Small heuristic: prefer center proximity too
        center_bonus = -abs(c - 3)
        score = (100 * cnt3) + (10 * cnt2) + center_bonus
        # Slight penalty if column was unsafe (i.e., not in safe_moves)
        if c not in safe_moves:
            score -= 50
        if best_score is None or score > best_score:
            best_score = score
            best_col = c

    if best_col is not None:
        return best_col

    # Fallback: return first valid column
    return valid_cols[0]