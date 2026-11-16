
from typing import List, Tuple
import copy

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move for 4x4 Tic Tac Toe.
    board: 4x4 list of lists with 1 (us), -1 (opponent), 0 (empty)
    Returns (r, c) within 0..3
    Strategy:
      1. Win immediately if possible.
      2. Block opponent immediate win.
      3. Create a fork (move that creates >=2 immediate winning replies).
      4. Block opponent fork (try to play into their fork squares or reduce threats).
      5. Otherwise pick move maximizing heuristic (favor lines with our pieces and block opponent).
    """
    N = 4
    US = 1
    OP = -1

    # Precompute all lines (rows, cols, two diagonals)
    lines = []
    # rows
    for r in range(N):
        lines.append([(r, c) for c in range(N)])
    # cols
    for c in range(N):
        lines.append([(r, c) for r in range(N)])
    # main diag
    lines.append([(i, i) for i in range(N)])
    # anti diag
    lines.append([(i, N - 1 - i) for i in range(N)])

    def empties(b):
        es = []
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    es.append((r, c))
        return es

    def winner_after_move(b, move, player):
        """Return True if placing player at move wins immediately."""
        r, c = move
        if b[r][c] != 0:
            return False
        b[r][c] = player
        # check only affected lines: row r, col c, maybe diags
        win = False
        # row
        if all(b[r][cc] == player for cc in range(N)):
            win = True
        # col
        if all(b[rr][c] == player for rr in range(N)):
            win = True
        # main diag
        if r == c and all(b[i][i] == player for i in range(N)):
            win = True
        # anti diag
        if r + c == N - 1 and all(b[i][N - 1 - i] == player for i in range(N)):
            win = True
        b[r][c] = 0
        return win

    def count_immediate_wins(b, player):
        """Count how many empty moves would let `player` win immediately."""
        cnt = 0
        for (r, c) in empties(b):
            if winner_after_move(b, (r, c), player):
                cnt += 1
        return cnt

    def immediate_winning_moves(b, player):
        res = []
        for (r, c) in empties(b):
            if winner_after_move(b, (r, c), player):
                res.append((r, c))
        return res

    # 1) immediate win
    for mv in empties(board):
        if winner_after_move(board, mv, US):
            return mv

    # 2) block opponent immediate win(s)
    opp_wins = immediate_winning_moves(board, OP)
    if opp_wins:
        # If there's a single immediate winning cell for opponent, block it.
        if len(opp_wins) == 1:
            return opp_wins[0]
        # If multiple, try to find a move that after our play leaves opponent with 0 immediate winning moves.
        best_block = None
        best_block_remaining = 999
        for mv in empties(board):
            b2 = [row[:] for row in board]
            r, c = mv
            b2[r][c] = US
            remaining = len(immediate_winning_moves(b2, OP))
            if remaining == 0:
                return mv
            if remaining < best_block_remaining:
                best_block_remaining = remaining
                best_block = mv
        # If none fully blocks all, pick the one that minimizes opponent immediate wins
        if best_block is not None:
            return best_block

    # 3) Create fork: move that creates >=2 immediate winning moves for us next turn
    for mv in empties(board):
        b2 = [row[:] for row in board]
        r, c = mv
        b2[r][c] = US
        if count_immediate_wins(b2, US) >= 2:
            return mv

    # 4) Block opponent fork
    # Find opponent fork squares (where opponent moving would create >=2 immediate wins)
    opp_fork_positions = []
    for mv in empties(board):
        b2 = [row[:] for row in board]
        r, c = mv
        b2[r][c] = OP
        if count_immediate_wins(b2, OP) >= 2:
            opp_fork_positions.append(mv)
    if opp_fork_positions:
        # If we can play into any fork position, do so
        for mv in opp_fork_positions:
            if board[mv[0]][mv[1]] == 0:
                return mv
        # Otherwise, try moves that reduce opponent forks after our move
        best_mv = None
        best_remaining = 999
        for mv in empties(board):
            b2 = [row[:] for row in board]
            r, c = mv
            b2[r][c] = US
            # count how many fork positions opponent would have after this
            rem = 0
            for mv2 in empties(b2):
                b3 = [row[:] for row in b2]
                b3[mv2[0]][mv2[1]] = OP
                if count_immediate_wins(b3, OP) >= 2:
                    rem += 1
            if rem < best_remaining:
                best_remaining = rem
                best_mv = mv
                if rem == 0:
                    break
        if best_mv is not None:
            return best_mv

    # 5) Heuristic: pick move maximizing our potential while minimizing opponent's.
    # Scoring by lines:
    # For a line with only our pieces and empties: +10^count
    # For a line with only opponent pieces and empties: - (10^count) * 1.2 (slightly prioritize blocking)
    pow10 = [1, 10, 100, 1000, 10000]
    best_score = -10**9
    best_move = None

    center_candidates = [(1,1),(1,2),(2,1),(2,2)]
    corners = [(0,0),(0,3),(3,0),(3,3)]

    for mv in empties(board):
        b2 = [row[:] for row in board]
        b2[mv[0]][mv[1]] = US
        score = 0.0
        # evaluate all lines
        for line in lines:
            vals = [b2[r][c] for (r,c) in line]
            sumv = sum(vals)
            if all(v != OP for v in vals):  # no opponent in line -> good for us
                cnt = sum(1 for v in vals if v == US)
                score += pow10[cnt]
            if all(v != US for v in vals):  # no us in line -> threat from opponent
                cnt_op = sum(1 for v in vals if v == OP)
                score -= pow10[cnt_op] * 1.2
        # small preference: center squares
        if mv in center_candidates:
            score += 5.0
        # prefer corners mildly
        if mv in corners:
            score += 2.0
        # prefer moves that increase immediate wins count
        score += 3.0 * (1 if winner_after_move(board, mv, US) else 0)
        # tie-breaker: prefer earlier moves due to deterministic order
        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # fallback: return first empty
    es = empties(board)
    if es:
        return es[0]
    # Should never happen - board full; but return (0,0)
    return (0, 0)


# If imported, expose policy function. If run directly, simple random test.
if __name__ == "__main__":
    # simple manual test
    b = [
        [ 0,  0,  0,  0],
        [ 0,  0,  0,  0],
        [ 0,  0,  0,  0],
        [ 0,  0,  0,  0],
    ]
    print("Move chosen:", policy(b))
