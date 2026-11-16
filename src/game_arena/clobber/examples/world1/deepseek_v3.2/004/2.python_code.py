
import numpy as np
from collections import deque

def policy(you, opponent):
    you_arr = np.array(you, dtype=int)
    opp_arr = np.array(opponent, dtype=int)
    rows, cols = 5, 6
    
    # 1. Generate all legal moves
    moves = []
    for r in range(rows):
        for c in range(cols):
            if you_arr[r, c] == 0:
                continue
            # Up
            if r > 0 and opp_arr[r-1, c] == 1:
                moves.append((r, c, 'U'))
            # Down
            if r < rows-1 and opp_arr[r+1, c] == 1:
                moves.append((r, c, 'D'))
            # Left
            if c > 0 and opp_arr[r, c-1] == 1:
                moves.append((r, c, 'L'))
            # Right
            if c < cols-1 and opp_arr[r, c+1] == 1:
                moves.append((r, c, 'R'))
    
    if not moves:
        # Shouldn't happen (game already over), but fallback
        return "0,0,U"
    
    # 2. Endgame solver for small number of pieces
    total_pieces = np.sum(you_arr) + np.sum(opp_arr)
    if total_pieces <= 10:
        best_move = moves[0]
        best_score = -2  # -1 lose, 0 draw?, 1 win
        # Use memoized negamax
        memo = {}
        def board_to_tuple(y, o):
            return (tuple(y.flatten()), tuple(o.flatten()))
        
        def solve(y, o, player_turn):
            # player_turn: 1 for "you", -1 for "opponent" in this recursion
            key = (board_to_tuple(y, o), player_turn)
            if key in memo:
                return memo[key]
            # Generate moves for player_turn's side
            if player_turn == 1:
                yb, ob = y, o
            else:
                yb, ob = o, y  # swap perspective
            legal_mvs = []
            for rr in range(rows):
                for cc in range(cols):
                    if yb[rr, cc] == 0:
                        continue
                    for dr, dc, dchar in [(-1,0,'U'), (1,0,'D'), (0,-1,'L'), (0,1,'R')]:
                        nr, nc = rr+dr, cc+dc
                        if 0 <= nr < rows and 0 <= nc < cols and ob[nr, nc] == 1:
                            legal_mvs.append((rr, cc, dr, dc, dchar))
            if not legal_mvs:
                memo[key] = -1  # player to move loses
                return -1
            best = -1
            for rr, cc, dr, dc, dchar in legal_mvs:
                # make move
                new_y = yb.copy()
                new_o = ob.copy()
                new_y[rr, cc] = 0
                new_y[rr+dr, cc+dc] = 1
                new_o[rr+dr, cc+dc] = 0
                if player_turn == 1:
                    res = -solve(new_y, new_o, -1)
                else:
                    res = -solve(new_o, new_y, -1)  # swap back
                if res == 1:
                    memo[key] = 1
                    return 1
                if res == 0:
                    best = max(best, 0)
                else:
                    best = max(best, -1)
            memo[key] = best
            return best
        
        for r, c, d in moves:
            # apply move
            new_you = you_arr.copy()
            new_opp = opp_arr.copy()
            nr, nc = r, c
            if d == 'U':
                nr -= 1
            elif d == 'D':
                nr += 1
            elif d == 'L':
                nc -= 1
            elif d == 'R':
                nc += 1
            new_you[r, c] = 0
            new_you[nr, nc] = 1
            new_opp[nr, nc] = 0
            score = solve(new_you, new_opp, -1)  # opponent's turn now
            if score == -1:  # opponent loses -> immediate win
                return f"{r},{c},{d}"
            if score == 1:
                best_move = (r, c, d)
                best_score = 1
            elif score == 0 and best_score < 0:
                best_move = (r, c, d)
                best_score = 0
        # fallback: first move
        r, c, d = best_move
        return f"{r},{c},{d}"
    
    # 3. Midgame heuristic
    def connected_components(board):
        visited = np.zeros((rows, cols), dtype=bool)
        components = []
        for r in range(rows):
            for c in range(cols):
                if board[r, c] == 1 and not visited[r, c]:
                    # BFS
                    stack = [(r, c)]
                    comp = []
                    while stack:
                        cr, cc = stack.pop()
                        if visited[cr, cc]:
                            continue
                        visited[cr, cc] = True
                        comp.append((cr, cc))
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 1 and not visited[nr, nc]:
                                stack.append((nr, nc))
                    components.append(comp)
        return components
    
    def evaluate_move(r, c, d):
        nr, nc = r, c
        if d == 'U':
            nr -= 1
        elif d == 'D':
            nr += 1
        elif d == 'L':
            nc -= 1
        elif d == 'R':
            nc += 1
        # simulate
        new_you = you_arr.copy()
        new_opp = opp_arr.copy()
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opp[nr, nc] = 0
        # component sizes
        you_comp = connected_components(new_you)
        opp_comp = connected_components(new_opp)
        your_max = max(len(c) for c in you_comp) if you_comp else 0
        opp_max = max(len(c) for c in opp_comp) if opp_comp else 0
        # score: bigger your max component, smaller opponent's max component
        score = your_max - opp_max
        # also count how many moves you have after this
        your_moves = 0
        for rr in range(rows):
            for cc in range(cols):
                if new_you[rr, cc] == 0:
                    continue
                if rr > 0 and new_opp[rr-1, cc] == 1:
                    your_moves += 1
                if rr < rows-1 and new_opp[rr+1, cc] == 1:
                    your_moves += 1
                if cc > 0 and new_opp[rr, cc-1] == 1:
                    your_moves += 1
                if cc < cols-1 and new_opp[rr, cc+1] == 1:
                    your_moves += 1
        score += 0.1 * your_moves
        return score
    
    best_move = None
    best_score = -999
    for r, c, d in moves:
        sc = evaluate_move(r, c, d)
        if sc > best_score:
            best_score = sc
            best_move = (r, c, d)
    
    r, c, d = best_move
    return f"{r},{c},{d}"
