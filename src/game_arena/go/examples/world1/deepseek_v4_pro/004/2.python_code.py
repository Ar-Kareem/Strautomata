
import random
import math
import time

class GoBoard:
    def __init__(self, me, opponent):
        # 21x21 board, index = row*21 + col
        self.board = [3] * 441  # 3 = border
        for r in range(1, 20):
            for c in range(1, 20):
                self.board[r*21+c] = 0
        for r, c in me:
            self.board[r*21+c] = 1
        for r, c in opponent:
            self.board[r*21+c] = 2
        self.ko = 0
        self.color = 1  # we are always 1
        self.visited = [0] * 441
        self.vis_token = 0
        self.queue = [0] * 441

    def copy(self):
        new_board = GoBoard.__new__(GoBoard)
        new_board.board = self.board.copy()
        new_board.ko = self.ko
        new_board.color = self.color
        new_board.visited = [0] * 441
        new_board.vis_token = 0
        new_board.queue = [0] * 441
        return new_board

    def count_liberties(self, pos):
        color = self.board[pos]
        if color == 0 or color == 3:
            return 0
        self.vis_token += 1
        token = self.vis_token
        queue = self.queue
        head = 0
        tail = 0
        queue[tail] = pos
        tail += 1
        self.visited[pos] = token
        liberties = 0
        while head < tail:
            cur = queue[head]
            head += 1
            for nbr in (cur-21, cur-1, cur+1, cur+21):
                if self.visited[nbr] == token:
                    continue
                val = self.board[nbr]
                if val == 0:
                    liberties += 1
                    self.visited[nbr] = token
                elif val == color:
                    self.visited[nbr] = token
                    queue[tail] = nbr
                    tail += 1
        return liberties

    def capture_group(self, pos, captured_list):
        color = self.board[pos]
        self.vis_token += 1
        token = self.vis_token
        queue = self.queue
        head = 0
        tail = 0
        queue[tail] = pos
        tail += 1
        self.visited[pos] = token
        while head < tail:
            cur = queue[head]
            head += 1
            self.board[cur] = 0
            captured_list.append(cur)
            for nbr in (cur-21, cur-1, cur+1, cur+21):
                if self.visited[nbr] == token:
                    continue
                if self.board[nbr] == color:
                    self.visited[nbr] = token
                    queue[tail] = nbr
                    tail += 1

    def play(self, move):
        if move == (0, 0):
            self.ko = 0
            self.color = 3 - self.color
            return True
        r, c = move
        idx = r*21 + c
        if self.board[idx] != 0:
            return False
        if idx == self.ko:
            return False
        self.board[idx] = self.color
        captured = []
        opp_color = 3 - self.color
        for nbr in (idx-21, idx-1, idx+1, idx+21):
            if self.board[nbr] == opp_color:
                if self.count_liberties(nbr) == 0:
                    self.capture_group(nbr, captured)
        if not captured and self.count_liberties(idx) == 0:
            self.board[idx] = 0
            return False
        if len(captured) == 1 and self.count_liberties(idx) == 1:
            self.ko = captured[0]
        else:
            self.ko = 0
        self.color = opp_color
        return True

    def is_legal(self, idx):
        if self.board[idx] != 0:
            return False
        if idx == self.ko:
            return False
        # fast check: if any neighbor is empty, it's not suicide
        for nbr in (idx-21, idx-1, idx+1, idx+21):
            if self.board[nbr] == 0:
                return True
        # No empty neighbor: need to check captures and suicide
        color = self.color
        opp_color = 3 - color
        self.board[idx] = color
        captures = False
        for nbr in (idx-21, idx-1, idx+1, idx+21):
            if self.board[nbr] == opp_color:
                if self.count_liberties(nbr) == 0:
                    captures = True
                    break
        if not captures:
            if self.count_liberties(idx) == 0:
                self.board[idx] = 0
                return False
        self.board[idx] = 0
        return True

    def legal_moves(self):
        moves = []
        for r in range(1, 20):
            for c in range(1, 20):
                idx = r*21 + c
                if self.is_legal(idx):
                    moves.append((r, c))
        moves.append((0, 0))  # pass
        return moves


