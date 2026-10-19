
import random
import math
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize board state
    board_size = 19
    board = [[None for _ in range(board_size)] for _ in range(board_size)]

    # Mark stones on the board
    for (r, c) in me:
        board[r-1][c-1] = 'me'
    for (r, c) in opponent:
        board[r-1][c-1] = 'opponent'

    # Get all empty points
    empty_points = [(r+1, c+1) for r in range(board_size) for c in range(board_size) if board[r][c] is None]

    # If no empty points, pass
    if not empty_points:
        return (0, 0), memory

    # Check for urgent moves first
    urgent_move = check_urgent_moves(board, me, opponent)
    if urgent_move:
        return urgent_move, memory

    # Evaluate strategic positions
    strategic_move = evaluate_strategic_positions(board, me, opponent)
    if strategic_move:
        return strategic_move, memory

    # Fall back to simplified MCTS
    mcts_move = simplified_mcts(board, me, opponent)
    return mcts_move, memory

def check_urgent_moves(board, me, opponent):
    # Check for stones in atari (1 liberty)
    for stone in me:
        r, c = stone[0]-1, stone[1]-1
        if count_liberties(board, r, c) == 1:
            # Find the liberty and play there to save the stone
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] is None:
                    return (nr+1, nc+1)

    # Check for opponent stones in atari that we can capture
    for stone in opponent:
        r, c = stone[0]-1, stone[1]-1
        if count_liberties(board, r, c) == 1:
            # Find the liberty and play there to capture
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] is None:
                    return (nr+1, nc+1)

    return None

def evaluate_strategic_positions(board, me, opponent):
    best_move = None
    best_score = -float('inf')

    # Evaluate all empty points
    for r in range(19):
        for c in range(19):
            if board[r][c] is None:
                score = evaluate_position(board, r, c, me, opponent)
                if score > best_score:
                    best_score = score
                    best_move = (r+1, c+1)

    return best_move

def evaluate_position(board, r, c, me, opponent):
    score = 0

    # Check if this move connects our groups
    connected_groups = 0
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 'me':
            connected_groups += 1
    score += connected_groups * 10

    # Check if this move threatens opponent groups
    threatened_groups = 0
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 'opponent':
            if count_liberties(board, nr, nc) <= 2:
                threatened_groups += 1
    score += threatened_groups * 15

    # Check if this move is in an empty area (potential territory)
    empty_neighbors = 0
    for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] is None:
            empty_neighbors += 1
    score += empty_neighbors * 5

    return score

def count_liberties(board, r, c):
    if board[r][c] is None:
        return 0

    color = board[r][c]
    visited = set()
    stack = [(r, c)]
    liberties = 0

    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))

        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19:
                if board[nx][ny] is None:
                    liberties += 1
                elif board[nx][ny] == color and (nx, ny) not in visited:
                    stack.append((nx, ny))

    return liberties

def simplified_mcts(board, me, opponent, iterations=100):
    root = MCTSNode(board, me, opponent)
    for _ in range(iterations):
        node = root
        # Selection
        while node.children and not node.is_terminal():
            node = node.select_child()

        # Expansion
        if not node.is_terminal():
            node.expand()

        # Simulation
        result = node.simulate()

        # Backpropagation
        while node is not None:
            node.update(result)
            node = node.parent

    # Return the most visited child
    if root.children:
        return max(root.children, key=lambda c: c.visits).move
    else:
        # If no children (shouldn't happen), return a random move
        empty_points = [(r+1, c+1) for r in range(19) for c in range(19) if board[r][c] is None]
        return random.choice(empty_points) if empty_points else (0, 0)

class MCTSNode:
    def __init__(self, board, me, opponent, move=None, parent=None):
        self.board = [row[:] for row in board]
        self.me = me[:]
        self.opponent = opponent[:]
        self.move = move
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = self.get_legal_moves()

    def get_legal_moves(self):
        moves = []
        for r in range(19):
            for c in range(19):
                if self.board[r][c] is None:
                    moves.append((r+1, c+1))
        return moves

    def select_child(self):
        # UCB1 formula
        log_parent_visits = math.log(self.visits)
        def ucb_score(child):
            if child.visits == 0:
                return float('inf')
            return (child.wins / child.visits) + math.sqrt(2 * log_parent_visits / child.visits)
        return max(self.children, key=ucb_score)

    def expand(self):
        if not self.untried_moves:
            return

        move = self.untried_moves.pop()
        new_board = [row[:] for row in self.board]
        new_me = self.me[:]
        new_opponent = self.opponent[:]

        # Apply the move
        r, c = move[0]-1, move[1]-1
        new_board[r][c] = 'me'
        new_me.append(move)

        # Create child node
        child = MCTSNode(new_board, new_me, new_opponent, move, self)
        self.children.append(child)
        return child

    def simulate(self):
        # Simple random playout
        current_board = [row[:] for row in self.board]
        current_me = self.me[:]
        current_opponent = self.opponent[:]

        # Apply our move if this is not the root
        if self.move:
            r, c = self.move[0]-1, self.move[1]-1
            current_board[r][c] = 'me'
            current_me.append(self.move)

        # Play random moves until game ends
        while True:
            # Get all legal moves
            legal_moves = []
            for r in range(19):
                for c in range(19):
                    if current_board[r][c] is None:
                        legal_moves.append((r+1, c+1))

            if not legal_moves:
                break

            # Random move
            move = random.choice(legal_moves)
            r, c = move[0]-1, move[1]-1

            # Alternate players
            if len(current_me) > len(current_opponent):
                current_board[r][c] = 'opponent'
                current_opponent.append(move)
            else:
                current_board[r][c] = 'me'
                current_me.append(move)

        # Simple evaluation: count territory
        me_territory = count_territory(current_board, 'me')
        opponent_territory = count_territory(current_board, 'opponent')

        # Return 1 if we win, 0 if draw, -1 if lose
        if me_territory > opponent_territory:
            return 1
        elif me_territory < opponent_territory:
            return -1
        else:
            return 0

    def update(self, result):
        self.visits += 1
        self.wins += result

    def is_terminal(self):
        return not self.untried_moves and not self.children

def count_territory(board, player):
    territory = 0
    visited = set()

    for r in range(19):
        for c in range(19):
            if board[r][c] is None and (r, c) not in visited:
                # BFS to find empty region
                queue = [(r, c)]
                region = []
                is_territory = True

                while queue:
                    x, y = queue.pop(0)
                    if (x, y) in visited:
                        continue
                    visited.add((x, y))
                    region.append((x, y))

                    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 19 and 0 <= ny < 19:
                            if board[nx][ny] is None and (nx, ny) not in visited:
                                queue.append((nx, ny))
                            elif board[nx][ny] != player:
                                is_territory = False

                if is_territory:
                    territory += len(region)

    return territory
