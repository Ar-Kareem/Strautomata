
import numpy as np
import time

def policy(you, opponent):
    # Directions in order: up, down, left, right
    DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    DIR_TO_CHAR = {(-1, 0): 'U', (1, 0): 'D', (0, -1): 'L', (0, 1): 'R'}

    me = np.array(you, dtype=bool)
    opp = np.array(opponent, dtype=bool)

    # ------------------------------------------------------------------
    # Generate all legal moves for the player whose pieces are `me_board`
    # ------------------------------------------------------------------
    def get_moves(me_board, opp_board):
        moves = []
        rows, cols = np.where(me_board)
        for r, c in zip(rows, cols):
            for dr, dc, _ in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 5 and 0 <= nc < 6 and opp_board[nr, nc]:
                    moves.append((r, c, dr, dc))
        return moves

    # --------------------------------------
    # Apply a move and return the new boards
    # --------------------------------------
    def apply_move(me_board, opp_board, r, c, dr, dc):
        new_me = me_board.copy()
        new_opp = opp_board.copy()
        new_me[r, c] = False
        new_opp[r + dr, c + dc] = False
        new_me[r + dr, c + dc] = True
        return new_me, new_opp

    # ------------------------------------------------------------------
    # Static evaluation: mobility difference (current player's perspective)
    # ------------------------------------------------------------------
    def evaluate(me_board, opp_board):
        my_moves = len(get_moves(me_board, opp_board))
        opp_moves = len(get_moves(opp_board, me_board))
        return my_moves - opp_moves

    # ------------------------------------------------------------------
    # Order moves by one-ply negamax score
    # ------------------------------------------------------------------
    def order_moves(me_board, opp_board, moves):
        scored = []
        for move in moves:
            r, c, dr, dc = move
            new_me, new_opp = apply_move(me_board, opp_board, r, c, dr, dc)
            # After the move, it's the opponent's turn.
            # Our one-step value is -evaluate(opponent, us).
            score = -evaluate(new_opp, new_me)
            scored.append((score, move))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    # ------------------------------------------------------------------
    # Negamax with alpha-beta pruning
    # me_board : pieces of the player whose turn it is
    # opp_board: pieces of the opponent
    # ------------------------------------------------------------------
    def negamax(me_board, opp_board, depth, alpha, beta):
        if depth == 0:
            return evaluate(me_board, opp_board)
        moves = get_moves(me_board, opp_board)
        if not moves:
            return -1_000_000   # current player loses

        moves_ordered = order_moves(me_board, opp_board, moves)
        best_val = -float('inf')
        for r, c, dr, dc in moves_ordered:
            new_me, new_opp = apply_move(me_board, opp_board, r, c, dr, dc)
            val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_val

    # ------------------------------------------------------------------
    # Iterative deepening with time control
    # ------------------------------------------------------------------
    start_time = time.time()
    TIME_LIMIT = 0.9  # seconds, leave small margin

    all_moves = get_moves(me, opp)
    if not all_moves:          # should never happen
        return "0,0,U"
    if len(all_moves) == 1:
        r, c, dr, dc = all_moves[0]
        return f"{r},{c},{DIR_TO_CHAR[(dr, dc)]}"

    best_move = all_moves[0]   # fallback
    depth = 1
    while True:
        if time.time() - start_time > TIME_LIMIT:
            break

        current_best_move = best_move
        best_val = -float('inf')
        alpha = -float('inf')
        beta = float('inf')

        moves_ordered = order_moves(me, opp, all_moves)
        for r, c, dr, dc in moves_ordered:
            if time.time() - start_time > TIME_LIMIT:
                break
            new_me, new_opp = apply_move(me, opp, r, c, dr, dc)
            val = -negamax(new_opp, new_me, depth - 1, -beta, -alpha)
            if val > best_val:
                best_val = val
                current_best_move = (r, c, dr, dc)
            alpha = max(alpha, val)
        else:
            # Completed the search at this depth
            best_move = current_best_move
            depth += 1
            continue
        # Time ran out inside the loop – use the best move from the last full depth
        break

    r, c, dr, dc = best_move
    return f"{r},{c},{DIR_TO_CHAR[(dr, dc)]}"
