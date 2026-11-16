
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a move for 4x4 Tic Tac Toe.
    board: 4x4 list of lists with 0 (empty), 1 (us), -1 (opponent)
    Returns (row, col)
    """

    SIZE = 4
    MY = 1
    OP = -1

    def moves(b):
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if b[r][c] == 0]

    def copy_board(b):
        return [row[:] for row in b]

    def is_win(b, player):
        # rows and cols
        for i in range(SIZE):
            if all(b[i][j] == player for j in range(SIZE)):
                return True
            if all(b[j][i] == player for j in range(SIZE)):
                return True
        # main diag
        if all(b[i][i] == player for i in range(SIZE)):
            return True
        # anti-diag
        if all(b[i][SIZE - 1 - i] == player for i in range(SIZE)):
            return True
        return False

    def immediate_wins(b, player):
        win_moves = []
        for (r, c) in moves(b):
            nb = copy_board(b)
            nb[r][c] = player
            if is_win(nb, player):
                win_moves.append((r, c))
        return win_moves

    # Evaluate if move creates a fork for 'player': after making move, count immediate winning moves for player >= 2
    def is_fork_move(b, move, player):
        nb = copy_board(b)
        r, c = move
        nb[r][c] = player
        wins = immediate_wins(nb, player)
        return len(wins) >= 2

    # Heuristic scoring for non-trivial positions
    def heuristic_score_for_move(b, move):
        # Positional preferences
        r, c = move
        pos_score = 0
        centers = {(1,1),(1,2),(2,1),(2,2)}
        corners = {(0,0),(0,3),(3,0),(3,3)}
        if (r, c) in centers:
            pos_score += 30
        elif (r, c) in corners:
            pos_score += 20
        else:
            pos_score += 10

        # Line-based evaluation after making the move
        nb = copy_board(b)
        nb[r][c] = MY
        score = pos_score

        # Define weights
        for i in range(SIZE):
            # Row
            row = [nb[i][j] for j in range(SIZE)]
            score += eval_line(row)
            # Col
            col = [nb[j][i] for j in range(SIZE)]
            score += eval_line(col)
        # Diagonals
        diag1 = [nb[i][i] for i in range(SIZE)]
        diag2 = [nb[i][SIZE-1-i] for i in range(SIZE)]
        score += eval_line(diag1)
        score += eval_line(diag2)
        return score

    def eval_line(line):
        # If both players present, line is dead (0)
        my_count = line.count(MY)
        opp_count = line.count(OP)
        empty_count = line.count(0)
        if my_count > 0 and opp_count > 0:
            return 0
        # Favor lines with more of our pieces, penalize opponent lines
        if my_count > 0:
            # weights: 3->1000,2->200,1->30,0->5
            if my_count == 3:
                return 800
            if my_count == 2:
                return 150
            if my_count == 1:
                return 30
            return 5
        if opp_count > 0:
            # Opponent lines are negative weights (we want to block)
            if opp_count == 3:
                return -700
            if opp_count == 2:
                return -120
            if opp_count == 1:
                return -20
            return -5
        # empty line
        return 2

    # Start logic
    all_moves = moves(board)
    if not all_moves:
        return (0, 0)

    # 1. Immediate win
    my_wins = immediate_wins(board, MY)
    if my_wins:
        # choose first immediate winning move
        return my_wins[0]

    # 2. Immediate block
    opp_wins = immediate_wins(board, OP)
    if len(opp_wins) == 1:
        return opp_wins[0]
    if len(opp_wins) > 1:
        # Opponent has multiple immediate wins; try to find a move that wins immediately (we handled above),
        # else try to occupy one of the opponent's winning squares (best we can do)
        # Prefer move that is also center/corner by heuristic
        best = None
        best_score = -10**9
        for mv in all_moves:
            if mv in opp_wins:
                s = heuristic_simple_pos_score(mv)
                if s > best_score:
                    best_score = s
                    best = mv
        if best:
            return best
        # fallback
        return opp_wins[0]

    # 3. Create fork
    for mv in all_moves:
        if is_fork_move(board, mv, MY):
            return mv

    # 4. Block opponent fork
    # First detect opponent fork moves
    opp_forks = [mv for mv in all_moves if is_fork_move(board, mv, OP)]
    if opp_forks:
        # If we can play directly on a fork square, do it
        for mv in opp_forks:
            if mv in all_moves:
                return mv
        # Otherwise, try moves that prevent forks by creating immediate threat
        # e.g., find our move that leads to an immediate win next (after which opponent can't fork)
        for mv in all_moves:
            nb = copy_board(board)
            nb[mv[0]][mv[1]] = MY
            if immediate_wins(nb, MY):
                return mv
        # Else choose a heuristic move that reduces opponent chances
        # pick center or best heuristic
        best = None
        best_score = -10**9
        for mv in all_moves:
            s = heuristic_score_for_move(board, mv)
            if s > best_score:
                best_score = s
                best = mv
        if best:
            return best

    # 5. Choose by heuristic score
    best_mv = None
    best_sc = -10**9
    for mv in all_moves:
        sc = heuristic_score_for_move(board, mv)
        # small deterministic tie-breaker: prefer lower row,col when equal
        if sc > best_sc or (sc == best_sc and (best_mv is None or mv < best_mv)):
            best_sc = sc
            best_mv = mv

    if best_mv:
        return best_mv

    # Fallback: first empty
    return all_moves[0]


# Helper: simple positional score for tie-breaking for immediate multi-threat blocks
def heuristic_simple_pos_score(mv):
    centers = {(1,1),(1,2),(2,1),(2,2)}
    corners = {(0,0),(0,3),(3,0),(3,3)}
    if mv in centers:
        return 3
    if mv in corners:
        return 2
    return 1


# If run as script, a tiny self-test
if __name__ == "__main__":
    # empty board example
    empty = [[0]*4 for _ in range(4)]
    print(policy(empty))  # should prefer a center position
