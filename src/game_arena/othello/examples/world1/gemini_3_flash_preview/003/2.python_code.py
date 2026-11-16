
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def get_legal_moves(player_board, opp_board):
        moves = []
        empty = ~(player_board | opp_board)
        for r in range(8):
            for c in range(8):
                if empty[r, c] and is_legal(r, c, player_board, opp_board):
                    moves.append((r, c))
        return moves

    def is_legal(r, c, player_board, opp_board):
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = r + dr, c + dc
            found_opp = False
            while 0 <= nr < 8 and 0 <= nc < 8 and opp_board[nr, nc]:
                nr += dr
                nc += dc
                found_opp = True
            if found_opp and 0 <= nr < 8 and 0 <= nc < 8 and player_board[nr, nc]:
                return True
        return False

    def make_move(r, c, player_board, opp_board):
        new_player = player_board.copy()
        new_opp = opp_board.copy()
        new_player[r, c] = 1
        for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr, nc = r + dr, c + dc
            path = []
            while 0 <= nr < 8 and 0 <= nc < 8 and opp_board[nr, nc]:
                path.append((nr, nc))
                nr += dr
                nc += dc
            if path and 0 <= nr < 8 and 0 <= nc < 8 and player_board[nr, nc]:
                for pr, pc in path:
                    new_player[pr, pc] = 1
                    new_opp[pr, pc] = 0
        return new_player, new_opp

    weights = np.array([
        [100, -20, 10,  5,  5, 10, -20, 100],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [ 10,  -2,  5,  1,  1,  5,  -2,  10],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [ 10,  -2,  5,  1,  1,  5,  -2,  10],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [100, -20, 10,  5,  5, 10, -20, 100]
    ])

    def evaluate(p_board, o_board):
        # Piece Differential & Position
        score = np.sum(p_board * weights) - np.sum(o_board * weights)
        # Mobility
        p_moves = len(get_legal_moves(p_board, o_board))
        o_moves = len(get_legal_moves(o_board, p_board))
        score += (p_moves - o_moves) * 10
        return score

    def minimax(p_board, o_board, depth, alpha, beta, maximizing):
        p_moves = get_legal_moves(p_board, o_board)
        if depth == 0 or (not p_moves and not get_legal_moves(o_board, p_board)):
            return evaluate(p_board, o_board)

        if not p_moves:
            return -minimax(o_board, p_board, depth - 1, -beta, -alpha, not maximizing)

        # Move ordering (Corners first)
        p_moves.sort(key=lambda m: weights[m[0], m[1]], reverse=True)

        if maximizing:
            v = -float('inf')
            for r, c in p_moves:
                nb_p, nb_o = make_move(r, c, p_board, o_board)
                v = max(v, -minimax(nb_o, nb_p, depth - 1, -beta, -alpha, False))
                alpha = max(alpha, v)
                if beta <= alpha: break
            return v
        else:
            v = float('inf')
            for r, c in p_moves:
                nb_p, nb_o = make_move(r, c, p_board, o_board)
                v = min(v, -minimax(nb_o, nb_p, depth - 1, -beta, -alpha, True))
                beta = min(beta, v)
                if beta <= alpha: break
            return v

    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"

    best_move = legal_moves[0]
    best_val = -float('inf')
    
    # Depth 4 is safe for 1s limit
    for r, c in legal_moves:
        nb_p, nb_o = make_move(r, c, you, opponent)
        val = -minimax(nb_o, nb_p, 3, -float('inf'), float('inf'), False)
        if val > best_val:
            best_val = val
            best_move = (r, c)

    return chr(best_move[1] + ord('a')) + str(best_move[0] + 1)