class Node:
    def __init__(self, move, parent, color):
        self.move = move
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.value = 0.0
        self.untried_moves = None
        self.color = color


def evaluate(board):
    stones_me = 0
    stones_opp = 0
    territory_me = 0
    territory_opp = 0
    visited = [0] * 441
    for i in range(1, 20):
        for j in range(1, 20):
            idx = i*21 + j
            if board.board[idx] == 1:
                stones_me += 1
            elif board.board[idx] == 2:
                stones_opp += 1
            elif board.board[idx] == 0 and not visited[idx]:
                queue = [idx]
                visited[idx] = 1
                head = 0
                touches_me = False
                touches_opp = False
                region = [idx]
                while head < len(queue):
                    cur = queue[head]
                    head += 1
                    for nbr in (cur-21, cur-1, cur+1, cur+21):
                        val = board.board[nbr]
                        if val == 0:
                            if not visited[nbr]:
                                visited[nbr] = 1
                                queue.append(nbr)
                                region.append(nbr)
                        elif val == 1:
                            touches_me = True
                        elif val == 2:
                            touches_opp = True
                if touches_me and not touches_opp:
                    territory_me += len(region)
                elif touches_opp and not touches_me:
                    territory_opp += len(region)
    total_me = stones_me + territory_me
    total_opp = stones_opp + territory_opp
    if total_me > total_opp:
        return 1.0
    elif total_opp > total_me:
        return 0.0
    else:
        return 0.5


def select_simulation_move(board, moves):
    non_pass = [m for m in moves if m != (0, 0)]
    if not non_pass:
        return (0, 0)
    # prefer moves adjacent to existing stones
    adjacent = []
    for m in non_pass:
        r, c = m
        idx = r*21 + c
        for nbr in (idx-21, idx-1, idx+1, idx+21):
            if board.board[nbr] in (1, 2):
                adjacent.append(m)
                break
    if adjacent:
        return random.choice(adjacent)
    return random.choice(non_pass)


def simulate(board):
    sim_board = board.copy()
    max_moves = 30
    passes = 0
    for _ in range(max_moves):
        moves = sim_board.legal_moves()
        if not moves:
            break
        move = select_simulation_move(sim_board, moves)
        sim_board.play(move)
        if move == (0, 0):
            passes += 1
            if passes >= 2:
                break
        else:
            passes = 0
    return evaluate(sim_board)


def uct_search(root_board, time_limit=0.9):
    root = Node(None, None, root_board.color)
    root.untried_moves = root_board.legal_moves()
    if not root.untried_moves:
        return (0, 0)
    start_time = time.time()
    while time.time() - start_time < time_limit:
        board = root_board.copy()
        node = root
        # Selection
        while node.untried_moves is None and node.children:
            best_child = None
            best_ucb = -float('inf')
            log_parent_visits = math.log(node.visits) if node.visits > 0 else 0
            for child in node.children.values():
                if child.visits == 0:
                    ucb = float('inf')
                else:
                    exploit = child.value / child.visits
                    explore = 1.4 * math.sqrt(log_parent_visits / child.visits)
                    ucb = exploit + explore
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = child
            node = best_child
            board.play(node.move)
        # Expansion
        if node.untried_moves is not None and node.untried_moves:
            move = random.choice(node.untried_moves)
            node.untried_moves.remove(move)
            if not node.untried_moves:
                node.untried_moves = None
            board.play(move)
            child = Node(move, node, board.color)
            node.children[move] = child
            node = child
        # Simulation
        result = simulate(board)
        # Backpropagation
        while node is not None:
            node.visits += 1
            if node.color == 1:
                node.value += result
            else:
                node.value += 1 - result
            node = node.parent
    if not root.children:
        return (0, 0)
    best_move = max(root.children, key=lambda m: root.children[m].visits)
    return best_move


def policy(me, opponent):
    board = GoBoard(me, opponent)
    moves = board.legal_moves()
    # only pass if no other legal move
    if len(moves) == 1 and moves[0] == (0, 0):
        return (0, 0)
    best_move = uct_search(board, time_limit=0.95)
    return best_move
