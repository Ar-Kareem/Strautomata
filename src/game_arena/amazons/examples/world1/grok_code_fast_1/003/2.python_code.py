
import numpy as np

def get_possible_moves(board, r, c):
    """Return list of (nr, nc) where the piece at (r,c) can move to empty squares."""
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves

def get_possible_arrows(board_after_move, to_r, to_c):
    """Return list of (nar, nac) where the arrow can be shot from (to_r, to_c) to empty squares."""
    arrows = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        nar, nac = to_r + dr, to_c + dc
        while 0 <= nar < 6 and 0 <= nac < 6:
            if board_after_move[nar, nac] == 0:
                arrows.append((nar, nac))
                nar += dr
                nac += dc
            else:
                break
    return arrows

def policy(board) -> str:
    # Find positions of my Amazons and opponent's Amazons
    my_positions = [(i, j) for i in range(6) for j in range(6) if board[i, j] == 1]
    opp_positions = [(i, j) for i in range(6) for j in range(6) if board[i, j] == 2]
    
    best_move = None
    best_score = -float('inf')
    
    for from_r, from_c in my_positions:
        possible_moves = get_possible_moves(board, from_r, from_c)
        for to_r, to_c in possible_moves:
            # Simulate the board after moving the Amazon
            board_after = np.copy(board)
            board_after[to_r, to_c] = 1
            board_after[from_r, from_c] = 0
            
            # Get possible arrow shots from the new position
            possible_arrows = get_possible_arrows(board_after, to_r, to_c)
            for ar_r, ar_c in possible_arrows:
                # Simulate the final board after shooting the arrow
                board_final = np.copy(board_after)
                board_final[ar_r, ar_c] = -1
                
                # Update my positions after the move
                my_pos_after = [p for p in my_positions if p != (from_r, from_c)] + [(to_r, to_c)]
                
                # Calculate my reachable moves (total empty squares I can reach)
                my_reach = sum(len(get_possible_moves(board_final, pr, pc)) for pr, pc in my_pos_after)
                
                # Calculate opponent's reachable moves
                opp_reach = sum(len(get_possible_moves(board_final, pr, pc)) for pr, pc in opp_positions)
                
                # Score: my reach - opponent's reach
                score = my_reach - opp_reach
                
                if score > best_score:
                    best_score = score
                    best_move = "f{from_r},{from_c}:{to_r},{to_c}:{ar_r},{ar_c}"
    
    # If no moves were found (though the environment should prevent this), return a default, but this won't happen as the code only runs if there are moves
    if best_move is None:
        raise ValueError("No legal moves available – this should not happen based on problem constraints.")
    
    return best_move
