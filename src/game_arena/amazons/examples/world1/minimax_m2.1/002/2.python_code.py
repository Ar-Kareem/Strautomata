
import numpy as np

def policy(board) -> str:
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    # Find our amazons
    our_positions = []
    for i in range(6):
        for j in range(6):
            if board[i,j] == 1:
                our_positions.append((i,j))
    
    candidate_moves = []
    
    # Generate candidate moves
    for (from_i, from_j) in our_positions:
        for dx,dy in directions:
            step = 1
            while True:
                to_i = from_i + dx*step
                to_j = from_j + dy*step
                if to_i < 0 or to_i>=6 or to_j<0 or to_j>=6:
                    break
                if board[to_i, to_j] != 0: # blocked
                    break
                # Create a new board for the move
                new_board_move = board.copy()
                new_board_move[from_i, from_j] = 0
                new_board_move[to_i, to_j] = 1
                
                # Now generate arrow shots from (to_i, to_j)
                for arrow_dx, arrow_dy in directions:
                    arrow_step = 1
                    while True:
                        arrow_i = to_i + arrow_dx*arrow_step
                        arrow_j = to_j + arrow_dy*arrow_step
                        if arrow_i<0 or arrow_i>=6 or arrow_j<0 or arrow_j>=6:
                            break
                        if new_board_move[arrow_i, arrow_j] != 0:
                            break
                        candidate_moves.append((from_i, from_j, to_i, to_j, arrow_i, arrow_j))
                        arrow_step += 1
                step += 1
    
    if len(candidate_moves) == 0:
        # Fallback: try to move the first amazon to an adjacent square and then shoot an arrow to an adjacent square
        for (from_i, from_j) in our_positions:
            for dx,dy in directions:
                to_i = from_i+dx
                to_j = from_j+dy
                if to_i in range(6) and to_j in range(6) and board[to_i,to_j]==0:
                    # Shoot arrow in same direction first
                    arrow_i = to_i+dx
                    arrow_j = to_j+dy
                    if arrow_i in range(6) and arrow_j in range(6) and board[arrow_i,arrow_j]==0:
                        return f"{from_i},{from_j}:{to_i},{to_j}:{arrow_i},{arrow_j}"
                    else:
                        # Try other directions for arrow
                        for arrow_dx, arrow_dy in directions:
                            if arrow_dx==dx and arrow_dy==dy:
                                continue
                            arrow_i = to_i+arrow_dx
                            arrow_j = to_j+arrow_dy
                            if arrow_i in range(6) and arrow_j in range(6) and board[arrow_i,arrow_j]==0:
                                return f"{from_i},{from_j}:{to_i},{to_j}:{arrow_i},{arrow_j}"
        # If still no move found, return a default move (should rarely happen)
        return "0,0:0,1:0,2"
    
    # Define function to count simple mobility for a player
    def count_moves_simple(board, player):
        count = 0
        for i in range(6):
            for j in range(6):
                if board[i,j] == player:
                    for dx,dy in directions:
                        step = 1
                        while True:
                            ni = i + dx*step
                            nj = j + dy*step
                            if ni<0 or ni>=6 or nj<0 or nj>=6:
                                break
                            if board[ni, nj] != 0:
                                break
                            count += 1
                            step += 1
        return count
    
    best_move = None
    best_score = -10**9
    
    for move in candidate_moves:
        from_i, from_j, to_i, to_j, arrow_i, arrow_j = move
        # Simulate the move
        new_board = board.copy()
        new_board[from_i, from_j] = 0
        new_board[to_i, to_j] = 1
        new_board[arrow_i, arrow_j] = -1
        
        our_mobility_simple = count_moves_simple(new_board, 1)
        opponent_mobility_simple = count_moves_simple(new_board, 2)
        
        # Center bonus
        center_bonus = 0
        if (to_i, to_j) in [(2,2),(2,3),(3,2),(3,3)]:
            center_bonus += 1000
        if (arrow_i, arrow_j) in [(2,2),(2,3),(3,2),(3,3)]:
            center_bonus += 500
        
        # Blocking bonus
        block_bonus = 0
        opponent_positions = []
        for i in range(6):
            for j in range(6):
                if new_board[i,j] == 2:
                    opponent_positions.append((i,j))
        
        for (opp_i, opp_j) in opponent_positions:
            # Check if arrow is in same row, column, or diagonal
            if arrow_i == opp_i and arrow_j > opp_j:
                dx, dy = 0, 1
            elif arrow_i == opp_i and arrow_j < opp_j:
                dx, dy = 0, -1
            elif arrow_j == opp_j and arrow_i > opp_i:
                dx, dy = 1, 0
            elif arrow_j == opp_j and arrow_i < opp_i:
                dx, dy = -1, 0
            elif arrow_i > opp_i and arrow_j > opp_j and (arrow_i-opp_i)==(arrow_j-opp_j):
                dx, dy = 1, 1
            elif arrow_i > opp_i and arrow_j < opp_j and (arrow_i-opp_i)==(opp_j-arrow_j):
                dx, dy = 1, -1
            elif arrow_i < opp_i and arrow_j > opp_j and (opp_i-arrow_i)==(arrow_j-opp_j):
                dx, dy = -1, 1
            elif arrow_i < opp_i and arrow_j < opp_j and (opp_i-arrow_i)==(opp_j-arrow_j):
                dx, dy = -1, -1
            else:
                continue  # Not in straight line
            
            # Traverse from opponent amazon to arrow position
            step = 1
            blocked = False
            while True:
                next_i = opp_i + dx*step
                next_j = opp_j + dy*step
                if next_i == arrow_i and next_j == arrow_j:
                    blocked = True
                    break
                if new_board[next_i, next_j] != 0:
                    break
                step += 1
            if blocked:
                block_bonus += 500
        
        score = 100 * our_mobility_simple - 50 * opponent_mobility_simple + center_bonus + block_bonus
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Convert best_move to string format
    from_i, from_j, to_i, to_j, arrow_i, arrow_j = best_move
    return f"{from_i},{from_j}:{to_i},{to_j}:{arrow_i},{arrow_j}"
