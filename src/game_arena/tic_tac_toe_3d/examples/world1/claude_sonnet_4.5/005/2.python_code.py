
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Generate all winning lines in 3D tic-tac-toe
    def get_all_lines():
        lines = []
        
        # Lines parallel to each axis (27 lines total)
        for i in range(3):
            for j in range(3):
                # Lines parallel to z-axis
                lines.append([(i, j, k) for k in range(3)])
                # Lines parallel to y-axis
                lines.append([(i, k, j) for k in range(3)])
                # Lines parallel to x-axis
                lines.append([(k, i, j) for k in range(3)])
        
        # Diagonals on planes parallel to xy (6 lines)
        for i in range(3):
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
        
        # Diagonals on planes parallel to xz (6 lines)
        for j in range(3):
            lines.append([(i, j, i) for i in range(3)])
            lines.append([(i, j, 2-i) for i in range(3)])
        
        # Diagonals on planes parallel to yz (6 lines)
        for k in range(3):
            lines.append([(i, i, k) for i in range(3)])
            lines.append([(i, 2-i, k) for i in range(3)])
        
        # Space diagonals (4 main diagonals through the cube)
        lines.append([(i, i, i) for i in range(3)])
        lines.append([(i, i, 2-i) for i in range(3)])
        lines.append([(i, 2-i, i) for i in range(3)])
        lines.append([(2-i, i, i) for i in range(3)])
        
        return lines
    
    lines = get_all_lines()
    
    # Evaluate a potential move
    def evaluate_move(pos):
        x, y, z = pos
        if board[x][y][z] != 0:
            return -1000  # Invalid move
        
        score = 0
        
        # Check all lines that include this position
        for line in lines:
            if pos not in line:
                continue
            
            values = [board[i][j][k] for i, j, k in line]
            my_count = values.count(1)
            opp_count = values.count(-1)
            empty_count = values.count(0)
            
            # Check if this move wins
            if my_count == 2 and empty_count == 1:
                score += 1000
            
            # Check if this move blocks opponent's win
            if opp_count == 2 and empty_count == 1:
                score += 500
            
            # Two in a row for us
            if my_count == 1 and empty_count == 2:
                score += 10
            
            # Block opponent's potential
            if opp_count == 1 and empty_count == 2:
                score += 5
        
        # Prefer center and edge-centers
        if (x, y, z) == (1, 1, 1):
            score += 3
        elif [x, y, z].count(1) >= 2:
            score += 1
        
        return score
    
    # Find best move
    best_move = None
    best_score = -float('inf')
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    score = evaluate_move((i, j, k))
                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)
    
    return best_move if best_move else (0, 0, 0)
