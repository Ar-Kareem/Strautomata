
import numpy as np
import time
import random as _random

# ---------- precompute board topology ----------
box_edges = []
edge_boxes = [[] for _ in range(40)]

for r in range(4):
    for c in range(4):
        top = r * 4 + c
        bottom = (r + 1) * 4 + c
        left = 20 + r * 5 + c
        right = 20 + r * 5 + (c + 1)
        box_edges.append([top, bottom, left, right])
        edge_boxes[top].append(r * 4 + c)
        edge_boxes[bottom].append(r * 4 + c)
        edge_boxes[left].append(r * 4 + c)
        edge_boxes[right].append(r * 4 + c)

# ---------- Zobrist hashing ----------
_random.seed(42)
EDGE_HASH = [_random.getrandbits(64) for _ in range(40)]
BOX_HASH = [[_random.getrandbits(64), _random.getrandbits(64)] for _ in range(16)]  # 0: player 1, 1: player -1


class TimeoutError(Exception):
    pass


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    edges = [False] * 40
    boxes = [0] * 16
    hash_val = 0

    # read horizontal edges (rows 0..4, cols 0..3)
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                idx = r * 4 + c
                edges[idx] = True
                hash_val ^= EDGE_HASH[idx]

    # read vertical edges (rows 0..3, cols 0..4)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                idx = 20 + r * 5 + c
                edges[idx] = True
                hash_val ^= EDGE_HASH[idx]

    # read captured boxes (rows 0..3, cols 0..3)
    for r in range(4):
        for c in range(4):
            box_idx = r * 4 + c
            val = int(capture[r, c])
            boxes[box_idx] = val
            if val == 1:
                hash_val ^= BOX_HASH[box_idx][0]
            elif val == -1:
                hash_val ^= BOX_HASH[box_idx][1]

    # We are always player 1
    player = 1

    legal_moves = [i for i in range(40) if not edges[i]]
    if not legal_moves:
        return "0,0,H"  # fallback (should not be reached)

    # ---------- move ordering heuristic ----------
    def move_priority(move, edges, boxes, player):
        capture_count = 0
        unsafe = False
        for box in edge_boxes[move]:
            if boxes[box] == 0:
                drawn = 0
                for e in box_edges[box]:
                    if e == move or edges[e]:
                        drawn += 1
                if drawn == 4:
                    capture_count += 1
                elif drawn == 3:
                    unsafe = True
        if capture_count > 0:
            return (2, capture_count)
        elif not unsafe:
            return (1, 0)
        else:
            return (0, 0)

    legal_moves.sort(key=lambda m: move_priority(m, edges, boxes, 1), reverse=True)
    best_move = legal_moves[0]

    start_time = time.time()
    time_limit = 0.9
    tt = {}

    # ---------- evaluation ----------
    def evaluate(boxes, player_to_move):
        my_boxes = sum(1 for b in boxes if b == 1)
        opp_boxes = sum(1 for b in boxes if b == -1)
        return my_boxes - opp_boxes

    def is_terminal(edges):
        return all(edges)

    # ---------- alpha-beta with TT ----------
    def alphabeta(edges, boxes, player, depth, alpha, beta, hash_val):
        nonlocal start_time, time_limit, tt
        if time.time() - start_time > time_limit:
            raise TimeoutError()

        if is_terminal(edges) or depth == 0:
            return evaluate(boxes, player)

        key = (hash_val, depth, player)
        if key in tt:
            val, flag = tt[key]
            if flag == 'exact':
                return val
            elif flag == 'lower':
                if val >= beta:
                    return val
                alpha = max(alpha, val)
            elif flag == 'upper':
                if val <= alpha:
                    return val
                beta = min(beta, val)
            if alpha >= beta:
                return val

        legal = [i for i in range(40) if not edges[i]]
        legal.sort(key=lambda m: move_priority(m, edges, boxes, player), reverse=True)

        if player == 1:
            original_alpha = alpha
            value = -float('inf')
            for move in legal:
                edges[move] = True
                new_hash = hash_val ^ EDGE_HASH[move]
                captured = []
                for box in edge_boxes[move]:
                    if boxes[box] == 0:
                        other_edges = [e for e in box_edges[box] if e != move]
                        if all(edges[e] for e in other_edges):
                            boxes[box] = 1
                            new_hash ^= BOX_HASH[box][0]
                            captured.append(box)
                extra = len(captured) > 0
                if extra:
                    val = alphabeta(edges, boxes, 1, depth - 1, alpha, beta, new_hash)
                else:
                    val = alphabeta(edges, boxes, -1, depth - 1, alpha, beta, new_hash)
                edges[move] = False
                for box in captured:
                    boxes[box] = 0
                value = max(value, val)
                if value >= beta:
                    break
                alpha = max(alpha, value)
            if value <= original_alpha:
                flag = 'upper'
            elif value >= beta:
                flag = 'lower'
            else:
                flag = 'exact'
            tt[key] = (value, flag)
            return value
        else:
            original_beta = beta
            value = float('inf')
            for move in legal:
                edges[move] = True
                new_hash = hash_val ^ EDGE_HASH[move]
                captured = []
                for box in edge_boxes[move]:
                    if boxes[box] == 0:
                        other_edges = [e for e in box_edges[box] if e != move]
                        if all(edges[e] for e in other_edges):
                            boxes[box] = -1
                            new_hash ^= BOX_HASH[box][1]
                            captured.append(box)
                extra = len(captured) > 0
                if extra:
                    val = alphabeta(edges, boxes, -1, depth - 1, alpha, beta, new_hash)
                else:
                    val = alphabeta(edges, boxes, 1, depth - 1, alpha, beta, new_hash)
                edges[move] = False
                for box in captured:
                    boxes[box] = 0
                value = min(value, val)
                if value <= alpha:
                    break
                beta = min(beta, value)
            if value <= alpha:
                flag = 'upper'
            elif value >= original_beta:
                flag = 'lower'
            else:
                flag = 'exact'
            tt[key] = (value, flag)
            return value

    # ---------- iterative deepening ----------
    for depth in range(1, 41):
        try:
            best_score = -float('inf')
            current_best_move = legal_moves[0]
            alpha = -float('inf')
            beta = float('inf')
            for move in legal_moves:
                edges[move] = True
                new_hash = hash_val ^ EDGE_HASH[move]
                captured = []
                for box in edge_boxes[move]:
                    if boxes[box] == 0:
                        other_edges = [e for e in box_edges[box] if e != move]
                        if all(edges[e] for e in other_edges):
                            boxes[box] = 1
                            new_hash ^= BOX_HASH[box][0]
                            captured.append(box)
                extra = len(captured) > 0
                if extra:
                    val = alphabeta(edges, boxes, 1, depth - 1, alpha, beta, new_hash)
                else:
                    val = alphabeta(edges, boxes, -1, depth - 1, alpha, beta, new_hash)
                edges[move] = False
                for box in captured:
                    boxes[box] = 0
                if val > best_score:
                    best_score = val
                    current_best_move = move
                alpha = max(alpha, val)
            best_move = current_best_move
        except TimeoutError:
            break

    # convert internal move index to required string format
    if best_move < 20:
        r = best_move // 4
        c = best_move % 4
        return f"{r},{c},H"
    else:
        idx = best_move - 20
        r = idx // 5
        c = idx % 5
        return f"{r},{c},V"
