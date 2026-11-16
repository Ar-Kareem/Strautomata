
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def count_edges(i, j, horizontal, vertical):
        edges = 0
        if horizontal[i, j] != 0:
            edges += 1
        if horizontal[i+1, j] != 0:
            edges += 1
        if vertical[i, j] != 0:
            edges += 1
        if vertical[i, j+1] != 0:
            edges += 1
        return edges

    def get_adjacent_boxes(row, col, dir):
        boxes = []
        if dir == 'H':
            if row < 4:
                boxes.append((row, col))
            if row > 0:
                boxes.append((row-1, col))
        else:
            if col < 4:
                boxes.append((row, col))
            if col > 0:
                boxes.append((row, col-1))
        return boxes

    def is_edge_available(horizontal, vertical, row, col, dir):
        if dir == 'H':
            if col < 0 or col > 3 or row < 0 or row > 4:
                return False
            return horizontal[row, col] == 0
        else:
            if row < 0 or row > 3 or col < 0 or col > 4:
                return False
            return vertical[row, col] == 0

    def simulate_move(horizontal, vertical, capture, move):
        row, col, dir = move
        new_h = horizontal.copy()
        new_v = vertical.copy()
        new_c = capture.copy()
        
        if dir == 'H':
            new_h[row, col] = 1
        else:
            new_v[row, col] = 1
            
        captured_boxes = 0
        boxes = get_adjacent_boxes(row, col, dir)
        for (i, j) in boxes:
            if 0 <= i < 4 and 0 <= j < 4:
                if new_h[i, j] != 0 and new_h[i+1, j] != 0 and new_v[i, j] != 0 and new_v[i, j+1] != 0:
                    if new_c[i, j] == 0:
                        new_c[i, j] = 1
                        captured_boxes += 1
                        
        return new_h, new_v, new_c, captured_boxes

    def get_chain_length(i, j, capture, horizontal, vertical):
        visited = set()
        stack = [(i, j)]
        count = 0
        while stack:
            box = stack.pop()
            if box in visited:
                continue
            visited.add(box)
            count += 1
            neighbors = []
            if box[0] > 0:
                neighbors.append((box[0]-1, box[1]))
            if box[0] < 3:
                neighbors.append((box[0]+1, box[1]))
            if box[1] > 0:
                neighbors.append((box[0], box[1]-1))
            if box[1] < 3:
                neighbors.append((box[0], box[1]+1))
            for (ni, nj) in neighbors:
                if (ni, nj) not in visited and capture[ni, nj] == 0:
                    if count_edges(ni, nj, horizontal, vertical) == 2:
                        stack.append((ni, nj))
        return count

    # Generate legal moves
    moves = []
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                moves.append((row, col, 'H'))
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                moves.append((row, col, 'V'))
                
    capturing_moves = []
    non_capturing_moves = []
    
    for move in moves:
        new_h, new_v, new_c, cap = simulate_move(horizontal, vertical, capture, move)
        if cap > 0:
            capturing_moves.append((move, cap, new_h, new_v, new_c))
        else:
            row, col, dir = move
            boxes_adj = get_adjacent_boxes(row, col, dir)
            boxes_3 = []
            for (i, j) in boxes_adj:
                if 0 <= i < 4 and 0 <= j < 4:
                    if new_c[i, j] == 0 and count_edges(i, j, new_h, new_v) == 3:
                        boxes_3.append((i, j))
            non_capturing_moves.append((move, boxes_3, new_h, new_v, new_c))
            
    if capturing_moves:
        best_move = None
        best_score = -1
        for move, cap, new_h, new_v, new_c in capturing_moves:
            next_capture = 0
            for i in range(4):
                for j in range(4):
                    if new_c[i, j] == 0 and count_edges(i, j, new_h, new_v) == 3:
                        if is_edge_available(new_h, new_v, i, j, 'H') or \
                           is_edge_available(new_h, new_v, i+1, j, 'H') or \
                           is_edge_available(new_h, new_v, i, j, 'V') or \
                           is_edge_available(new_h, new_v, i, j+1, 'V'):
                            next_capture = 1
                            break
                if next_capture:
                    break
            score = cap * 1000 + next_capture * 100
            if score > best_score:
                best_score = score
                best_move = move
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
        
    else:
        safe_moves = [m for m in non_capturing_moves if len(m[1]) == 0]
        bad_moves = [m for m in non_capturing_moves if len(m[1]) > 0]
        
        if safe_moves:
            best_move = None
            best_score = -1
            for move, boxes_3, new_h, new_v, new_c in safe_moves:
                row, col, dir = move
                adj_boxes = get_adjacent_boxes(row, col, dir)
                adjacent_2_edges = 0
                for (i, j) in adj_boxes:
                    if 0 <= i < 4 and 0 <= j < 4 and new_c[i, j] == 0:
                        if count_edges(i, j, new_h, new_v) == 2:
                            adjacent_2_edges += 1
                score = -adjacent_2_edges
                if score > best_score:
                    best_score = score
                    best_move = move
            return f"{best_move[0]},{best_move[1]},{best_move[2]}"
            
        else:
            best_move = None
            best_score = -1
            for move, boxes_3, new_h, new_v, new_c in bad_moves:
                max_chain = 0
                for (i, j) in boxes_3:
                    neighbors = []
                    if i > 0:
                        neighbors.append((i-1, j))
                    if i < 3:
                        neighbors.append((i+1, j))
                    if j > 0:
                        neighbors.append((i, j-1))
                    if j < 3:
                        neighbors.append((i, j+1))
                    for (ni, nj) in neighbors:
                        if 0 <= ni < 4 and 0 <= nj < 4 and new_c[ni, nj] == 0:
                            if count_edges(ni, nj, new_h, new_v) == 2:
                                chain_len = get_chain_length(ni, nj, new_c, new_h, new_v)
                                max_chain = max(max_chain, chain_len)
                score = -len(boxes_3) * 1000 + max_chain * 10
                if score > best_score:
                    best_score = score
                    best_move = move
            return f"{best_move[0]},{best_move[1]},{best_move[2]}"
