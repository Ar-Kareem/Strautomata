
def policy(board: list[list[int]]) -> tuple[int, int]:
    import numpy as np
    
    # Define line directions (horizontal, vertical, diagonal, anti-diagonal)
    lines = [
        # Horizontal
        [(i,0),(i,1),(i,2),(i,3)] for i in range(4)
    ] + [
        # Vertical
        [(0,j),(1,j),(2,j),(3,j)] for j in range(4)
    ] + [
        # Diagonals
        [(i,i) for i in range(4)],
        [(i,3-i) for i in range(4)]
    ]
    
    # 1. Check for immediate wins
    win_moves = []
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                # Check if this move completes a line with our piece
                our_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                opp_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                # Check all line directions
                for line in lines:
                    # Count our and opponent pieces in the line
                    our_count = sum(board[x][y] == 1 for x,y in line)
                    opp_count = sum(board[x][y] == -1 for x,y in line)
                    if board[row][col] == 0 and our_count == 2 and opp_count == 0:
                        # This move would complete our line
                        if our_count == 2:  # 2 of ours and 0 opponent's
                            win_moves.append((row, col))
    
    # 2. Check for immediate blocks (opponent's win threats)
    block_moves = []
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                # Check if this move blocks opponent's win
                our_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                opp_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                for line in lines:
                    our_count = sum(board[x][y] == 1 for x,y in line)
                    opp_count = sum(board[x][y] == -1 for x,y in line)
                    if board[row][col] == 0 and opp_count == 2 and our_count == 0:
                        # This move would block opponent's line
                        if opp_count == 2:  # 2 of theirs and 0 ours
                            block_moves.append((row, col))
    
    # 3. Check for fork creation opportunities
    fork_moves = []
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                # This move could create two winning lines
                our_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                opp_lines = [1 for _ in [(row,0),(row,1),(row,2),(row,3)]]
                potential_wins = []
                for line in lines:
                    our_count = sum(board[x][y] == 1 for x,y in line)
                    opp_count = sum(board[x][y] == -1 for x,y in line)
                    if board[row][col] == 0:
                        # Simulate placing our piece here
                        temp_board = [list(r) for r in board]
                        temp_board[row][col] = 1
                        temp_wins = []
                        for t_line in lines:
                            t_our = sum(temp_board[x][y] == 1 for x,y in t_line)
                            t_opp = sum(temp_board[x][y] == -1 for x,y in t_line)
                            if t_our == 2 and t_opp == 0:  # Winning threat
                                temp_wins.append(t_line)
                        if len(temp_wins) >= 2:
                            # This creates multiple winning threats
                            fork_moves.append((row, col))
    
    # 4. Prioritize based on our strategic priorities
    if win_moves:
        return win_moves[0]  # Win immediately
    
    if block_moves:
        return block_moves[0]  # Block opponent's immediate win
    
    if fork_moves:
        return fork_moves[0]  # Create a forced fork
    
    # 5. Heuristic evaluation for remaining moves
    center_moves = [(1,1), (1,2), (2,1), (2,2)]
    corner_moves = [(0,0), (0,3), (3,0), (3,3)]
    
    # Evaluate all empty positions
    best_move = None
    best_score = -float('inf')
    
    for row in range(4):
        for col in range(4):
            if board[row][col] != 0:
                continue
                
            # Calculate line participation score
            participation_score = 0
            for line in lines:
                our_count = sum(board[x][y] == 1 for x,y in line)
                opp_count = sum(board[x][y] == -1 for x,y in line)
                if row in [x for x,y in line] and col in [y for x,y in line]:
                    # This cell participates in the line
                    participation_score += (our_count + opp_count + 1)
            
            # Evaluate based on cell position
            if (row, col) in center_moves:
                position_score = 2
            elif (row, col) in corner_moves:
                position_score = 3
            else:
                position_score = 1  # Edge
                
            total_score = participation_score + position_score
            
            if total_score > best_score:
                best_score = total_score
                best_move = (row, col)
    
    return best_move
