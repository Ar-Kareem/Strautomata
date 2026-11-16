
import random
import math
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'phase': 'opening',  # opening, midgame, endgame
            'opening_moves': [],  # Track opening moves
            'last_move': None,   # Track last move to avoid ko
            'mcts_nodes': defaultdict(lambda: {'visits': 0, 'wins': 0, 'children': {}}),
            'board_size': 19,
            'move_count': 0,
        }
    memory['move_count'] += 1

    # Convert stones to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opponent)

    # Check if game is nearly over (endgame)
    if memory['move_count'] > 150 or len(my_stones) + len(opp_stones) > 200:
        memory['phase'] = 'endgame'
    elif memory['move_count'] <= 30:
        memory['phase'] = 'opening'
    else:
        memory['phase'] = 'midgame'

    # Generate all legal moves (including pass)
    legal_moves = [(0, 0)]  # pass is always legal
    for row in range(1, 20):
        for col in range(1, 20):
            if (row, col) not in my_stones and (row, col) not in opp_stones:
                # Check if placing here is legal (no suicide)
                if is_legal_move(my_stones, opp_stones, (row, col)):
                    legal_moves.append((row, col))

    # Choose move based on phase
    if memory['phase'] == 'opening':
        move = choose_opening_move(my_stones, opp_stones, memory)
    elif memory['phase'] == 'midgame':
        move = choose_midgame_move(my_stones, opp_stones, memory, legal_moves)
    else:  # endgame
        move = choose_endgame_move(my_stones, opp_stones, memory, legal_moves)

    # Update memory
    memory['last_move'] = move
    return move, memory

def is_legal_move(my_stones, opp_stones, move):
    """Check if placing a stone at `move` is legal (no suicide)."""
    if move == (0, 0):
        return True  # pass is always legal

    # Simulate placing the stone
    temp_my_stones = my_stones.copy()
    temp_my_stones.add(move)

    # Check if the move is suicide (no liberties)
    liberties = count_liberties(temp_my_stones, opp_stones, move)
    if liberties == 0:
        return False

    # Check for immediate ko (not implemented here for simplicity)
    return True

def count_liberties(my_stones, opp_stones, move):
    """Count liberties of the group containing `move`."""
    if move not in my_stones:
        return 0

    visited = set()
    stack = [move]
    liberties = 0

    while stack:
        stone = stack.pop()
        if stone in visited:
            continue
        visited.add(stone)

        # Check adjacent empty points
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (stone[0] + dr, stone[1] + dc)
            if 1 <= neighbor[0] <= 19 and 1 <= neighbor[1] <= 19:
                if neighbor not in my_stones and neighbor not in opp_stones:
                    liberties += 1
                elif neighbor in my_stones and neighbor not in visited:
                    stack.append(neighbor)

    return liberties

def choose_opening_move(my_stones, opp_stones, memory):
    """Choose a move based on standard opening patterns."""
    if not memory['opening_moves']:
        # First move: play center (3-4 point opening)
        return (9, 9)

    last_move = memory['opening_moves'][-1] if memory['opening_moves'] else (0, 0)
    move_count = len(memory['opening_moves'])

    # Simple opening sequence (can be expanded)
    if move_count == 1:
        return (9, 9)  # First move: center
    elif move_count == 2:
        return (3, 3)  # Second move: corner
    elif move_count == 3:
        return (17, 17)  # Third move: opposite corner
    elif move_count == 4:
        return (9, 10)  # Fourth move: approach
    else:
        # Default to random legal move if no pattern
        legal_moves = []
        for row in range(1, 20):
            for col in range(1, 20):
                if (row, col) not in my_stones and (row, col) not in opp_stones:
                    legal_moves.append((row, col))
        return random.choice(legal_moves)

def choose_midgame_move(my_stones, opp_stones, memory, legal_moves):
    """Choose a move using MCTS and pattern recognition."""
    # Simplified MCTS (UCT) for midgame
    if len(legal_moves) == 1:
        return legal_moves[0]  # only pass

    # Use MCTS to select a move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        if move == (0, 0):
            continue  # skip pass for now

        # Simulate MCTS (simplified)
        score = evaluate_move(my_stones, opp_stones, move, memory)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else (0, 0)

def evaluate_move(my_stones, opp_stones, move, memory):
    """Evaluate a move using pattern matching and MCTS."""
    if move == (0, 0):
        return 0  # pass has no score

    # Pattern matching (simplified)
    score = 0

    # Check if move is near opponent's stones (influence)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (move[0] + dr, move[1] + dc)
        if neighbor in opp_stones:
            score += 10  # influence bonus

    # Check liberties after placing the stone
    temp_my_stones = my_stones.copy()
    temp_my_stones.add(move)
    liberties = count_liberties(temp_my_stones, opp_stones, move)
    score += liberties * 2  # more liberties = better

    # Check if move captures opponent stones
    captured = set()
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (move[0] + dr, move[1] + dc)
        if neighbor in opp_stones:
            if count_liberties(opp_stones, my_stones, neighbor) == 0:
                captured.add(neighbor)
    score += len(captured) * 50  # capturing is very good

    return score

def choose_endgame_move(my_stones, opp_stones, memory, legal_moves):
    """Choose a move to secure territory in the endgame."""
    if (0, 0) in legal_moves and len(legal_moves) == 1:
        return (0, 0)  # pass if no moves left

    # Simple territory scoring
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        if move == (0, 0):
            continue

        # Simulate placing the stone and count potential territory
        temp_my_stones = my_stones.copy()
        temp_my_stones.add(move)
        score = count_territory(temp_my_stones, opp_stones, move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else (0, 0)

def count_territory(my_stones, opp_stones, move):
    """Count potential territory after placing a stone at `move`."""
    # Simplified: count empty points adjacent to my stones
    score = 0
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor = (move[0] + dr, move[1] + dc)
        if 1 <= neighbor[0] <= 19 and 1 <= neighbor[1] <= 19:
            if neighbor not in my_stones and neighbor not in opp_stones:
                score += 1
    return score
