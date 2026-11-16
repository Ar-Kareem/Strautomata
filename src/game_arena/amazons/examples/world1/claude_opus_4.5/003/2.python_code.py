
import numpy as np
from typing import List, Tuple

def policy(board: np.ndarray) -> str:
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    def in_bounds(r, c):
        return 0 <= r < 6 and 0 <= c < 6
    
    def get_queen_moves(board, r, c, vacated=None):
        moves = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                cell = board[nr, nc]
                if vacated and (nr, nc) == vacated:
                    cell = 0
                if cell == 0:
                    moves.append((nr, nc))
                    nr, nc = nr + dr, nc + dc
                else:
                    break
        return moves
    
    def get_all_moves(board, player):
        moves = []
        amazons = list(zip(*np.where(board == player)))
        for fr, fc in amazons:
            board[fr, fc] = 0
            for tr, tc in get_queen_moves(board, fr, fc):
                board[tr, tc] = player
                for ar, ac in get_queen_moves(board, tr, tc, vacated=(fr, fc)):
                    moves.append((fr, fc, tr, tc, ar, ac))
                board[tr, tc] = 0
            board[fr, fc] = player
        return moves
    
    def count_reachable(board, player):
        amazons = list(zip(*np.where(board == player)))
        reachable = set()
        for r, c in amazons:
            for mr, mc in get_queen_moves(board, r, c):
                reachable.add((mr, mc))
        return len(reachable)
    
    def evaluate(board):
        my_mobility = count_reachable(board, 1)
        opp_mobility = count_reachable(board, 2)
        
        my_moves = len(get_all_moves(board, 1))
        opp_moves = len(get_all_moves(board, 2))
        
        if opp_moves == 0:
            return 10000
        if my_moves == 0:
            return -10000
        
        return (my_mobility - opp_mobility) * 2 + (my_moves - opp_moves)
    
    def apply_move(board, move, player):
        fr, fc, tr, tc, ar, ac = move
        new_board = board.copy()
        new_board[fr, fc] = 0
        new_board[tr, tc] = player
        new_board[ar, ac] = -1
        return new_board
    
    def minimax(board, depth, alpha, beta, maximizing):
        player = 1 if maximizing else 2
        moves = get_all_moves(board, player)
        
        if depth == 0 or not moves:
            return evaluate(board), None
        
        if maximizing:
            max_eval = float('-inf')
            best_move = moves[0] if moves else None
            for move in moves:
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
            best_move = moves[0] if moves else None
            for move in moves:
                new_board = apply_move(board, move, 2)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    moves = get_all_moves(board, 1)
    
    if not moves:
        amazons = list(zip(*np.where(board == 1)))
        if amazons:
            r, c = amazons[0]
            return f"{r},{c}:{r},{c}:{r},{c}"
        return "0,0:0,0:0,0"
    
    depth = 2
    if len(moves) < 50:
        depth = 3
    if len(moves) < 20:
        depth = 4
    
    _, best_move = minimax(board.copy(), depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        best_move = moves[0]
    
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
