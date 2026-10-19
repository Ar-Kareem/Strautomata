
from typing import List, Tuple

N = 4

# Positional preference: center > inner edges/corners
POSITION_WEIGHTS = [
    [3, 4, 4, 3],
    [4, 6, 6, 4],
    [4, 6, 6, 4],
    [3, 4, 4, 3],
]

# Precompute all winning lines on a 4x4 board
LINES = []

# Rows
for r in range(N):
    LINES.append([(r, c) for c in range(N)])

# Cols
for c in range(N):
    LINES.append([(r, c) for r in range(N)])

# Diagonals
LINES.append([(i, i) for i in range(N)])
LINES.append([(i, N - 1 - i) for i in range(N)])


def empty_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                cells.append((r, c))
    return cells


def is_win(board: List[List[int]], player: int) -> bool:
    for line in LINES:
        ok = True
        for r, c in line:
            if board[r][c] != player:
                ok = False
                break
        if ok:
            return True
    return False


def line_score(board: List[List[int]], player: int) -> int:
    """
    Evaluate board potential for player.
    Only lines not blocked by opponent contribute.
    """
    opp = -player
    score = 0
    for line in LINES:
        p_count = 0
        o_count = 0
        empties = 0
        for r, c in line:
            v = board[r][c]
            if v == player:
                p_count += 1
            elif v == opp:
                o_count += 1
            else:
                empties += 1

        if o_count == 0:
            # Exponential-like reward for progress on open lines
            if p_count == 4:
                score += 100000
            elif p_count == 3 and empties == 1:
                score += 500
            elif p_count == 2 and empties == 2:
                score += 50
            elif p_count == 1 and empties == 3:
                score += 8
            elif p_count == 0:
                score += 1

        if p_count == 0:
            # Penalize opponent open lines too
            if o_count == 4:
                score -= 100000
            elif o_count == 3 and empties == 1:
                score -= 700
            elif o_count == 2 and empties == 2:
                score -= 60
            elif o_count == 1 and empties == 3:
                score -= 8
    return score


def immediate_winning_moves(board: List[List[int]], player: int) -> List[Tuple[int, int]]:
    wins = []
    for r, c in empty_cells(board):
        board[r][c] = player
        if is_win(board, player):
            wins.append((r, c))
        board[r][c] = 0
    return wins


def count_future_wins_after_move(board: List[List[int]], move: Tuple[int, int], player: int) -> int:
    """
    Count how many immediate winning moves player would have on the next turn
    after placing move now.
    """
    r, c = move
    board[r][c] = player
    count = 0
    for rr, cc in empty_cells(board):
        board[rr][cc] = player
        if is_win(board, player):
            count += 1
        board[rr][cc] = 0
    board[r][c] = 0
    return count


def move_heuristic(board: List[List[int]], move: Tuple[int, int]) -> int:
    r, c = move
    score = 0

    # Positional value
    score += POSITION_WEIGHTS[r][c]

    # Count participation in viable lines
    for line in LINES:
        if (r, c) not in line:
            continue
        vals = [board[rr][cc] for rr, cc in line]
        if -1 not in vals:
            my_count = vals.count(1)
            score += 2 + 3 * my_count
        if 1 not in vals:
            opp_count = vals.count(-1)
            score += 1 + 2 * opp_count  # occupying key defensive squares matters

    return score


def policy(board: List[List[int]]) -> Tuple[int, int]:
    legal = empty_cells(board)
    if not legal:
        return (0, 0)  # should not happen in valid play, but keeps function total

    # 1. Win immediately if possible
    my_wins = immediate_winning_moves(board, 1)
    if my_wins:
        return my_wins[0]

    # 2. Block opponent immediate win
    opp_wins = immediate_winning_moves(board, -1)
    if opp_wins:
        # If multiple blocks exist, choose the best-scoring blocking move
        best = None
        best_score = -10**18
        for mv in opp_wins:
            r, c = mv
            board[r][c] = 1
            score = line_score(board, 1) + move_heuristic(board, mv)
            board[r][c] = 0
            if score > best_score:
                best_score = score
                best = mv
        return best

    # 3. Score all legal moves
    best_move = legal[0]
    best_score = -10**18

    for mv in legal:
        r, c = mv
        board[r][c] = 1

        # If this somehow already wins, strongly prefer it
        if is_win(board, 1):
            board[r][c] = 0
            return mv

        score = 0

        # Static board evaluation after move
        score += line_score(board, 1)

        # Positional and line participation
        score += move_heuristic(board, mv)

        # Create future threats
        future_wins = 0
        for rr, cc in empty_cells(board):
            board[rr][cc] = 1
            if is_win(board, 1):
                future_wins += 1
            board[rr][cc] = 0
        score += 180 * future_wins

        # Opponent's immediate replies after our move
        opp_immediate = 0
        opp_best_reply_eval = -10**18
        for rr, cc in empty_cells(board):
            board[rr][cc] = -1
            if is_win(board, -1):
                opp_immediate += 1
            reply_eval = line_score(board, -1)
            if reply_eval > opp_best_reply_eval:
                opp_best_reply_eval = reply_eval
            board[rr][cc] = 0

        # Strongly avoid giving immediate wins
        score -= 300 * opp_immediate

        # Mild minimax flavor: avoid moves that give opponent strong positions
        score -= opp_best_reply_eval // 5

        board[r][c] = 0

        if score > best_score:
            best_score = score
            best_move = mv

    # 4. Guaranteed legal fallback
    if board[best_move[0]][best_move[1]] == 0:
        return best_move

    for mv in legal:
        if board[mv[0]][mv[1]] == 0:
            return mv

    return (0, 0)
