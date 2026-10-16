
import random
import math
import time
from collections import defaultdict, deque

class HexBoard:
    def __init__(self, size=11):
        self.size = size
        self.board = [[None for _ in range(size)] for _ in range(size)]
        self.me = set()
        self.opp = set()
        self.color = None
        self.opp_color = None

    def set_state(self, me, opp, color):
        self.me = set(me)
        self.opp = set(opp)
        self.color = color
        self.opp_color = 'w' if color == 'b' else 'b'
        self._update_board()

    def _update_board(self):
        for i in range(self.size):
            for j in range(self.size):
                if (i, j) in self.me:
                    self.board[i][j] = self.color
                elif (i, j) in self.opp:
                    self.board[i][j] = self.opp_color
                else:
                    self.board[i][j] = None

    def get_neighbors(self, i, j):
        neighbors = []
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.size and 0 <= nj < self.size:
                neighbors.append((ni, nj))
        return neighbors

    def is_empty(self, i, j):
        return self.board[i][j] is None

    def is_winning_move(self, i, j, color):
        if not self.is_empty(i, j):
            return False

        # Temporarily place the stone
        self.board[i][j] = color

        # Check for connection
        visited = set()
        if color == 'b':
            # Check top to bottom connection
            for col in range(self.size):
                if self.board[0][col] == color:
                    if self._dfs(0, col, color, visited):
                        self.board[i][j] = None
                        return True
        else:
            # Check left to right connection
            for row in range(self.size):
                if self.board[row][0] == color:
                    if self._dfs(row, 0, color, visited):
                        self.board[i][j] = None
                        return True

        self.board[i][j] = None
        return False

    def _dfs(self, i, j, color, visited):
        if (i, j) in visited:
            return False
        visited.add((i, j))

        if color == 'b' and i == self.size - 1:
            return True
        if color == 'w' and j == self.size - 1:
            return True

        for ni, nj in self.get_neighbors(i, j):
            if self.board[ni][nj] == color and self._dfs(ni, nj, color, visited):
                return True
        return False

    def get_legal_moves(self):
        return [(i, j) for i in range(self.size) for j in range(self.size) if self.is_empty(i, j)]

    def make_move(self, move, color):
        if move in self.me or move in self.opp:
            return False
        if color == self.color:
            self.me.add(move)
        else:
            self.opp.add(move)
        self._update_board()
        return True

    def copy(self):
        new_board = HexBoard(self.size)
        new_board.me = self.me.copy()
        new_board.opp = self.opp.copy()
        new_board.color = self.color
        new_board.opp_color = self.opp_color
        new_board._update_board()
        return new_board

class MCTSNode:
    def __init__(self, board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = board.get_legal_moves()

    def uct_select_child(self):
        log_parent_visits = math.log(self.visits)

        def uct_score(child):
            exploit = child.wins / child.visits
            explore = math.sqrt(2 * log_parent_visits / child.visits)
            return exploit + explore

        return max(self.children, key=uct_score)

    def add_child(self, move, board):
        child = MCTSNode(board, parent=self, move=move)
        self.untried_moves.remove(move)
        self.children.append(child)
        return child

    def update(self, result):
        self.visits += 1
        self.wins += result

def policy(me, opp, color):
    board = HexBoard()
    board.set_state(me, opp, color)

    # First check for immediate winning moves
    for move in board.get_legal_moves():
        if board.is_winning_move(move[0], move[1], color):
            return move

    # Then check for immediate blocking moves
    opp_color = 'w' if color == 'b' else 'b'
    for move in board.get_legal_moves():
        if board.is_winning_move(move[0], move[1], opp_color):
            return move

    # If no immediate win/block, use MCTS to find best move
    start_time = time.time()
    root = MCTSNode(board)

    while time.time() - start_time < 0.8:  # Leave some time for final move selection
        node = root
        temp_board = board.copy()

        # Selection
        while node.untried_moves == [] and node.children != []:
            node = node.uct_select_child()
            temp_board.make_move(node.move, board.color if (node.parent.visits + node.visits) % 2 == 0 else opp_color)

        # Expansion
        if node.untried_moves != []:
            move = random.choice(node.untried_moves)
            temp_board.make_move(move, board.color if node.visits % 2 == 0 else opp_color)
            node = node.add_child(move, temp_board)

        # Simulation
        current_board = temp_board.copy()
        current_color = board.color if node.visits % 2 == 0 else opp_color
        while True:
            legal_moves = current_board.get_legal_moves()
            if not legal_moves:
                break

            # Simple playout policy: prioritize moves near our stones and edges
            if random.random() < 0.7:
                # Try to connect to our stones
                our_stones = current_board.me if current_color == board.color else current_board.opp
                if our_stones:
                    # Find moves adjacent to our stones
                    adjacent_moves = []
                    for stone in our_stones:
                        for neighbor in current_board.get_neighbors(stone[0], stone[1]):
                            if current_board.is_empty(neighbor[0], neighbor[1]):
                                adjacent_moves.append(neighbor)
                    if adjacent_moves:
                        move = random.choice(adjacent_moves)
                    else:
                        move = random.choice(legal_moves)
                else:
                    move = random.choice(legal_moves)
            else:
                move = random.choice(legal_moves)

            current_board.make_move(move, current_color)
            current_color = opp_color if current_color == board.color else board.color

            # Check for win
            if current_color == board.color:
                for i in range(current_board.size):
                    if current_board.board[i][0] == current_color and current_board._dfs(i, 0, current_color, set()):
                        result = 1 if current_color == board.color else 0
                        break
                else:
                    continue
            else:
                for j in range(current_board.size):
                    if current_board.board[0][j] == current_color and current_board._dfs(0, j, current_color, set()):
                        result = 1 if current_color == board.color else 0
                        break
                else:
                    continue
            break
        else:
            result = 0.5  # Draw

        # Backpropagation
        while node is not None:
            node.update(result)
            node = node.parent
            result = 1 - result

    # Select the move with the highest visit count
    best_move = max(root.children, key=lambda c: c.visits).move
    return best_move
