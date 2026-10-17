
import numpy as np

def policy(board):
    # Get positions of my and opponent's amazons
    my_amazons = np.argwhere(board == 1).tolist()
    opponent_amazons = np.argwhere(board == 2).tolist()
    
    # All eight possible movement directions (queen moves)
    directions = [(dr, dc) for dr in (-1,0,1) for dc in (-1,0,1) if not (dr ==0 and dc==0)]
    
    legal_moves = []
    
    # Generate all legal moves
    for amazon in my_amazons:
        r, c = amazon
        for dr, dc in directions:
            # Check movement in this direction
            for step in range(1, 6):
                nr = r + dr * step
                nc = c + dc * step
                if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                    break
                if board[nr, nc] != 0:
                    break
                
                # Generate arrow shots from new position
                for adr, adc in directions:
                    for astep in range(1, 6):
                        ar = nr + adr * astep
                        ac = nc + adc * astep
                        if ar < 0 or ar >= 6 or ac < 0 or ac >= 6:
                            break
                        if board[ar, ac] != 0:
                            break
                        
                        # Verify arrow path is clear (allow passing through vacated from square)
                        path_ok = True
                        for i in range(1, astep + 1):
                            check_r = nr + adr * i
                            check_c = nc + adc * i
                            if (check_r, check_c) == (ar, ac):
                                break  # Reached arrow position (already checked empty)
                            if (check_r, check_c) == (r, c):
                                continue  # Vacated square is passable
                            if board[check_r, check_c] != 0:
                                path_ok = False
                                break
                        if not path_ok:
                            break
                        
                        legal_moves.append((r, c, nr, nc, ar, ac))
    
    # Scoring function to evaluate moves
    def score_move(move):
        _, _, tr, tc, ar, ac = move
        center_r, center_c = 2.5, 2.5  # Board center
        
        # Prefer moving closer to center
        move_centrality = - (abs(tr - center_r) + abs(tc - center_c))
        
        # Prefer arrows blocking opponents
        if opponent_amazons:
            min_opponent_dist = min(abs(ar - orow) + abs(ac - ocol) for orow, ocol in opponent_amazons)
        else:
            min_opponent_dist = 0
        arrow_score = - min_opponent_dist  # Closer to opponent is better
        
        # Weighted combination favoring move centrality
        total_score = move_centrality * 1.0 + arrow_score * 0.5
        return total_score
    
    # Select move with highest score
    best_move = max(legal_moves, key=score_move)
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
