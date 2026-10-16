
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    all_empty = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in me_set and (i, j) not in opp_set:
                all_empty.append((i, j))
    
    adj_dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    best_score = -float('inf')
    best_move = None
    
    for cell in all_empty:
        i, j = cell
        
        if color == 'b':
            pos_score = i * (10 - i)
        else:
            pos_score = j * (10 - j)
        
        adj_score = 0
        for di, dj in adj_dirs:
            ni, nj = i + di, j + dj
            if 0 <= ni < 11 and 0 <= nj < 11 and (ni, nj) in me_set:
                adj_score += 1
        
        total_score = pos_score + adj_score * 5
        
        if total_score > best_score:
            best_score = total_score
            best_move = cell
    
    return best_move
