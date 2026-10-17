"""Cost conversion: only additive means can be multiplied by task counts."""
import math


ADDITIVE_UNITS = {'per_task', 'per_problem', 'per_rollout', 'per_test', 'per_prompt', 'per_bot', 'per_debate', 'per_session', 'per_question', 'per_run'}


def cost_values(cost, unit, n_tasks, explicit_total=math.nan):
    has_n = math.isfinite(n_tasks) and n_tasks > 0
    if unit == 'total_run':
        return cost, cost / n_tasks if has_n else math.nan
    if math.isfinite(explicit_total):
        return explicit_total, cost
    total = cost * n_tasks if has_n and unit in ADDITIVE_UNITS else math.nan
    return total, cost
