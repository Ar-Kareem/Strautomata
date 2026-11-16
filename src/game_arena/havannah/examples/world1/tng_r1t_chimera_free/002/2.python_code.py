
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    def is_connected(stones, start, end):
        stone_set = set(stones)
        if start not in stone_set or end not in stone_set:
            return False
        visited = set()
        queue = [start]
        visited.add(start)
        directions = [(-1,0), (1,0), (0,-1), (-1,-1), (0,1), (-1,1)]
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            r, c = current
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                neighbor = (nr, nc)
                if 0 <= nr < 15 and 0 <= nc < 15 and neighbor in stone_set and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    corners = {(0,0), (0,14), (7,0), (7,14), (14,0), (14,14)}
    me_set = set(me)
    opp_set = set(opp)
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
                
    # Check for immediate bridge win
    for move in valid_moves:
        r, c = move
        new_me = me + [move]
        my_corners = [corner for corner in corners if corner in new_me]
        for i in range(len(my_corners)):
            for j in range(i+1, len(my_corners)):
                if is_connected(new_me, my_corners[i], my_corners[j]):
                    return move

    # Check for opponent's potential bridge win next turn
    for move in valid_moves:
        r, c = move
        new_opp = opp + [move]
        their_corners = [corner for corner in corners if corner in new_opp]
        for i in range(len(their_corners)):
            for j in range(i+1, len(their_corners)):
                if is_connected(new_opp, their_corners[i], their_corners[j]):
                    return move

    # Heuristic scoring for fallback
    max_score = -float('inf')
    best_move = valid_moves[0]
    for (r, c) in valid_moves:
        score = 0
        # Adjacency to own and opponent stones
        for dr, dc in [(-1,0), (1,0), (0,-1), (-1,-1), (0,1), (-1,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if (nr, nc) in me_set:
                    score += 2
                elif (nr, nc) in opp_set:
                    score -= 1
        # Strategic positions
        if (r, c) in corners:
            score += 5
        elif r == 0 or r == 14 or c == 0 or c == 14 or (r == 7 and (c == 0 or c == 14)):
            score += 3
        # Update best move
        if score > max_score or (score == max_score and (r, c) < best_move):
            max_score = score
            best_move = (r, c)
    return best_move
