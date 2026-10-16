
import sys
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Plays an optimal move for 4x4 Tic-Tac-Toe.
    The strategy follows a standard hierarchy:
    1. Win: If we have a winning move, take it.
    2. Block: If the opponent has a winning move, block it.
    3. Center: Take the strongest center positions (1,1), (1,2), (2,1), (2,2).
    4. Forks: Create or block forks (double threats).
    5. Sides: Take any available edge.
    6. Corners: Take any available corner (weakly prioritized).
    """
    
    N = 4
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    
    # Identify empty cells
    empty_cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))
    
    # Optimization: If board is full, we shouldn't be called, but handle gracefully
    if not empty_cells:
        return (-1, -1)

    # --- 1. WIN ---
    # Check if any move allows us to win immediately
    for r, c in empty_cells:
        board[r][c] = PLAYER
        if check_win(board, PLAYER):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # --- 2. BLOCK ---
    # Check if any move blocks opponent from winning
    for r, c in empty_cells:
        board[r][c] = OPPONENT
        if check_win(board, OPPONENT):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # --- 3. CENTER STRATEGY ---
    # Prioritize the 2x2 center block (r=1,2; c=1,2)
    # We sort empty cells so that center comes first.
    # Order: Center -> Corners -> Sides
    # Actually, standard Tic-Tac-Toe strategy suggests Center > Corners > Sides.
    
    def get_priority(r, c):
        # High priority for center 2x2
        if 1 <= r <= 2 and 1 <= c <= 2:
            return 0
        # Next priority for corners
        if (r == 0 or r == 3) and (c == 0 or c == 3):
            return 1
        # Lowest priority for edges
        return 2

    # Sort moves by priority (lower number is better)
    # Also add minor randomization for identical priorities to prevent predictability
    empty_cells.sort(key=lambda x: (get_priority(*x), random.random()))

    # We should check for forks before committing to center.
    # However, checking forks is computationally heavier.
    # Let's try to place a piece that creates a fork (we get 2 winning lines) 
    # or blocks a fork (opponent has 2 ways to win).
    
    # --- 4. FORKS ---
    # A fork is a position where a player has two non-blocked winning lines intersecting.
    # We simulate creating a fork.
    
    # We'll look for a move that gives us multiple threats.
    # Since board is small, we can do a deeper check on potential candidates.
    # We filter candidates to just center and corners first, as forks usually involve these.
    
    candidates = [cell for cell in empty_cells if get_priority(*cell) <= 1]
    if not candidates:
        candidates = empty_cells
    
    # Check for creating a fork
    # A fork usually means we have 2 lines where we are 1 away from winning (empty cell completes it).
    # Since we just checked for immediate Win (3 in a row), we look for 2 in a row with empty 3rd.
    
    best_fork_move = None
    
    for r, c in candidates:
        board[r][c] = PLAYER
        # Count how many winning opportunities we create
        threats = 0
        # Check all lines passing through (r, c)
        # Horizontal
        threats += count_threats(board, r, c, PLAYER)
        
        if threats >= 2:
            board[r][c] = EMPTY
            return (r, c) # Take the fork!
        board[r][c] = EMPTY

    # Check for blocking opponent fork
    # Opponent has a fork if they have 2 threats.
    # We should block one of the threats. However, if there are multiple forks, it's complex.
    # Simple 4x4 Tic-Tac-Toe heuristic:
    # If opponent has 2 potential winning lines intersecting at an empty cell, block it?
    # Actually, the standard check "Block Opponent" handles the immediate win.
    # If opponent has a fork setup (2 ways to win on next turn), we must block one of the lines.
    # BUT, we only have 1 move. So we pick the cell that intersects their threats.
    
    for r, c in candidates:
        board[r][c] = OPPONENT
        threats = count_threats(board, r, c, OPPONENT)
        if threats >= 2:
            board[r][c] = EMPTY
            return (r, c) # Block the fork intersection
        board[r][c] = EMPTY

    # --- 5. FALLBACK ---
    # If no special strategic moves, return the highest priority empty cell
    # We already sorted 'empty_cells', so the first one is best.
    return empty_cells[0]

def check_win(board, player):
    # Check rows and cols
    for i in range(4):
        if all(board[i][j] == player for j in range(4)): return True
        if all(board[j][i] == player for j in range(4)): return True
    # Check diagonals
    if all(board[i][i] == player for i in range(4)): return True
    if all(board[i][3-i] == player for i in range(4)): return True
    return False

def count_threats(board, r, c, player):
    # Count how many lines through (r,c) are one move away from winning (2 player + 1 empty)
    # Note: We don't count lines that are already blocked (have opponent piece)
    count = 0
    # Horizontal
    line = board[r]
    if sum(1 for x in line if x == player) == 2 and player not in line: # Basic check, need specific check for the specific line
        # Actually, let's just check the specific line.
        # We know (r,c) is currently set to player. We need 2 others that are player.
        # The line has 4 cells. If (r,c) is player, we need 2 more players and 1 empty.
        p_count = 0
        e_count = 0
        for x in line:
            if x == player: p_count += 1
            elif x == EMPTY: e_count += 1
            else: break # Opponent blocks
        else:
            if p_count == 2 and e_count == 1: count += 1
            
    # Vertical
    p_count = 0
    e_count = 0
    for i in range(4):
        x = board[i][c]
        if x == player: p_count += 1
        elif x == EMPTY: e_count = 0 # Reset, we need consecutive or just count?
        # Wait, for 4-in-a-row, we need 4. If we have 2 players and 1 empty in the 4, that's a threat.
        # But we need to handle disjoint? No, in 4x4, a threat is a line with 2 players and 2 empties?
        # No, a threat is usually 3 in a row in 3x3. In 4x4, usually 4 in a row is win.
        # So a threat is 3 in a row?
        # But standard 4x4 Tic Tac Toe is often played to 3 in a row (not 4), or 4 in a row.
        # Let's assume standard 4-in-a-row is the win condition, as per board size.
        # If win is 4 in a row, a threat is 3 in a row.
        # If win is 3 in a row (sub-game), it changes things.
        # Given the prompt, it says "Tic Tac Toe" on 4x4. Usually implies 4-in-a-row or match 3.
        # Let's assume standard 4-in-a-row rules.
        # A threat is 3 of the same symbol with 1 empty.
        # Let's check vertical.
        pass # Optimized below
    
    # Let's rewrite count_threats for 4-in-a-row:
    # A threat is a line with exactly 3 'player' and 1 'empty'.
    # Or if we have 2 'player' and 2 'empty', is that a threat?
    # In 4-in-a-row, 3 is a direct threat (win next move).
    # So we look for 3 players.
    
    # Re-implementation of count_threats specifically for finding "forks" (creating 2 threats)
    # A threat here means: I play here, and I create a line of 3.
    # But wait, if I play here, I am added to the line. So I need 2 other players in the line.
    # And the remaining cell must be empty.
    
    t_count = 0
    
    # Horizontal
    p = 0
    e = 0
    for j in range(4):
        if board[r][j] == player: p += 1
        elif board[r][j] == EMPTY: e += 1
        else: break # Blocked by opponent
    else:
        # Only count if we have 2 other players (since (r,c) is player, total 3) and 1 empty
        if p == 3 and e == 1: t_count += 1
        # Or if we are setting up for future? No, forks are about immediate multiple winning paths after move.
        # If we play (r,c), we have 3 in line if p==3.
        # If p==2 (and e==2), that's not a winning threat immediately.
        # However, forking is creating 2 lines that WILL be winning threats on next turn.
        # In 4-in-a-row, a line with 2 players + 2 empty isn't a win threat.
        # We need 3 players.
        # So, to create a fork, we need to move to an intersection where we have 2 lines with 2 players each?
        # And we become the 3rd?
        # Wait, in 4x4, "fork" usually means creating two threats of 3-in-a-row.
        # So we need the move to complete a line of 3? Or create 2 lines of 3?
        # If we are counting threats AFTER the move:
        # We need lines where there are 3 players.
        # If we played at (r,c), we are the player.
        # We check how many lines through (r,c) have 2 OTHER players and 1 empty.
        # This creates a line of 3. That is a win threat.
        # So we count lines with exactly 2 other players and 1 empty (excluding (r,c)).
        
        p = 0
        e = 0
        for j in range(4):
            if j == c: continue
            if board[r][j] == player: p += 1
            elif board[r][j] == EMPTY: e += 1
            else: break
        else:
            if p == 2 and e == 1: t_count += 1

    # Vertical
    p = 0
    e = 0
    for i in range(4):
        if i == r: continue
        if board[i][c] == player: p += 1
        elif board[i][c] == EMPTY: e += 1
        else: break
    else:
        if p == 2 and e == 1: t_count += 1

    # Diag 1 (Top-Left to Bottom-Right)
    # Check if (r,c) is on diag
    if r == c:
        p = 0
        e = 0
        for i in range(4):
            if i == r: continue
            if board[i][i] == player: p += 1
            elif board[i][i] == EMPTY: e += 1
            else: break
        else:
            if p == 2 and e == 1: t_count += 1

    # Diag 2 (Top-Right to Bottom-Left)
    if r + c == 3:
        p = 0
        e = 0
        for i in range(4):
            if i == r: continue
            if board[i][3-i] == player: p += 1
            elif board[i][3-i] == EMPTY: e += 1
            else: break
        else:
            if p == 2 and e == 1: t_count += 1
            
    return t_count
