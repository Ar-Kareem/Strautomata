
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    from typing import List, Tuple
    
    start = time.time()
    
    def is_terminal(state: List[int], opp: List[int]) -> bool:
        return all(h == 0 for h in state[:6]) or all(h == 0 for h in opp[:6])
    
    def get_legal_moves(state: List[int]) -> List[int]:
        return [i for i in range(6) if state[i] > 0]
    
    def sow(state: List[int], opp: List[int], move: int) -> Tuple[List[int], List[int], bool]:
        s, o = state[:], opp[:]
        seeds = s[move]
        s[move] = 0
        pos = (move + 1) % 13
        last, last_mine = -1, False
        
        while seeds:
            if pos < 6:
                s[pos] += 1
                last, last_mine = pos, True
            elif pos == 6:
                s[6] += 1
                last, last_mine = 6, True
            else:
                o[pos - 7] += 1
                last, last_mine = pos - 7, False
            seeds -= 1
            pos = (pos + 1) % 13
        
        if last_mine and last < 6 and s[last] == 1:
            idx = 5 - last
            if o[idx]:
                s[6] += s[last] + o[idx]
                s[last] = o[idx] = 0
        
        return s, o, last_mine and last == 6
    
    def evaluate(state: List[int], opp: List[int]) -> float:
        store_diff = state[6] - opp[6]
        my_seeds, opp_seeds = sum(state[:6]), sum(opp[:6])
        
        my_extra = sum(1 for i in range(6) if state[i] and (i + state[i]) % 13 == 6)
        opp_extra = sum(1 for i in range(6) if opp[i] and (i + opp[i]) % 13 == 6)
        
        my_cap = 0
        for i in range(6):
            if state[i]:
                final = (i + state[i]) % 13
                if final < 6 and (final == i or state[final] == 0) and opp[5 - final]:
                    my_cap += opp[5 - final]
        
        opp_cap = 0
        for i in range(6):
            if opp[i]:
                final = (i + opp[i]) % 13
                if final < 6 and (final == i or opp[final] == 0) and state[5 - final]:
                    opp_cap += state[5 - final]
        
        return 8*store_diff + my_seeds - opp_seeds + 3*(my_extra - opp_extra) + 0.3*(my_cap - opp_cap)
    
    def minimax(state: List[int], opp: List[int], depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, int]:
        if time.time() - start > 0.95:
            return evaluate(state, opp), -1
        if is_terminal(state, opp):
            return state[6] - opp[6], -1
        if depth == 0:
            return evaluate(state, opp), -1
        
        moves = get_legal_moves(state if maximizing else opp)
        
        if maximizing:
            best, best_move = -float('inf'), moves[0]
            for m in moves:
                ns, no, extra = sow(state, opp, m)
                score, _ = minimax(ns, no, depth - 1, alpha, beta, extra)
                if score > best:
                    best, best_move = score, m
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return best, best_move
        else:
            best = float('inf')
            for m in moves:
                no, ns, extra = sow(opp, state, m)
                score, _ = minimax(ns, no, depth - 1, alpha, beta, not extra)
                if score < best:
                    best = score
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return best, -1
    
    moves = get_legal_moves(you)
    if len(moves) == 1:
        return moves[0]
    
    for m in moves:
        final = (m + you[m]) % 13
        if final == 6:
            return m
        if final < 6 and (final == m or you[final] == 0) and opponent[5 - final]:
            return m
    
    total = sum(you) + sum(opponent)
    max_depth = 6 if total > 36 else 8 if total > 24 else 10
    
    best = moves[0]
    for d in range(1, max_depth + 1):
        _, m = minimax(you, opponent, d, -float('inf'), float('inf'), True)
        if m >= 0:
            best = m
    
    return best
