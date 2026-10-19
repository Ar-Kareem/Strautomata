
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic Tac Toe policy using strategic evaluation
    
    Args:
        board: 3x3x3 list of lists of lists
            0 = empty, 1 = our move, -1 = opponent's move
    
    Returns:
        tuple[int, int, int]: (i, j, k) coordinates of the move
    """
    
    def count_line(line: list) -> tuple:
        """
        Analyze a line for strategic evaluation
        Returns counts of (our marks, opponent marks, empty cells)
        """
        our_count = sum(1 for x in line if x == 1)
        opp_count = sum(1 for x in line if x == -1)
        empty_count = sum(1 for x in line if x == 0)
        return (our_count, opp_count, empty_count)
    
    def get_all_lines() -> list:
        """Generate all 49 possible winning lines in 3x3x3"""
        lines = []
        
        # Horizontal lines within each layer (9 lines)
        for i in range(3):
            for j in range(3):
                lines.append([board[i][j][0], board[i][j][1], board[i][j][2]])
        
        # Vertical lines through layers (9 lines)
        for i in range(3):
            for k in range(3):
                lines.append([board[i][0][k], board[i][1][k], board[i][2][k]])
        
        # Depth lines (9 lines)
        for j in range(3):
            for k in range(3):
                lines.append([board[0][j][k], board[1][j][k], board[2][j][k]])
        
        # Diagonals within each layer (6 lines)
        for i in range(3):
            # Main diagonals
            lines.append([board[i][0][0], board[i][1][1], board[i][2][2]])
            lines.append([board[i][0][2], board[i][1][1], board[i][2][0]])
        
        # Diagonals through layers (6 lines)
        for j in range(3):
            lines.append([board[0][j][0], board[1][j][1], board[2][j][2]])
            lines.append([board[0][j][2], board[1][j][1], board[2][j][0]])
        
        for k in range(3):
            lines.append([board[0][0][k], board[1][1][k], board[2][2][k]])
            lines.append([board[0][2][k], board[1][1][k], board[2][0][k]])
        
        # Space diagonals (4 lines)
        lines.append([board[0][0][0], board[1][1][1], board[2][2][2]])
        lines.append([board[0][0][2], board[1][1][1], board[2][2][0]])
        lines.append([board[0][2][0], board[1][1][1], board[2][0][2]])
        lines.append([board[0][2][2], board[1][1][1], board[2][0][0]])
        
        return lines
    
    def get_lines_through_cell(i: int, j: int, k: int) -> list:
        """Get all lines that pass through a specific cell"""
        lines = []
        
        # Horizontal line in this layer
        lines.append([board[i][j][0], board[i][j][1], board[i][j][2]])
        
        # Vertical line through this cell
        lines.append([board[i][0][k], board[i][1][k], board[i][2][k]])
        
        # Depth line
        lines.append([board[0][j][k], board[1][j][k], board[2][j][k]])
        
        # Layer diagonals
        lines.append([board[i][0][0], board[i][1][1], board[i][2][2]])
        lines.append([board[i][0][2], board[i][1][1], board[i][2][0]])
        
        # Vertical diagonals
        if j == 1:
            lines.append([board[0][j][0], board[1][j][1], board[2][j][2]])
            lines.append([board[0][j][2], board[1][j][1], board[2][j][0]])
        if k == 1:
            lines.append([board[0][0][k], board[1][1][k], board[2][2][k]])
            lines.append([board[0][2][k], board[1][1][k], board[2][0][k]])
        
        # Space diagonals (only for center and corners)
        if i == 1 and j == 1 and k == 1:
            lines.append([board[0][0][0], board[1][1][1], board[2][2][2]])
            lines.append([board[0][0][2], board[1][1][1], board[2][2][0]])
            lines.append([board[0][2][0], board[1][1][1], board[2][0][2]])
            lines.append([board[0][2][2], board[1][1][1], board[2][0][0]])
        elif i == 0 and j == 0 and k == 0:
            lines.append([board[0][0][0], board[1][1][1], board[2][2][2]])
        elif i == 0 and j == 0 and k == 2:
            lines.append([board[0][0][2], board[1][1][1], board[2][2][0]])
        elif i == 0 and j == 2 and k == 0:
            lines.append([board[0][2][0], board[1][1][1], board[2][0][2]])
        elif i == 0 and j == 2 and k == 2:
            lines.append([board[0][2][2], board[1][1][1], board[2][0][0]])
        elif i == 2 and j == 0 and k == 0:
            lines.append([board[0][0][0], board[1][1][1], board[2][2][2]])
        elif i == 2 and j == 0 and k == 2:
            lines.append([board[0][0][2], board[1][1][1], board[2][2][0]])
        elif i == 2 and j == 2 and k == 0:
            lines.append([board[0][2][0], board[1][1][1], board[2][0][2]])
        elif i == 2 and j == 2 and k == 2:
            lines.append([board[0][2][2], board[1][1][1], board[2][0][0]])
        
        return lines
    
    def cell_score(i: int, j: int, k: int) -> int:
        """Calculate strategic score for a cell position"""
        # Center cell is most valuable (part of 13 lines)
        if i == 1 and j == 1 and k == 1:
            return 100
        
        # Corner cells are highly valuable (part of 7 lines each)
        if (i in [0, 2]) and (j in [0, 2]) and (k in [0, 2]):
            return 50
        
        # Edge centers (part of 3 lines each)
        if sum(1 for x in [i, j, k] if x == 1) == 1:
            # Check if it's center of an edge vs corner of a face
            if (i == 1 and j in [0, 2] and k in [0, 2]) or \
               (j == 1 and i in [0, 2] and k in [0, 2]) or \
               (k == 1 and i in [0, 2] and j in [0, 2]):
                return 30
        
        # Edge edges (part of 4 lines each)
        return 10
    
    def evaluate_move(i: int, j: int, k: int) -> tuple:
        """
        Evaluate how good a move is
        Returns (win_opportunity, block_opportunity, strategic_score)
        """
        # Temporarily make the move
        original = board[i][j][k]
        board[i][j][k] = 1
        
        # Check if this move wins
        win_opportunity = 0
        lines = get_lines_through_cell(i, j, k)
        for line in lines:
            counts = count_line(line)
            if counts[0] == 3:  # We win
                win_opportunity = 1
                break
        
        # Restore the board
        board[i][j][k] = original
        
        # Check if this blocks opponent
        block_opportunity = 0
        lines = get_lines_through_cell(i, j, k)
        for line in lines:
            counts = count_line(line)
            if counts[1] == 2 and counts[2] == 1:  # Opponent has 2, we have 0
                block_opportunity = 1
                break
        
        strategic_score = cell_score(i, j, k)
        
        return (win_opportunity, block_opportunity, strategic_score)
    
    # Find all empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    
    # If no empty cells, return (0,0,0) as fallback
    if not empty_cells:
        return (0, 0, 0)
    
    # Find winning move
    for i, j, k in empty_cells:
        eval_result = evaluate_move(i, j, k)
        if eval_result[0] == 1:  # This move wins
            return (i, j, k)
    
    # Find blocking move
    for i, j, k in empty_cells:
        eval_result = evaluate_move(i, j, k)
        if eval_result[1] == 1:  # This blocks opponent win
            return (i, j, k)
    
    # Otherwise, choose based on strategic position
    best_move = None
    best_score = -1
    
    for i, j, k in empty_cells:
        eval_result = evaluate_move(i, j, k)
        score = eval_result[2]  # Strategic score
        
        if score > best_score:
            best_score = score
            best_move = (i, j, k)
    
    return best_move if best_move else empty_cells[0]
