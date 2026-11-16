
def policy(state: list[list[object]], role: str) -> str:
    # Helper: does a given proposition exist exactly?
    def has(prop):
        return any(s == prop for s in state)

    # Extract steps (if present) and control
    control_left = has(["control", "left"])
    control_right = has(["control", "right"])
    # If control doesn't exist (shouldn't happen), fall back to using the provided role.
    current = None
    if control_left and not control_right:
        current = "left"
    elif control_right and not control_left:
        current = "right"
    else:
        current = role

    # If it's not our role, still must output a legal move for `role`.
    # In that case, best-effort: choose a move template that doesn't depend on control.
    # However in this game, control facts typically match the current role input.
    r = role

    # Safe default: if we can see that this role already "played", then tick is commonly legal.
    if has(["played", r]):
        return "tick"

    # Otherwise, choose among a/b/c for the current role.
    # Use the presence of p(other) / step parity to create a consistent, hard-to-beat pattern.
    # Observed examples:
    # - left at step 1: a(left)
    # - right at step 2: b(right)
    # - right at step 6: c(right)
    # - left at step 7: a(left)
    # We'll approximate by using step number mod 3.
    step_num = None
    for s in state:
        if len(s) == 2 and s[0] == "step":
            try:
                step_num = int(s[1])
            except Exception:
                pass
            break

    if step_num is None:
        # If unknown, pick a canonical move based on role.
        return "a({})".format(r) if r == "left" else "b({})".format(r)

    m = step_num % 3
    if m == 1:
        return "a({})".format(r)
    elif m == 2:
        return "b({})".format(r)
    else:
        return "c({})".format(r)
