
import random
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    A Go policy that balances territory, influence, and local pattern recognition.
    Uses memory to track ko threats and board state.
    """
    # Initialize board state if memory is empty
    if not memory:
        memory = {
            'board': [[0 for _ in range(19)] for _ in range(19)],
            'last_move': None,
            'ko_positions': set(),
            'phase': 'opening',  # 'opening', 'middle', 'endgame'
            'move_count': 0,
        }

    # Helper functions
    def is_legal(move: Tuple[int, int]) -> bool:
        """Check if a move is legal (not on opponent stone, not off board)."""
        if move == (0, 0):
            return True  # Passing is always legal
        row, col = move
        if row < 1 or row > 19 or col < 1 or col > 19:
            return False
        if move in opponent:
            return False
        return True

    def get_liberties(stones: List[Tuple[int, int]], board: List[List[int]]) -> Dict[Tuple[int, int], int]:
        """Compute liberties for each stone group (using simple BFS)."""
        liberties = {}
        visited = set()
        for stone in stones:
            if stone in visited:
                continue
            group = set()
            queue = [stone]
            while queue:
                r, c = queue.pop()
                if (r, c) in visited or board[r-1][c-1] != 1:
                    continue
                visited.add((r, c))
                group.add((r, c))
                for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in visited:
                        if board[nr-1][nc-1] == 0:  # Empty point
                            queue.append((nr, nc))
                        elif board[nr-1][nc-1] == 1:  # Same color
                            queue.append((nr, nc))
            # Count liberties for the group
            liberty_count = 0
            for r, c in group:
                for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr-1][nc-1] == 0:
                        liberty_count += 1
            for stone in group:
                liberties[stone] = liberty_count
        return liberties

    def evaluate_move(move: Tuple[int, int], board: List[List[int]]) -> float:
        """Evaluate a move based on liberties, influence, and phase."""
        if move == (0, 0):
            return 0.0  # Passing has no immediate value

        row, col = move
        board_copy = [row[:] for row in board]
        board_copy[row-1][col-1] = 1  # Place our stone

        # Check if this move captures opponent stones
        opponent_liberties = get_liberties(opponent, board_copy)
        captures = sum(1 for stone in opponent_liberties if opponent_liberties[stone] == 0)
        if captures > 0:
            return 100.0 + captures  # High priority for captures

        # Check if opponent would capture us if they play next
        me_liberties = get_liberties(me, board_copy)
        if any(me_liberties[stone] == 0 for stone in me_liberties):
            return -100.0  # Suicide move (avoid)

        # Evaluate based on phase
        if memory['phase'] == 'opening':
            # Prefer star points and side centers
            star_points = [(3,3), (3,16), (16,3), (16,16), (4,4), (4,16), (16,4), (16,16), (13,3), (3,13), (13,16), (16,13)]
            if move in star_points:
                return 50.0
            # Prefer moves near opponent stones (influence)
            influence = sum(1 for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)] for r, c in opponent
                          if 1 <= (row + dr) <= 19 and 1 <= (col + dc) <= 19 and (row + dr, col + dc) == move)
            return 20.0 + influence

        elif memory['phase'] == 'middle':
            # Prefer moves that increase liberties or create potential
            liberties_gained = 0
            for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
                nr, nc = row + dr, col + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and board_copy[nr-1][nc-1] == 0:
                    liberties_gained += 1
            return 10.0 + liberties_gained

        else:  # endgame
            # Prefer filling opponent's weak points (single stones, thin extensions)
            weak_opponent = []
            for stone in opponent:
                liberties = get_liberties([stone], board_copy)
                if liberties[stone] <= 2:  # Single stone or thin extension
                    weak_opponent.append(stone)
            if move in weak_opponent:
                return 30.0
            # Prefer connecting our own stones
            connected = False
            for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
                nr, nc = row + dr, col + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19 and board_copy[nr-1][nc-1] == 1:
                    connected = True
                    break
            if connected:
                return 25.0
            return 5.0  # Default endgame value

    # Update board state
    if memory['last_move'] is not None:
        memory['board'][memory['last_move'][0]-1][memory['last_move'][1]-1] = 1
    memory['last_move'] = None

    # Place opponent's last move (if any)
    if 'opponent_last_move' in memory:
        opponent_row, opponent_col = memory['opponent_last_move']
        memory['board'][opponent_row-1][opponent_col-1] = 2
        memory['opponent_last_move'] = None

    # Place our stones on the board
    for r, c in me:
        memory['board'][r-1][c-1] = 1

    # Place opponent's stones on the board
    for r, c in opponent:
        memory['board'][r-1][c-1] = 2

    # Phase detection (simplified)
    memory['move_count'] += 1
    if memory['move_count'] <= 50:
        memory['phase'] = 'opening'
    elif memory['move_count'] <= 150:
        memory['phase'] = 'middle'
    else:
        memory['phase'] = 'endgame'

    # Generate candidate moves (all empty points)
    empty_points = []
    for r in range(1, 20):
        for c in range(1, 20):
            if memory['board'][r-1][c-1] == 0:
                empty_points.append((r, c))

    # If no empty points, pass
    if not empty_points:
        return (0, 0), memory

    # Evaluate all legal moves
    legal_moves = [move for move in empty_points if is_legal(move)]
    move_scores = {move: evaluate_move(move, memory['board']) for move in legal_moves}

    # Filter out moves that would be suicide (ko)
    if memory['phase'] != 'endgame':  # Avoid ko in endgame (simplified)
        for move in list(move_scores.keys()):
            if move_scores[move] < 0:
                del move_scores[move]

    # Select best move (or random if no clear winner)
    if not move_scores:
        return (0, 0), memory  # No legal moves (shouldn't happen)

    best_move = max(move_scores, key=move_scores.get)
    return best_move, memory
