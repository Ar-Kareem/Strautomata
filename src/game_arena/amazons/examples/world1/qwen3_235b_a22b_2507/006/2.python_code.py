
import numpy as np
from typing import List, Tuple, Optional

def policy(board: np.ndarray) -> str:
    # Directions: 8 queen-like directions
    DIRS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    def is_valid(r: int, c: int) -> bool:
        return 0 <= r < 6 and 0 <= c < 6

    def path_clear(brd: np.ndarray, r: int, c: int, dr: int, dc: int, steps: int) -> bool:
        for i in range(1, steps + 1):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid(nr, nc) or brd[nr, nc] != 0:
                return False
        return True

    def legal_moves(brd: np.ndarray, player: int) -> List[Tuple[int, int, int, int, int, int]]:
        amazons = []
        opp = 3 - player
        for r in range(6):
            for c in range(6):
                if brd[r, c] == player:
                    amazons.append((r, c))
        
        moves = []
        for r, c in amazons:
            for dr, dc in DIRS:
                for step in range(1, 6):
                    nr, nc = r + dr * step, c + dc * step
                    if not is_valid(nr, nc):
                        break
                    if brd[nr, nc] != 0:
                        break
                    # Now from (nr, nc), shoot arrow
                    for adr, adc in DIRS:
                        for astep in range(1, 6):
                            ar, ac = nr + adr * astep, nc + adc * astep
                            if not is_valid(ar, ac):
                                break
                            if brd[ar, ac] != 0 and (ar, ac) != (r, c):  # arrow path blocked, except it can pass through original pos
                                break
                            # Valid move and shot
                            moves.append((r, c, nr, nc, ar, ac))
        return moves

    def evaluate(brd: np.ndarray) -> int:
        # Simple mobility heuristic: count legal moves for each player
        my_moves = len(legal_moves(brd, 1))
        opp_moves = len(legal_moves(brd, 2))
        if my_moves == 0:
            return -10000  # losing
        if opp_moves == 0:
            return 10000  # winning
        return my_moves - opp_moves  # prefer higher mobility

    def minimax(brd: np.ndarray, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        if depth == 0:
            return evaluate(brd)
        
        moves = legal_moves(brd, 1 if maximizing else 2)
        if not moves:
            return -10000 if maximizing else 10000

        # Move ordering: sort by estimated mobility improvement
        move_scores = []
        for move in moves:
            sim_board = brd.copy()
            fr, fc, tr, tc, ar, ac = move
            sim_board[fr, fc] = 0
            sim_board[tr, tc] = 1 if maximizing else 2
            sim_board[ar, ac] = -1
            score = evaluate(sim_board)
            move_scores.append((score, move))
        # Prioritize better moves for pruning
        move_scores.sort(reverse=True if maximizing else False)

        if maximizing:
            value = -np.inf
            for score, move in move_scores:
                sim_board = brd.copy()
                fr, fc, tr, tc, ar, ac = move
                sim_board[fr, fc] = 0
                sim_board[tr, tc] = 1
                sim_board[ar, ac] = -1
                value = max(value, minimax(sim_board, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = np.inf
            for score, move in move_scores:
                sim_board = brd.copy()
                fr, fc, tr, tc, ar, ac = move
                sim_board[fr, fc] = 0
                sim_board[tr, tc] = 2
                sim_board[ar, ac] = -1
                value = min(value, minimax(sim_board, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    # Main logic
    legal_moves_list = legal_moves(board, 1)
    if not legal_moves_list:
        # Fallback: shouldn't happen, but just in case
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if is_valid(nr, nc) and board[nr, nc] == 0:
                            for adr, adc in DIRS:
                                ar, ac = nr + adr, nc + adc
                                if is_valid(ar, ac) and (board[ar, ac] == 0 or (ar == r and ac == c)):
                                    return f"{r},{c}:{nr},{nc}:{ar},{ac}"

    # Order moves by heuristic before searching
    scored_moves = []
    for move in legal_moves_list:
        sim_board = board.copy()
        fr, fc, tr, tc, ar, ac = move
        sim_board[fr, fc] = 0
        sim_board[tr, tc] = 1
        sim_board[ar, ac] = -1
        score = evaluate(sim_board)
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(reverse=True)
    
    # Search top moves only to save time
    best_move = scored_moves[0][1]
    best_value = -np.inf
    for score, move in scored_moves[:10]:  # Limit branching factor
        sim_board = board.copy()
        fr, fc, tr, tc, ar, ac = move
        sim_board[fr, fc] = 0
        sim_board[tr, tc] = 1
        sim_board[ar, ac] = -1
        value = minimax(sim_board, depth=1, alpha=-np.inf, beta=np.inf, maximizing=False)
        if value > best_value:
            best_value = value
            best_move = move

    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
