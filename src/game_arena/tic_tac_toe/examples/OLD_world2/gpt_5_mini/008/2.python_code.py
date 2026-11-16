
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose next move for 4x4 tic-tac-toe.
    board: 4x4 list of lists with 0 empty, 1 (us), -1 (opponent)
    Returns (row, col) in 0..3
    """
    SIZE = 4
    ME = 1
    OP = -1

    # generate all winning lines (each as list of (r,c) coordinates)
    lines = []
    # rows
    for r in range(SIZE):
        lines.append([(r, c) for c in range(SIZE)])
    # cols
    for c in range(SIZE):
        lines.append([(r, c) for r in range(SIZE)])
    # main diag
    lines.append([(i, i) for i in range(SIZE)])
    # anti diag
    lines.append([(i, SIZE - 1 - i) for i in range(SIZE)])

    def is_win(bd, player):
        for L in lines:
            s = sum(bd[r][c] for (r, c) in L)
            if s == player * SIZE:
                return True
        return False

    # list empty cells
    empties = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if not empties:
        return (0, 0)  # no move, shouldn't happen

    # 1) Immediate winning move for us?
    for (r, c) in empties:
        board[r][c] = ME
        if is_win(board, ME):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2) Immediate winning moves for opponent -> must block
    opp_wins = []
    for (r, c) in empties:
        board[r][c] = OP
        if is_win(board, OP):
            opp_wins.append((r, c))
        board[r][c] = 0

    if len(opp_wins) == 1:
        return opp_wins[0]
    # if many immediate opponent wins, try to create immediate win (we already checked none)
    # or create fork (multiple future threats). Otherwise we'll pick best heuristic move.

    # helper to count line stats
    def line_stats_after_move(r, c, player):
        # returns (own_count, opp_count, empty_count) for each line containing (r,c) after placing player's mark at (r,c)
        stats = []
        # consider only lines that include (r,c)
        for L in lines:
            if (r, c) in L:
                own = opp = empty = 0
                for (rr, cc) in L:
                    val = board[rr][cc]
                    if rr == r and cc == c:
                        val = player  # simulate placing
                    if val == player:
                        own += 1
                    elif val == -player:
                        opp += 1
                    else:
                        empty += 1
                stats.append((own, opp, empty))
        return stats

    # 3) Try to create a fork: number of lines that would be 3-of-our and the fourth empty (i.e., immediate threats next turn)
    def count_future_winning_threats(r, c):
        stats = line_stats_after_move(r, c, ME)
        threats = 0
        for own, oppc, emp in stats:
            # a threat is a line with our_count == 3 and no opponent in that line (empty should be 0 because our_count==3 consumes one placed; but we count if there will be one empty to complete 4)
            # Here own counts include the placed piece.
            if oppc == 0 and own == SIZE - 1:
                threats += 1
        return threats

    # 4) Heuristic scoring for each empty cell
    # weights for own and opponent counts (after our hypothetical move)
    own_weight = {1: 10, 2: 100, 3: 1000, 4: 100000}
    opp_weight = {1: 8, 2: 80, 3: 800, 4: 80000}  # blocking value (slightly less)
    center_bonus = {(1,1): 6, (1,2):6, (2,1):6, (2,2):6}  # prefer central 2x2
    diag_corner_bonus = {(0,0):1, (0,3):1, (3,0):1, (3,3):1}

    best_moves = []
    best_score = -10**9

    # Evaluate all empties
    for (r, c) in empties:
        # if this move creates immediate win we already returned. So evaluate further.
        # Count future winning threats (fork)
        forks = count_future_winning_threats(r, c)
        score = forks * 10000  # strong preference for forks

        # Evaluate lines that pass through (r,c) after placing our piece
        stats = line_stats_after_move(r, c, ME)
        for own, oppc, emp in stats:
            # if opponent present, cannot make this line ours; but blocking opponent progress is useful
            if oppc == 0:
                # pure line for us; assign weight depending on how many of our pieces would be there
                score += own_weight.get(own, 0)
            if own == 0 and oppc > 0:
                # blocking opponent's pure line progress
                score += opp_weight.get(oppc, 0)

        # center and diagonal bonuses
        score += center_bonus.get((r,c), 0)
        score += diag_corner_bonus.get((r,c), 0)

        # If opponent had multiple immediate winning squares, try moves that reduce their count:
        if len(opp_wins) >= 2:
            # count how many opp immediate wins would be blocked by placing here
            blocks = sum(1 for pos in opp_wins if pos == (r, c))
            # that is either 0 or 1; but also if placing here creates our threat maybe block indirectly - we already count forks
            score += blocks * 5000

        # deterministic tie-breaking by preferring smaller (r,c) implicitly: include tiny epsilon
        tie_break = - (r * SIZE + c) * 1e-6
        score += tie_break

        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    # If there's an opponent immediate win in multiple places and we have no winning move,
    # prefer a move that reduces opponent wins next turn if possible; already partly handled.
    # Choose first best move in sorted order for determinism
    best_moves.sort()
    return best_moves[0]
