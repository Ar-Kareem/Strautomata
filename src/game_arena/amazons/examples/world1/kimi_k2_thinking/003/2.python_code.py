
import numpy as np

# ----------------------------------------------------------------------
# Constants
BOARD_SIZE = 6
DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
INF = 10 ** 6               # large value for terminal states

# ----------------------------------------------------------------------
# Helper functions -----------------------------------------------------

def get_legal_moves(board, player):
    """
    Return a list of legal moves for `player` (1 or 2).
    Each move is a tuple ((from_r, from_c), (to_r, to_c), (arrow_r, arrow_c)).
    """
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == player:
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    # step in this direction while squares are empty
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr, nc] == 0:
                        # generate all possible arrows from (nr,nc)
                        for dr2, dc2 in DIRECTIONS:
                            ar, ac = nr + dr2, nc + dc2
                            while 0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE:
                                # arrow may land on the vacated `from` square
                                if board[ar, ac] != 0 and not (ar == r and ac == c):
                                    break
                                moves.append(((r, c), (nr, nc), (ar, ac)))
                                ar += dr2
                                ac += dc2
                        nr += dr
                        nc += dc
    return moves


def apply_move(board, move, player):
    """
    Apply a move (tuple as returned by get_legal_moves) to a board copy.
    `player` must be the moving player (1 or 2).
    """
    (fr, fc), (tr, tc), (ar, ac) = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def count_moves(board, player):
    """
    Count how many legal moves `player` has on the given board.
    This is a fast, counting‑only version of get_legal_moves.
    """
    cnt = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == player:
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr, nc] == 0:
                        # all possible arrows from (nr,nc)
                        for dr2, dc2 in DIRECTIONS:
                            ar, ac = nr + dr2, nc + dc2
                            while 0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE:
                                if board[ar, ac] != 0 and not (ar == r and ac == c):
                                    break
                                cnt += 1
                                ar += dr2
                                ac += dc2
                        nr += dr
                        nc += dc
    return cnt


def compute_move_dependencies(board, player):
    """
    For a given board (after our move) compute:
        M      – total number of legal moves for `player`
        deps   – 6x6 array where deps[r,c] is how many of those M moves require
                 square (r,c) to stay empty.
    """
    deps = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    M = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == player:
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr, nc] == 0:
                        # squares that must stay empty for this move (path)
                        path = []
                        cr, cc = r + dr, c + dc
                        while True:
                            path.append((cr, cc))
                            if cr == nr and cc == nc:
                                break
                            cr += dr
                            cc += dc

                        # all possible arrows from the landing square (nr,nc)
                        for dr2, dc2 in DIRECTIONS:
                            ar, ac = nr + dr2, nc + dc2
                            while 0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE:
                                if board[ar, ac] != 0 and not (ar == r and ac == c):
                                    break
                                # this complete move requires every square in `path`
                                # plus the arrow landing square
                                for sq in path:
                                    deps[sq] += 1
                                deps[ar, ac] += 1
                                M += 1
                                ar += dr2
                                ac += dc2
                        nr += dr
                        nc += dc
    return M, deps


def opponent_arrow_squares(board, opponent):
    """
    Return a set of all squares that `opponent` could place an arrow on
    (the third part of any of his legal moves).
    """
    reachable = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] == opponent:
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr, nc] == 0:
                        # arrows from (nr,nc)
                        for dr2, dc2 in DIRECTIONS:
                            ar, ac = nr + dr2, nc + dc2
                            while 0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE:
                                if board[ar, ac] != 0 and not (ar == r and ac == c):
                                    break
                                reachable.add((ar, ac))
                                ar += dr2
                                ac += dc2
                        nr += dr
                        nc += dc
    return reachable


# ----------------------------------------------------------------------
# Policy ---------------------------------------------------------------

def policy(board):
    """
    Return a legal move string for player 1 (amazon == 1).
    The move format is: "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    """
    # ---- 1. generate all legal moves for player 1 -----------------
    moves = get_legal_moves(board, player=1)
    if not moves:                     # should never happen, but be safe
        # emergency: try to produce any legal move by scanning the board
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r, c] == 1:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr, nc] == 0:
                            for dr2, dc2 in DIRECTIONS:
                                ar, ac = nr + dr2, nc + dc2
                                while 0 <= ar < BOARD_SIZE and 0 <= ac < BOARD_SIZE:
                                    if board[ar, ac] != 0 and not (ar == r and ac == c):
                                        break
                                    return f"{r},{c}:{nr},{nc}:{ar},{ac}"
        # ultimate fallback – illegal, but the environment should never ask for a move
        # when we have none.
        return "0,0:0,0:0,0"

    # ---- 2. quick screen – opponent mobility after each move -------
    move_opp_mob = []
    for mv in moves:
        nb = apply_move(board, mv, player=1)
        opp_mob = count_moves(nb, player=2)
        move_opp_mob.append((opp_mob, mv))

    # sort by increasing opponent mobility (best first)
    move_opp_mob.sort(key=lambda x: x[0])

    # ---- 3. immediate win ? ---------------------------------------
    for opp_mob, mv in move_opp_mob:
        if opp_mob == 0:                     # opponent cannot move -> we win
            (fr, fc), (tr, tc), (ar, ac) = mv
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # ---- 4. deeper evaluation of the best K candidates -----------
    K = min(15, len(move_opp_mob))           # keep the branching factor small
    best_eff_mob = -INF
    best_move = None

    for i in range(K):
        opp_mob, mv = move_opp_mob[i]
        nb = apply_move(board, mv, player=1)

        # --- our mobility and dependency counts on the new board ---
        M, deps = compute_move_dependencies(nb, player=1)

        # --- squares the opponent could place an arrow on ----------
        opp_arrows = opponent_arrow_squares(nb, opponent=2)

        # --- opponent's best block (max dependency count among his reachable squares) ---
        if opp_arrows:
            block = max(deps[sq] for sq in opp_arrows)
        else:
            block = 0

        effective_mobility = M - block          # our moves after opponent's best block

        if effective_mobility > best_eff_mob:
            best_eff_mob = effective_mobility
            best_move = mv

    # ---- 5. final decision ----------------------------------------
    if best_move is None:                     # should not happen, but guard
        best_move = move_opp_mob[0][1]        # pick the move with smallest opponent mobility

    (fr, fc), (tr, tc), (ar, ac) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
