
import numpy as np

def policy(board):
    # Define all 8 possible directions for queen moves
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    
    # Iterate through each cell to find my amazons
    for fy in range(6):
        for fx in range(6):
            if board[fy, fx] == 1:
                # Explore all movement directions
                for (dy, dx) in directions:
                    # Check steps in this direction until blocked
                    for k in range(1, 6):
                        ty = fy + dy * k
                        tx = fx + dx * k
                        # Check if within bounds
                        if ty < 0 or ty >= 6 or tx < 0 or tx >= 6:
                            break
                        # Destination must be empty
                        if board[ty, tx] != 0:
                            break
                        # Check path is clear
                        path_clear = True
                        for j in range(1, k):
                            y = fy + dy * j
                            x = fx + dx * j
                            if board[y, x] != 0:
                                path_clear = False
                                break
                        if not path_clear:
                            break
                        # Now check arrow shots from (ty, tx)
                        for (ady, adx) in directions:
                            # Check steps in this arrow direction
                            for l in range(1, 6):
                                ay = ty + ady * l
                                ax = tx + adx * l
                                # Check bounds
                                if ay < 0 or ay >=6 or ax <0 or ax >=6:
                                    break
                                # Arrow destination must be empty
                                if board[ay, ax] != 0:
                                    break
                                # Check arrow path is clear, allowing from square
                                arrow_path_clear = True
                                for m in range(1, l):
                                    y = ty + ady * m
                                    x = tx + adx * m
                                    if y == fy and x == fx:
                                        continue  # from square is empty now
                                    if board[y, x] != 0:
                                        arrow_path_clear = False
                                        break
                                if arrow_path_clear:
                                    # Found valid move
                                    return f"{fy},{fx}:{ty},{tx}:{ay},{ax}"
    # Fallback (shouldn't be reached per problem statement)
    return "0,0:0,0:0,0"  # Placeholder, but validated moves ensure this is never used
