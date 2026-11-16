
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Determine current player:
    # We assume this policy plays as 1.
    # If counts are equal -> it's our turn, else opponent's turn in some settings,
    # but the arena typically calls policy only when it's our move.
    flat = [c for row in board for c in row]
    count_1 = flat.count(1)
    count_m1 = flat.count(-1)
    # If it's not our turn by counts, we still must return a legal move;
    # choose best move for the side to move accordingly.
    to_move = 1 if count_1 == count_m1 else -1

    def winner(b):
        # returns 1 if 1 wins, -1 if -1 wins, 0 otherwise
        lines = []
        lines.extend(b[0]); lines.extend(b[1]); lines.extend(b[2])
        # rows
        for r in range(3):
            if b[r][0] != 0 and b[r][0] == b[r][1] == b[r][2]:
                return b[r][0]
        # cols
        for c in range(3):
            if b[0][c] != 0 and b[0][c] == b[1][c] == b[2][c]:
                return b[0][c]
        # diags
        if b[0][0] != 0 and b[0][0] == b[1][1] == b[2][2]:
            return b[0][0]
        if b[0][2] != 0 and b[0][2] == b[1][1] == b[2][0]:
            return b[0][2]
        return 0

    def legal_moves(b):
        moves = []
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    moves.append((r, c))
        return moves

    # Quick checks: win/block first to be faster and still optimal.
    w = winner(board)
    if w != 0:
        # Game already ended; just return any legal move.
        moves = legal_moves(board)
        return moves[0] if moves else (0, 0)

    moves = legal_moves(board)

    def would_win(b, player, move):
        r, c = move
        b[r][c] = player
        res = winner(b)
        b[r][c] = 0
        return res == player

    # If it's our turn to move for player 1, try immediate win.
    if to_move == 1:
        for mv in moves:
            if would_win([row[:] for row in board], 1, mv):
                return mv
        # Block opponent immediate win
        for mv in moves:
            if would_win([row[:] for row in board], -1, mv):
                return mv
    else:
        # If arena ever calls policy when it's opponent's turn, choose best defense
        # i.e., block our perspective would be "play to avoid losing". We'll still
        # handle in minimax below; this block is only a shortcut.
        for mv in moves:
            if would_win([row[:] for row in board], -1, mv):
                # Opponent could win by playing mv; block it.
                return mv

    # Minimax with memoization.
    # Score from perspective of player 1:
    # +1 win for 1, -1 win for -1, 0 draw.
    @lru_cache(maxsize=None)
    def solve(state, player):
        # state is a tuple of 9 ints
        b = [list(state[i*3:(i+1)*3]) for i in range(3)]
        w = winner(b)
        if w == 1:
            return 1
        if w == -1:
            return -1
        # Draw?
        if all(v != 0 for v in state):
            return 0

        # Current player chooses move.
        best = -2 if player == 1 else 2
        for r, c in legal_moves(b):
            idx = r * 3 + c
            new_state = list(state)
            new_state[idx] = player
            val = solve(tuple(new_state), -player)
            if player == 1:
                if val > best:
                    best = val
                if best == 1:
                    break
            else:
                if val < best:
                    best = val
                if best == -1:
                    break
        return best

    # Choose a move that maximizes outcome for player 1 if it's our turn,
    # otherwise minimizes outcome for player 1 (i.e., maximizes for the side to move).
    best_moves = []
    best_score = None

    state = tuple(flat)
    # If to_move is not 1, still compute from minimax perspective.
    for r, c in moves:
        idx = r * 3 + c
        new_state = list(state)
        new_state[idx] = to_move
        score = solve(tuple(new_state), -to_move)
        if to_move == 1:
            # maximize score
            if best_score is None or score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))
        else:
            # opponent to move in some setups: they minimize our score; but we must still return a legal move.
            # We'll pick the move that is best for us (player 1), i.e., among all legal moves we choose
            # the one that gives highest score assuming it's actually our turn. However, if to_move == -1,
            # that means the arena likely expects opponent move, but we'll still return legal move that
            # maximizes score for player 1.
            if best_score is None or score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))

    # Tie-breaker: prefer center, then corners, then edges.
    priority = {(1, 1): 0, (0, 0): 1, (0, 2): 1, (2, 0): 1, (2, 2): 1,
                (0, 1): 2, (1, 0): 2, (1, 2): 2, (2, 1): 2}
    best_moves.sort(key=lambda m: priority.get(m, 3))
    return best_moves[0] if best_moves else moves[0]
