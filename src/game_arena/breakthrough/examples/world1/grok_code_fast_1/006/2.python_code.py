
import numpy as np
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    def get_home_row(color: str) -> int:
        return 7 if color == 'w' else 0
    
    def get_direction(color: str) -> int:
        return 1 if color == 'w' else -1
    
    def get_opp_color(color: str) -> str:
        return 'w' if color == 'b' else 'b'
    
    def is_win(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> bool:
        home = get_home_row(color)
        return any(r == home for r, c in me) or len(opp) == 0
    
    def generate_moves(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        moves = []
        opp_set = set(opp)
        me_set = set(me)
        dir = get_direction(color)
        for r, c in me:
            to_r = r + dir
            if not (0 <= to_r <= 7):
                continue
            # straight
            if (to_r, c) not in me_set and (to_r, c) not in opp_set:
                moves.append(((r, c), (to_r, c)))
            # diagonal left
            if c > 0:
                to_c = c - 1
                if (to_r, to_c) not in me_set:
                    moves.append(((r, c), (to_r, to_c)))
            # diagonal right
            if c < 7:
                to_c = c + 1
                if (to_r, to_c) not in me_set:
                    moves.append(((r, c), (to_r, to_c)))
        # Sort by captures first
        def is_capture(move):
            fr, to = move
            return to in opp_set
        moves.sort(key=is_capture, reverse=True)
        return moves
    
    def apply_move(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], move: Tuple[Tuple[int, int], Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        fr, to = move
        new_me = [p for p in me if p != fr] + [to]
        new_opp = [p for p in opp if p != to]
        return new_me, new_opp
    
    def evaluate(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> int:
        def piece_value(r: int, c: int, color: str) -> int:
            base = r if color == 'w' else 7 - r
            return base + (1 if 3 <= c <= 4 else 0)
        val = sum(piece_value(r, c, color) for r, c in me) - sum(piece_value(r, c, color) for r, c in opp)
        return val
    
    INF = 10000
    WIN = INF
    LOSE = -INF
    
    def minimax(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        if depth == 0:
            return evaluate(me, opp, color)
        if is_win(me, opp, color):
            return WIN
        if len(me) == 0 or len(opp) > 0 and is_win(opp, me, get_opp_color(color)):
            return LOSE
        moves = generate_moves(me, opp, color)
        if not moves:
            return LOSE
        if maximizing:
            max_eval = -INF
            for move in moves:
                new_me, new_opp = apply_move(me, opp, move)
                eval_val = minimax(new_me, new_opp, get_opp_color(color), depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for move in moves:
                new_me, new_opp = apply_move(opp, me, move)  # note: for opponent, me and opp swapped
                eval_val = minimax(new_opp, new_me, color, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check for immediate win
    home = get_home_row(color)
    for r, c in me:
        to_r = r + get_direction(color)
        if to_r == home and (to_r, c) not in me and (to_r, c) not in set(opp):
            return ((r, c), (to_r, c))
        if c > 0 and (to_r, c-1) in set(opp) and to_r == home:
            return ((r, c), (to_r, c-1))
        if c < 7 and (to_r, c+1) in set(opp) and to_r == home:
            return ((r, c), (to_r, c+1))
    
    # Use minimax to select best move
    moves = generate_moves(me, opp, color)
    if not moves:
        # Assume always possible, but fallback to first piece straight if blocked (though rare)
        if me:
            r, c = me[0]
            dir = get_direction(color)
            to_r = r + dir
            if 0 <= to_r <= 7 and (to_r, c) not in set(opp) and (to_r, c) not in set(me):
                return ((r, c), (to_r, c))
        return ((0,0),(0,0))  # Shouldn't happen
    
    best_move = None
    best_val = -INF
    for move in moves:
        new_me, new_opp = apply_move(me, opp, move)
        val = minimax(new_me, new_opp, get_opp_color(color), 4, -INF, INF, False)
        if val > best_val:
            best_val = val
            best_move = move
    return best_move
