
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    A simple Hex policy that prioritizes moves close to existing stones and the center of the board.
    """

    board_size = 11

    def get_neighbors(row: int, col: int) -> list[tuple[int, int]]:
        """
        Returns a list of valid neighbors for a given cell.
        """
        neighbors = []
        for i in range(max(0, row - 1), min(board_size, row + 2)):
            for j in range(max(0, col - 1), min(board_size, col + 2)):
                if (i, j) != (row, col) and (i, j) != (row -1, col - 1) and (i, j) != (row + 1, col + 1):
                    neighbors.append((i, j))
        return neighbors

    def get_legal_moves(me: list[tuple[int, int]], opp: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """
        Returns a list of legal moves (empty cells) on the board.
        """
        all_cells = set((r, c) for r in range(board_size) for c in range(board_size))
        occupied_cells = set(me + opp)
        return list(all_cells - occupied_cells)

    legal_moves = get_legal_moves(me, opp)

    if not legal_moves:
        return (0, 0)  # Should never happen, but handle empty board.

    # Opening moves
    if not me and not opp:
        if color == 'b':
             return (5,5)
        else:
            return (5, 6) # or any other decent opening move

    if len(me) == 1 and len(opp) == 1:
        if color == 'b':
            return (5, 4) # counter attack for black
        else:
          return (6, 6)

    # Heuristic: Prioritize moves close to existing stones
    move_scores = {}
    for move in legal_moves:
        row, col = move
        score = 0
        for my_stone in me:
            stone_row, stone_col = my_stone
            distance = abs(row - stone_row) + abs(col - stone_col)
            score += 1.0 / (distance + 1) # Inverse distance

        # Prioritize the center of the board
        score += 0.5 / ((abs(row - board_size // 2) + abs(col - board_size // 2)) + 1)
        move_scores[move] = score

    best_move = max(move_scores, key=move_scores.get)


    # Random legal move as fallback
    return best_move
