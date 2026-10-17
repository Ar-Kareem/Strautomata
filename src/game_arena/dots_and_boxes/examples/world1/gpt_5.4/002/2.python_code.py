
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, arrays are 5x5

    def is_legal(move):
        r, c, d = move
        if d == 'H':
            return 0 <= r <= N and 0 <= c < N and horizontal[r, c] == 0
        else:
            return 0 <= r < N and 0 <= c <= N and vertical[r, c] == 0

    def all_legal_moves():
        moves = []
        for r in range(N + 1):
            for c in range(N):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(N):
            for c in range(N + 1):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def box_sides_count(br, bc):
        cnt = 0
        if horizontal[br, bc] != 0:
            cnt += 1
        if horizontal[br + 1, bc] != 0:
            cnt += 1
        if vertical[br, bc] != 0:
            cnt += 1
        if vertical[br, bc + 1] != 0:
            cnt += 1
        return cnt

    def boxes_adjacent_to_move(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0:
                boxes.append((r - 1, c))
            if r < N:
                boxes.append((r, c))
        else:
            if c > 0:
                boxes.append((r, c - 1))
            if c < N:
                boxes.append((r, c))
        return boxes

    def completes_boxes(move):
        total = 0
        for br, bc in boxes_adjacent_to_move(move):
            if capture[br, bc] == 0 and box_sides_count(br, bc) == 3:
                total += 1
        return total

    def creates_three_sided_box(move):
        # After making this move, does any adjacent uncaptured box become 3-sided?
        for br, bc in boxes_adjacent_to_move(move):
            if capture[br, bc] == 0 and box_sides_count(br, bc) == 2:
                return True
        return False

    def move_risk_score(move):
        # Lower is better.
        # Strongly penalize creating 3-sided boxes.
        # Mildly prefer edges adjacent to boxes with fewer existing sides.
        score = 0
        r, c, d = move

        adj = boxes_adjacent_to_move(move)
        for br, bc in adj:
            if capture[br, bc] != 0:
                continue
            sides = box_sides_count(br, bc)
            if sides == 2:
                score += 100  # this move would create a 3-sided box
            elif sides == 1:
                score += 3
            elif sides == 0:
                score += 1

        # Tiny structural preference: boundary edges can be slightly safer early,
        # but interior edges may preserve flexibility. Keep this very mild.
        if d == 'H':
            if r == 0 or r == N:
                score += 0.2
        else:
            if c == 0 or c == N:
                score += 0.2

        # Prefer moves touching fewer boxes when all else equal.
        score += 0.1 * len(adj)
        return score

    def simulate_chain_gain(start_move):
        """
        Estimate how many boxes the opponent can immediately harvest if we play
        this unsafe non-capturing move and they greedily keep taking forced boxes.
        We model only the forced capture cascade on the resulting board.
        Lower is better for us.
        """
        h = horizontal.copy()
        v = vertical.copy()
        cap = capture.copy()

        r, c, d = start_move
        if d == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1

        def sides_count_local(br, bc):
            cnt = 0
            if h[br, bc] != 0:
                cnt += 1
            if h[br + 1, bc] != 0:
                cnt += 1
            if v[br, bc] != 0:
                cnt += 1
            if v[br, bc + 1] != 0:
                cnt += 1
            return cnt

        def legal_moves_local():
            moves = []
            for rr in range(N + 1):
                for cc in range(N):
                    if h[rr, cc] == 0:
                        moves.append((rr, cc, 'H'))
            for rr in range(N):
                for cc in range(N + 1):
                    if v[rr, cc] == 0:
                        moves.append((rr, cc, 'V'))
            return moves

        def boxes_adj_local(move):
            rr, cc, dd = move
            boxes = []
            if dd == 'H':
                if rr > 0:
                    boxes.append((rr - 1, cc))
                if rr < N:
                    boxes.append((rr, cc))
            else:
                if cc > 0:
                    boxes.append((rr, cc - 1))
                if cc < N:
                    boxes.append((rr, cc))
            return boxes

        gain = 0
        while True:
            scoring = []
            for mv in legal_moves_local():
                made = 0
                for br, bc in boxes_adj_local(mv):
                    if cap[br, bc] == 0 and sides_count_local(br, bc) == 3:
                        made += 1
                if made > 0:
                    scoring.append((made, mv))
            if not scoring:
                break

            # Opponent greedily takes the biggest immediate score
            scoring.sort(reverse=True, key=lambda x: x[0])
            made, mv = scoring[0]
            rr, cc, dd = mv
            if dd == 'H':
                h[rr, cc] = -1
            else:
                v[rr, cc] = -1

            for br, bc in boxes_adj_local(mv):
                if cap[br, bc] == 0 and sides_count_local(br, bc) == 4:
                    cap[br, bc] = -1
                    gain += 1

        return gain

    legal = all_legal_moves()
    if not legal:
        # Should not happen in a valid game state, but return a syntactically valid move.
        return "0,0,H"

    # 1. Take points immediately if available.
    scoring_moves = []
    for mv in legal:
        made = completes_boxes(mv)
        if made > 0:
            scoring_moves.append((made, mv))

    if scoring_moves:
        # Prefer moves that capture more boxes; break ties by not creating fresh 3-sided boxes if possible.
        scoring_moves.sort(key=lambda x: (-x[0], creates_three_sided_box(x[1]), move_risk_score(x[1])))
        r, c, d = scoring_moves[0][1]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves that do not create a 3-sided box.
    safe_moves = [mv for mv in legal if not creates_three_sided_box(mv)]
    if safe_moves:
        safe_moves.sort(key=move_risk_score)
        r, c, d = safe_moves[0]
        return f"{r},{c},{d}"

    # 3. If all moves are unsafe, choose the move that gives away the smallest forced chain.
    best_move = None
    best_key = None
    for mv in legal:
        chain_loss = simulate_chain_gain(mv)
        key = (chain_loss, move_risk_score(mv))
        if best_key is None or key < best_key:
            best_key = key
            best_move = mv

    if best_move is None:
        best_move = legal[0]

    r, c, d = best_move
    return f"{r},{c},{d}"
