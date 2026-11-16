
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship policy that combines random hunting with targeted attacks.
    """

    def get_neighbors(row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row - 1, col))
        if row < 9:
            neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row, col - 1))
        if col < 9:
            neighbors.append((row, col + 1))
        return neighbors

    def get_oriented_neighbors(row, col, orientation):
        neighbors = []
        if orientation == 'horizontal':
            if col > 0:
                neighbors.append((row, col - 1))
            if col < 9:
                neighbors.append((row, col + 1))
        elif orientation == 'vertical':
            if row > 0:
                neighbors.append((row - 1, col))
            if row < 9:
                neighbors.append((row + 1, col))
        return neighbors


    # Prioritize moves near hits
    potential_moves = []
    for row in range(10):
        for col in range(10):
            if board[row][col] == 1:
                neighbors = get_neighbors(row, col)
                for r, c in neighbors:
                    if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                        potential_moves.append((r, c))
            
            #Check for potential ship orientations if two hits are neighbors
            if board[row][col] == 1:
                #Horizontal check right
                if col < 9 and board[row][col+1] == 1:
                    for r, c in get_oriented_neighbors(row, col, 'horizontal'):
                         if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                            potential_moves.append((r, c))
                #Vertical check down
                if row < 9 and board[row+1][col] == 1:
                    for r, c in get_oriented_neighbors(row, col, 'vertical'):
                         if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                            potential_moves.append((r, c))     

    if potential_moves:
        return random.choice(potential_moves)


    # Random hunting with checkerboard pattern
    possible_moves = []
    for row in range(10):
        for col in range(10):
            if board[row][col] == 0 and (row + col) % 2 == 0:
                possible_moves.append((row, col))

    if possible_moves:
        return random.choice(possible_moves)
    

    # If no checkerboard spots are left, just pick any remaining unknown cell.
    for row in range(10):
        for col in range(10):
            if board[row][col] == 0:
                return (row, col)

    # If all cells have been targeted, return a random location (this should never happen in a proper game)
    return (0, 0)
