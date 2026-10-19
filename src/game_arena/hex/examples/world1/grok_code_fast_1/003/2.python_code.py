
import random
from collections import deque

def neighbors(i: int, j: int) -> list[tuple[int, int]]:
    ns = []
    for di, dj in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < 11 and 0 <= nj < 11:
            ns.append((ni, nj))
    return ns

def check_win(stones: set[tuple[int, int]], color: str) -> bool:
    if color == 'b':
        start_row = 0
        end_row = 10
        sources = [s for s in stones if s[0] == start_row]
        targets = set(s for s in stones if s[0] == end_row)
    else:  # color == 'w'
        start_col = 0
        end_col = 10
        sources = [s for s in stones if s[1] == start_col]
        targets = set(s for s in stones if s[1] == end_col)
    
    if not sources or not targets:
        return False
    
    visited = set()
    q = deque(sources)
    visited.update(sources)
    
    while q:
        curr = q.popleft()
        if curr in targets:
            return True
        for neigh in neighbors(*curr):
            if neigh in stones and neigh not in visited:
                q.append(neigh)
                visited.add(neigh)
    return False

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    all_stones = me_set | opp_set
    
    # Get empty cells
    empty = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in all_stones:
                empty.append((i, j))
    
    # Check if I can win
    for move in empty:
        new_me = me_set | {move}
        if check_win(new_me, color):
            return move
    
    # Check if I need to block opponent win
    opp_color = 'w' if color == 'b' else 'b'
    for move in empty:
        new_opp = opp_set | {move}
        if check_win(new_opp, opp_color):
            # Block this move by placing here
            return move
    
    # Otherwise, random move
    if empty:
        return random.choice(empty)
    else:
        # Should not happen, but just in case
        raise ValueError("No empty cells, but game should not reach here")
