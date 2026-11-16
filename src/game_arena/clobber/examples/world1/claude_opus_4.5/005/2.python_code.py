
import numpy as np
import time

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    DIR_NAMES = ['U', 'D', 'L', 'R']
    DIR_DELTAS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    start_time = time.time()
    time_limit = 0.9  # Leave some margin
    
    def get_moves(my_board, opp_board):
        moves = []
        for r in range(5):
            for c in range(6):
                if my_board[r, c] == 1:
                    for i, (dr, dc) in enumerate(DIR_DELTAS):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and opp_board[nr, nc] == 1:
                            moves.append((r, c, DIR_NAMES[i], nr, nc))
        return moves
    
    def make_move(my_board, opp_board, move):
        r, c, _, nr, nc = move
        new_my = my_board.copy()
        new_opp = opp_board.copy()
        new_my[r, c] = 0
        new_my[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_my, new_opp
    
    def evaluate(my_board, opp_board):
        my_moves = len(get_moves(my_board, opp_board))
        opp_moves = len(get_moves(opp_board, my_board))
        
        my_pieces = np.sum(my_board)
        opp_pieces = np.sum(opp_board)
        
        # Mobility is crucial
        mobility_score = (my_moves - opp_moves) * 10
        
        # Piece advantage matters but less than mobility
        piece_score = (my_pieces - opp_pieces) * 2
        
        return mobility_score + piece_score
    
    def minimax(my_board, opp_board, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(my_board, opp_board), None
        
        if maximizing:
            moves = get_moves(my_board, opp_board)
        else:
            moves = get_moves(opp_board, my_board)
        
        if not moves:
            # Current player loses
            return (-10000 if maximizing else 10000), None
        
        if depth == 0:
            return evaluate(my_board, opp_board), None
        
        best_move = moves[0]
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_my, new_opp = make_move(my_board, opp_board, move)
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_opp, new_my = make_move(opp_board, my_board, move)
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Get initial legal moves
    legal_moves = get_moves(you, opponent)
    
    if not legal_moves:
        # Should not happen if we're called with legal moves available
        return "0,0,U"
    
    best_move = legal_moves[0]
    
    # Iterative deepening
    for depth in range(1, 20):
        if time.time() - start_time > time_limit:
            break
        
        _, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
        
        if move is not None:
            best_move = move
        
        if time.time() - start_time > time_limit:
            break
    
    r, c, d, _, _ = best_move
    return f"{r},{c},{d}"
