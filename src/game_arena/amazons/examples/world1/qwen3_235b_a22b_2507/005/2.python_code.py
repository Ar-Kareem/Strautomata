
import numpy as np
from typing import List, Tuple, Optional
import random

def policy(board) -> str:
    """
    Main policy function. Returns a move string in format: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    Implements a 2-ply minimax with alpha-beta pruning and a mobility-based heuristic.
    """
    
    def get_directions():
        """Returns 8 queen-like movement directions."""
        return [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    def is_in_bounds(r: int, c: int) -> bool:
        return 0 <= r < 6 and 0 <= c < 6
    
    def is_path_clear(board: np.ndarray, fr: int, fc: int, tr: int, tc: int) -> bool:
        """Check if path from (fr,fc) to (tr,tc) is clear (queen move)."""
        if fr == tr and fc == tc:
            return False
        dr = tr - fr
        dc = tc - fc
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        r, c = fr + step_r, fc + step_c
        while (r, c) != (tr, tc):
            if board[r, c] != 0:  # blocked
                return False
            r += step_r
            c += step_c
        return True

    def get_moves_for_amazon(board: np.ndarray, r: int, c: int) -> List[Tuple[int,int,int,int,int,int]]:
        """Generate all legal moves (to_r, to_c, ar_r, ar_c) from (r,c)."""
        moves = []
        directions = get_directions()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while is_in_bounds(nr, nc) and board[nr, nc] == 0:
                # Now from (nr, nc), shoot arrow in any direction
                for adr, adc in directions:
                    ar_r, ar_c = nr + adr, nc + adc
                    while is_in_bounds(ar_r, ar_c) and (ar_r != r or ar_c != c or (board[ar_r, ar_c] == 0)):
                        if board[ar_r, ar_c] != 0 and (ar_r, ar_c) != (r, c):  # arrow lands on non-empty or own vacated
                            break
                        moves.append((r, c, nr, nc, ar_r, ar_c))
                        ar_r += adr
                        ar_c += adc
                nr += dr
                nc += dc
        return moves

    def get_all_legal_moves(board: np.ndarray, player: int) -> List[str]:
        """Returns list of move strings for given player."""
        moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == player:
                    piece_moves = get_moves_for_amazon(board, r, c)
                    for fm in piece_moves:
                        move_str = f"{fm[0]},{fm[1]}:{fm[2]},{fm[3]}:{fm[4]},{fm[5]}"
                        moves.append(move_str)
        return moves

    def execute_move(board: np.ndarray, move_str: str) -> np.ndarray:
        """Apply move to board and return new board."""
        board_copy = board.copy()
        parts = move_str.split(':')
        from_part = parts[0].split(',')
        to_part = parts[1].split(',')
        arrow_part = parts[2].split(',')
        fr, fc = int(from_part[0]), int(from_part[1])
        tr, tc = int(to_part[0]), int(to_part[1])
        ar_r, ar_c = int(arrow_part[0]), int(arrow_part[1])
        
        # Move amazon
        board_copy[fr, fc] = 0
        board_copy[tr, tc] = 1 if board[fr,fc] == 1 else 2  # preserve player
        board_copy[ar_r, ar_c] = -1  # arrow
        return board_copy

    def evaluate(board: np.ndarray) -> int:
        """Heuristic: (own mobility) - 1.2*(opponent mobility) + small center bonus."""
        my_moves = get_all_legal_moves(board, 1)
        opp_moves = get_all_legal_moves(board, 2)
        score = len(my_moves) - 1.2 * len(opp_moves)
        
        # Center bonus for our amazons
        center = [(2,2), (2,3), (3,2), (3,3)]
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    if (r, c) in center:
                        score += 0.25
        return score

    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax with alpha-beta pruning. Depth 0 is our move."""
        if depth == 0:
            return evaluate(board)
        
        if maximizing:
            max_eval = -np.inf
            moves = get_all_legal_moves(board, 1)  # our moves
            if not moves:
                return -1000  # losing
            for move in moves:
                new_board = execute_move(board, move)
                ev = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = np.inf
            moves = get_all_legal_moves(board, 2)  # opponent moves
            if not moves:
                return 1000  # winning
            for move in moves:
                new_board = execute_move(board, move)
                ev = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval

    # Get all legal moves for player 1
    legal_moves = get_all_legal_moves(board, 1)
    if not legal_moves:
        # Should not happen, but for safety pick any amazon and try random valid shot (fallback)
        # In practice, return first possible move
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    # try to move one step in any direction
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            if dr == 0 and dc == 0:
                                continue
                            tr, tc = r + dr, c + dc
                            if is_in_bounds(tr, tc) and board[tr, tc] == 0:
                                # shoot arrow one step further
                                for adr in [-1,0,1]:
                                    for adc in [-1,0,1]:
                                        if adr == 0 and adc == 0:
                                            continue
                                        ar_r, ar_c = tr + adr, tc + adc
                                        if is_in_bounds(ar_r, ar_c) and board[ar_r, ar_c] == 0:
                                            return f"{r},{c}:{tr},{tc}:{ar_r},{ar_c}"
    # Sort moves roughly by center proximity for better pruning
    def move_center_score(move_str):
        parts = move_str.split(':')[1].split(',')
        tr, tc = int(parts[0]), int(parts[1])
        center_dist = abs(tr - 2.5) + abs(tc - 2.5)
        return -center_dist  # prefer center
    
    # Order moves for better pruning
    legal_moves.sort(key=move_center_score, reverse=True)
    
    # Use 2-ply search if time allows (pruning helps keep it fast)
    best_move = legal_moves[0]  # always have fallback
    best_value = -np.inf
    depth = 2  # 2-ply: we move, opponent moves, evaluate
    
    for move in legal_moves:
        new_board = execute_move(board, move)
        value = minimax(new_board, depth - 1, -np.inf, np.inf, False)
        if value > best_value:
            best_value = value
            best_move = move

    return best_move
