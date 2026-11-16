
import numpy as np
from typing import List, Tuple

def policy(board) -> str:
    # Find all your amazons (player 1)
    your_amazons = np.where(board == 1)
    your_amazons = list(zip(your_amazons[0], your_amazons[1]))
    
    # Direction vectors for queen moves: 8 directions
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    legal_moves = []
    
    # For each amazon, try all possible moves and arrow shots
    for from_r, from_c in your_amazons:
        # Try all possible destinations for the amazon (queen moves)
        for dr, dc in directions:
            # Explore along this direction until blocked
            for step in range(1, 6):  # max 5 steps on 6x6 board
                to_r = from_r + dr * step
                to_c = from_c + dc * step
                
                # Check bounds
                if not (0 <= to_r < 6 and 0 <= to_c < 6):
                    break
                
                # If the destination is not empty, we cannot move there
                if board[to_r, to_c] != 0:
                    break
                
                # Now, from (to_r, to_c), try to shoot an arrow in all 8 directions
                for adr, adc in directions:
                    for arrow_step in range(1, 6):
                        arrow_r = to_r + adr * arrow_step
                        arrow_c = to_c + adc * arrow_step
                        
                        # Check bounds
                        if not (0 <= arrow_r < 6 and 0 <= arrow_c < 6):
                            break
                        
                        # The arrow path must be clear: cannot go through any non-empty square
                        # But note: the from square is now empty, so it's fair game
                        # Check if we hit a blocker before arrow_r, arrow_c
                        blocked = False
                        for s in range(1, arrow_step+1):
                            check_r = to_r + adr * s
                            check_c = to_c + adc * s
                            # Blockers: opponent amazon (2), arrow (-1), or other your amazon (1)
                            # But note: our original from square is now free (vacated)
                            if check_r == from_r and check_c == from_c:
                                continue  # this square is empty now, so it's OK
                            
                            if board[check_r, check_c] != 0:
                                blocked = True
                                break
                        
                        if blocked:
                            continue
                        
                        # Check if arrow lands on a legal square (must be empty)
                        if board[arrow_r, arrow_c] != 0:
                            continue  # cannot land on non-empty square
                        
                        # Valid move! Record it
                        move_str = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
                        legal_moves.append(move_str)
    
    # Since we must always return a legal move, and we've collected all legal moves,
    # we now choose one. Implement a simple heuristic: pick the move that maximizes
    # the number of legal moves for the player in the next state (i.e., after making this move).
    
    if not legal_moves:
        # This should never happen per problem constraints, but for safety
        # Fallback: return the first possible move we can think of (shouldn't be reached)
        # Try brute force again to find ANY move (just in case)
        for from_r, from_c in your_amazons:
            for dr, dc in directions:
                for step in range(1, 6):
                    to_r = from_r + dr * step
                    to_c = from_c + dc * step
                    if not (0 <= to_r < 6 and 0 <= to_c < 6):
                        break
                    if board[to_r, to_c] != 0:
                        break
                    # Try first arrow direction: straight right
                    arrow_r, arrow_c = to_r, to_c + 1
                    if 0 <= arrow_r < 6 and 0 <= arrow_c < 6 and board[arrow_r, arrow_c] == 0:
                        # Check path from (to_r, to_c) to (arrow_r, arrow_c) is clear
                        if from_r == to_r and from_c + 1 == arrow_c:  # moved right, arrow right
                            # Path is just one step, and from square is vacated
                            move_str = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
                            return move_str
                    # Try any other fixed direction, just to return something
                    for arrow_step in range(1, 2):  # just one step
                        for adr, adc in directions:
                            arrow_r = to_r + adr * arrow_step
                            arrow_c = to_c + adc * arrow_step
                            if not (0 <= arrow_r < 6 and 0 <= arrow_c < 6):
                                continue
                            # Check if arrow path is clear (only one step)
                            if (arrow_r == from_r and arrow_c == from_c) or board[arrow_r, arrow_c] == 0:
                                # One step, and it's empty or over vacated from square
                                # Check if we are shooting through occupied? Only step so must be empty
                                if board[arrow_r, arrow_c] == 0:
                                    move_str = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
                                    return move_str
        # If we get here, something is horribly wrong, return a dummy move
        return "0,0:1,0:2,0"
    
    # If we have legal moves, choose the one that leads to the most future moves
    best_move = legal_moves[0]
    best_score = -1
    
    for move in legal_moves:
        # Parse the move: "from_r,from_c:to_r,to_c:arrow_r,arrow_c"
        parts = move.split(':')
        from_coord = parts[0].split(',')
        to_coord = parts[1].split(',')
        arrow_coord = parts[2].split(',')
        
        from_r, from_c = int(from_coord[0]), int(from_coord[1])
        to_r, to_c = int(to_coord[0]), int(to_coord[1])
        arrow_r, arrow_c = int(arrow_coord[0]), int(arrow_coord[1])
        
        # Create a simulated board after this move
        simulated_board = board.copy()
        # Vacate the original position
        simulated_board[from_r, from_c] = 0
        # Place amazon at new position
        simulated_board[to_r, to_c] = 1
        # Shoot arrow
        simulated_board[arrow_r, arrow_c] = -1
        
        # Count number of legal moves for player in this new state
        score = count_legal_moves(simulated_board)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def count_legal_moves(board) -> int:
    """Count the number of legal moves for the player (player 1) on the given board."""
    your_amazons = np.where(board == 1)
    your_amazons = list(zip(your_amazons[0], your_amazons[1]))
    
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    count = 0
    
    for from_r, from_c in your_amazons:
        for dr, dc in directions:
            for step in range(1, 6):
                to_r = from_r + dr * step
                to_c = from_c + dc * step
                
                if not (0 <= to_r < 6 and 0 <= to_c < 6):
                    break
                if board[to_r, to_c] != 0:
                    break
                
                # Try all arrow directions
                for adr, adc in directions:
                    for arrow_step in range(1, 6):
                        arrow_r = to_r + adr * arrow_step
                        arrow_c = to_c + adc * arrow_step
                        
                        if not (0 <= arrow_r < 6 and 0 <= arrow_c < 6):
                            break
                        
                        # Check if arrow path is clear from (to_r, to_c) to (arrow_r, arrow_c)
                        blocked = False
                        for s in range(1, arrow_step+1):
                            check_r = to_r + adr * s
                            check_c = to_c + adc * s
                            
                            if (check_r == from_r and check_c == from_c):
                                continue  # vacated square, OK
                            
                            if board[check_r, check_c] != 0:
                                blocked = True
                                break
                        
                        if blocked:
                            continue
                        
                        # Must land on empty
                        if board[arrow_r, arrow_c] != 0:
                            continue
                        
                        count += 1
    
    return count
