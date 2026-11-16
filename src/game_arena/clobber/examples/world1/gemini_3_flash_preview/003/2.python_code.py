
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert lists to numpy arrays for easier indexing (5x6)
    me = np.array(you).reshape(5, 6)
    them = np.array(opponent).reshape(5, 6)
    
    legal_moves = []
    directions = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    
    # Identify all legal moves
    for r in range(5):
        for c in range(6):
            if me[r, c] == 1:
                for dr, dc, dname in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6:
                        if them[nr, nc] == 1:
                            legal_moves.append((r, c, dname, nr, nc))

    if not legal_moves:
        return "0,0,U" # Should not happen based on game rules
    
    best_move = legal_moves[0]
    best_score = -float('inf')

    # Simple heuristic: maximize (our_potential_moves - opponent_potential_moves)
    for move in legal_moves:
        r, c, dname, nr, nc = move
        
        # Simulate move
        new_me = me.copy()
        new_them = them.copy()
        new_me[r, c] = 0
        new_me[nr, nc] = 1
        new_them[nr, nc] = 0
        
        my_future_moves = 0
        their_future_moves = 0
        
        # Count potential moves for both sides in the next state
        for row in range(5):
            for col in range(6):
                # My future moves
                if new_me[row, col] == 1:
                    for dr, dc, _ in directions:
                        tr, tc = row + dr, col + dc
                        if 0 <= tr < 5 and 0 <= tc < 6 and new_them[tr, tc] == 1:
                            my_future_moves += 1
                # Opponent future moves
                if new_them[row, col] == 1:
                    for dr, dc, _ in directions:
                        tr, tc = row + dr, col + dc
                        if 0 <= tr < 5 and 0 <= tc < 6 and new_me[tr, tc] == 1:
                            their_future_moves += 1
                            
        score = my_future_moves - their_future_moves
        if score > best_score:
            best_score = score
            best_move = move

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
