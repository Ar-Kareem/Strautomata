
import numpy as np

def count_box_edges(h, v, r, c):
    return int(h[r,c]!=0) + int(h[r+1,c]!=0) + int(v[r,c]!=0) + int(v[r,c+1]!=0)

def legal_moves_list(h, v):
    moves = []
    for r in range(5):
        for c in range(4):
            if h[r,c] == 0:
                moves.append((r,c,'H'))
    for r in range(4):
        for c in range(5):
            if v[r,c] == 0:
                moves.append((r,c,'V'))
    return moves

def apply_move(h, v, cap, move, player):
    h2 = h.copy(); v2 = v.copy(); cap2 = cap.copy()
    r, c, d = move
    completed = 0
    if d == 'H':
        h2[r,c] = player
        if r > 0 and count_box_edges(h2, v2, r-1, c) == 4 and cap2[r-1,c]==0:
            cap2[r-1,c] = player; completed += 1
        if r < 4 and count_box_edges(h2, v2, r, c) == 4 and cap2[r,c]==0:
            cap2[r,c] = player; completed += 1
    else:
        v2[r,c] = player
        if c > 0 and count_box_edges(h2, v2, r, c-1) == 4 and cap2[r,c-1]==0:
            cap2[r,c-1] = player; completed += 1
        if c < 4 and count_box_edges(h2, v2, r, c) == 4 and cap2[r,c]==0:
            cap2[r,c] = player; completed += 1
    return h2, v2, cap2, completed

def classify(h, v, move):
    r, c, d = move
    h2 = h.copy(); v2 = v.copy()
    if d == 'H': h2[r,c] = 1
    else: v2[r,c] = 1
    c3 = False; c4 = False
    bs = []
    if d == 'H':
        if r > 0: bs.append((r-1,c))
        if r < 4: bs.append((r,c))
    else:
        if c > 0: bs.append((r,c-1))
        if c < 4: bs.append((r,c))
    for (br,bc) in bs:
        e = count_box_edges(h2, v2, br, bc)
        if e == 4: c4 = True
        elif e == 3: c3 = True
    if c4: return 'capture'
    if c3: return 'sacrifice'
    return 'safe'

def greedy_capture_sim(h, v, cap, player):
    gain = 0
    while True:
        moves = legal_moves_list(h, v)
        cm = None
        for m in moves:
            if classify(h, v, m) == 'capture':
                cm = m; break
        if not cm: break
        h, v, cap, g = apply_move(h, v, cap, cm, player)
        gain += g
    return h, v, cap, gain

def move_to_str(m):
    return f"{m[0]},{m[1]},{m[2]}"

def estimate_position_for_mover(h, v, cap, mover):
    """Estimate (mover_gain, other_gain) assuming greedy play from this position where 'mover' is to move and has no captures."""
    moves = legal_moves_list(h, v)
    if not moves:
        return 0, 0
    safes = [m for m in moves if classify(h, v, m) == 'safe']
    if safes:
        # Symmetric: can't tell easily; assume roughly even future
        return 0, 0
    sacs = [m for m in moves if classify(h, v, m) == 'sacrifice']
    if not sacs:
        return 0, 0
    best_loss = float('inf')
    for sm in sacs:
        hs, vs, caps, _ = apply_move(h, v, cap, sm, mover)
        _, _, _, og = greedy_capture_sim(hs, vs, caps, -mover)
        if og < best_loss:
            best_loss = og
    return 0, best_loss

def policy(horizontal, vertical, capture):
    h = horizontal.copy().astype(int)
    v = vertical.copy().astype(int)
    cap = capture.copy().astype(int)

    moves = legal_moves_list(h, v)
    if not moves:
        return "0,0,H"

    captures = []
    safes = []
    sacrifices = []
    for m in moves:
        cls = classify(h, v, m)
        if cls == 'capture': captures.append(m)
        elif cls == 'safe': safes.append(m)
        else: sacrifices.append(m)

    if captures:
        # Option A: take captures greedily, then estimate future
        hA, vA, capA, gainA = greedy_capture_sim(h, v, cap, 1)
        # After greedy, my turn still; play best non-capture move
        mvA = legal_moves_list(hA, vA)
        if not mvA:
            diff_A = gainA
        else:
            safeA = [m for m in mvA if classify(hA, vA, m) == 'safe']
            if safeA:
                # I have safe moves; rough estimate: even
                _, opp_future = estimate_position_for_mover(hA, vA, capA, -1)
                diff_A = gainA - opp_future
            else:
                sacA = [m for m in mvA if classify(hA, vA, m) == 'sacrifice']
                if not sacA:
                    diff_A = gainA
                else:
                    best_loss = float('inf')
                    for sm in sacA:
                        hs, vs, caps, _ = apply_move(hA, vA, capA, sm, 1)
                        _, _, _, og = greedy_capture_sim(hs, vs, caps, -1)
                        if og < best_loss:
                            best_loss = og
                    diff_A = gainA - best_loss

        # Option B: double-cross via sacrifice giving exactly 2 to opponent
        best_B = None
        best_B_diff = -float('inf')
        for sm in sacrifices:
            hB, vB, capB, _ = apply_move(h, v, cap, sm, 1)
            hBf, vBf, capBf, opp_gain = greedy_capture_sim(hB, vB, capB, -1)
            if opp_gain != 2:
                continue
            mvB = legal_moves_list(hBf, vBf)
            if not mvB:
                my_gain_B = 0
            else:
                safeB = [m for m in mvB if classify(hBf, vBf, m) == 'safe']
                if safeB:
                    my_gain_B = 0
                else:
                    sacB = [m for m in mvB if classify(hBf, vBf, m) == 'sacrifice']
                    if not sacB:
                        my_gain_B = 0
                    else:
                        best_my = 0
                        for om in sacB:
                            ho, vo, co, _ = apply_move(hBf, vBf, capBf, om, -1)
                            _, _, _, mg = greedy_capture_sim(ho, vo, co, 1)
                            if mg > best_my:
                                best_my = mg
                        my_gain_B = best_my
            diff_B = my_gain_B - opp_gain
            if diff_B > best_B_diff:
                best_B_diff = diff_B
                best_B = sm

        if best_B is not None and best_B_diff > diff_A:
            return move_to_str(best_B)
        return move_to_str(captures[0])

    if safes:
        # Pick safe move preferring those near less-filled boxes
        best = safes[0]
        best_score = -float('inf')
        for m in safes:
            r, c, d = m
            bs = []
            if d == 'H':
                if r > 0: bs.append((r-1,c))
                if r < 4: bs.append((r,c))
            else:
                if c > 0: bs.append((r,c-1))
                if c < 4: bs.append((r,c))
            s = -sum(count_box_edges(h, v, br, bc) for (br,bc) in bs)
            if s > best_score:
                best_score = s
                best = m
        return move_to_str(best)

    # Must sacrifice: choose one minimizing opponent's gain
    best_move = sacrifices[0]
    best_loss = float('inf')
    for m in sacrifices:
        h1, v1, cap1, _ = apply_move(h, v, cap, m, 1)
        _, _, _, oppG = greedy_capture_sim(h1, v1, cap1, -1)
        if oppG < best_loss:
            best_loss = oppG
            best_move = m
    return move_to_str(best_move)
