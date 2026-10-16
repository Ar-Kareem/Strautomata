
import numpy as np

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def policy(board) -> str:
    board = np.array(board, dtype=int)
    
    def get_amazons(board, player):
        positions = np.argwhere(board == player)
        return [tuple(p) for p in positions]
    
    def get_queen_moves(board, pos):
        moves = []
        r, c = pos
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                moves.append((nr, nc))
                nr, nc = nr + dr, nc + dc
        return moves
    
    def get_all_moves(board, player):
        moves = []
        amazons = get_amazons(board, player)
        for fr, fc in amazons:
            amazon_moves = get_queen_moves(board, (fr, fc))
            for tr, tc in amazon_moves:
                # Simulate amazon move
                board[fr, fc] = 0
                board[tr, tc] = player
                arrow_targets = get_queen_moves(board, (tr, tc))
                for ar, ac in arrow_targets:
                    moves.append(((fr, fc), (tr, tc), (ar, ac)))
                # Undo
                board[fr, fc] = player
                board[tr, tc] = 0
        return moves
    
    def count_mobility(board, player):
        return len(get_all_moves(board, player))
    
    def evaluate(board):
        my_mobility = count_mobility(board, 1)
        opp_mobility = count_mobility(board, 2)
        if my_mobility == 0:
            return -10000
        if opp_mobility == 0:
            return 10000
        return (my_mobility - opp_mobility) * 10
    
    def apply_move(board, move, player):
        new_board = board.copy()
        (fr, fc), (tr, tc), (ar, ac) = move
        new_board[fr, fc] = 0
        new_board[tr, tc] = player
        new_board[ar, ac] = -1
        return new_board
    
    def minimax(board, depth, alpha, beta, maximizing):
        player = 1 if maximizing else 2
        moves = get_all_moves(board, player)
        
        if depth == 0 or not moves:
            return evaluate(board), None
        
        best_move = moves[0] if moves else None
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves[:30]:  # Limit branching
                new_board = apply_move(board, move, 1)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves[:30]:
                new_board = apply_move(board, move, 2)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Get all legal moves for safety
    legal_moves = get_all_moves(board, 1)
    
    if not legal_moves:
        # Should not happen, but return something
        amazons = get_amazons(board, 1)
        if amazons:
            fr, fc = amazons[0]
            return f"{fr},{fc}:{fr},{fc}:{fr},{fc}"
        return "0,0:0,0:0,0"
    
    # Use minimax to find best move
    try:
        _, best_move = minimax(board, 3, -float('inf'), float('inf'), True)
        if best_move is None:
            best_move = legal_moves[0]
    except:
        best_move = legal_moves[0]
    
    (fr, fc), (tr, tc), (ar, ac) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
