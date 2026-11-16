
import random

def policy(my_men, my_kings, opp_men, opp_kings, color):
    my_men = [tuple(x) for x in my_men]
    my_kings = [tuple(x) for x in my_kings]
    opp_men = [tuple(x) for x in opp_men]
    opp_kings = [tuple(x) for x in opp_kings]
    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)
    all_set = my_set | opp_set

    def in_bounds(r,c):
        return 0 <= r < 8 and 0 <= c < 8

    # directions
    if color == 'w':
        fdirs = [(1,1),(1,-1)]
        home_row = 7
    else:
        fdirs = [(-1,1),(-1,-1)]
        home_row = 0
    kdirs = [(1,1),(1,-1),(-1,1),(-1,-1)]

    moves = []
    captures = []

    # helper for scoring
    def score_move(fr, fc, tr, tc, capture):
        score = 0
        if capture:
            mr, mc = (fr+tr)//2, (fc+tc)//2
            if (mr,mc) in opp_kings:
                score += 5
            else:
                score += 3
        # promotion bonus
        if (fr,fc) in my_men and tr == home_row:
            score += 2
        # advance bonus
        if (fr,fc) in my_men:
            if color == 'w' and tr > fr: score += 1
            if color == 'b' and tr < fr: score += 1
        return score

    # generate captures
    for (r,c) in my_men:
        for dr,dc in fdirs:
            mr, mc = r+dr, c+dc
            tr, tc = r+2*dr, c+2*dc
            if in_bounds(tr,tc) and (mr,mc) in opp_set and (tr,tc) not in all_set:
                sc = score_move(r,c,tr,tc,True)
                captures.append(((r,c),(tr,tc),sc))
    for (r,c) in my_kings:
        for dr,dc in kdirs:
            mr, mc = r+dr, c+dc
            tr, tc = r+2*dr, c+2*dc
            if in_bounds(tr,tc) and (mr,mc) in opp_set and (tr,tc) not in all_set:
                sc = score_move(r,c,tr,tc,True)
                captures.append(((r,c),(tr,tc),sc))

    if captures:
        # choose best capture
        captures.sort(key=lambda x:(-x[2], x[0], x[1]))
        return (captures[0][0], captures[0][1])

    # generate normal moves
    for (r,c) in my_men:
        for dr,dc in fdirs:
            tr, tc = r+dr, c+dc
            if in_bounds(tr,tc) and (tr,tc) not in all_set:
                sc = score_move(r,c,tr,tc,False)
                moves.append(((r,c),(tr,tc),sc))
    for (r,c) in my_kings:
        for dr,dc in kdirs:
            tr, tc = r+dr, c+dc
            if in_bounds(tr,tc) and (tr,tc) not in all_set:
                sc = score_move(r,c,tr,tc,False)
                moves.append(((r,c),(tr,tc),sc))

    if moves:
        moves.sort(key=lambda x:(-x[2], x[0], x[1]))
        return (moves[0][0], moves[0][1])

    # fallback (should not occur)
    return ((0,0),(0,0))
