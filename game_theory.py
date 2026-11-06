"""Pure game theory logic for a 2x2 normal-form game. No web code here."""
from typing import Any, Dict, List, Optional

EPS = 1e-9  # tolerance for float comparisons


def _eq(x: float, y: float) -> bool:
    return abs(x - y) <= EPS


def best_responses_a(payoffs) -> Dict[int, List[int]]:
    """For each B strategy j, the list of A strategies maximizing A's payoff."""
    result = {}
    for j in range(2):
        vals = [payoffs[i][j][0] for i in range(2)]
        m = max(vals)
        result[j] = [i for i in range(2) if _eq(vals[i], m)]
    return result


def best_responses_b(payoffs) -> Dict[int, List[int]]:
    """For each A strategy i, the list of B strategies maximizing B's payoff."""
    result = {}
    for i in range(2):
        vals = [payoffs[i][j][1] for j in range(2)]
        m = max(vals)
        result[i] = [j for j in range(2) if _eq(vals[j], m)]
    return result


def _dominance(payoffs, player: int) -> Optional[Dict[str, Any]]:
    """Return {'index', 'type'} for the strongest dominant strategy, else None.

    player 0 = Seller A (rows), player 1 = Seller B (columns).
    """

    def pay(own: int, opp: int) -> float:
        i, j = (own, opp) if player == 0 else (opp, own)
        return payoffs[i][j][player]

    for s in range(2):
        other = 1 - s
        diffs = [pay(s, opp) - pay(other, opp) for opp in range(2)]
        if all(d > EPS for d in diffs):
            return {"index": s, "type": "strict"}
        if all(d >= -EPS for d in diffs) and any(d > EPS for d in diffs):
            return {"index": s, "type": "weak"}
    return None


def pure_nash(payoffs) -> List[tuple]:
    br_a = best_responses_a(payoffs)
    br_b = best_responses_b(payoffs)
    return [
        (i, j)
        for i in range(2)
        for j in range(2)
        if i in br_a[j] and j in br_b[i]
    ]


def mixed_nash_2x2(payoffs) -> Optional[Dict[str, float]]:
    """Fully mixed equilibrium of a 2x2 game (only meaningful if no pure NE).

    p = P(A plays strategy 0) making B indifferent.
    q = P(B plays strategy 0) making A indifferent.
    """
    a = [[payoffs[i][j][0] for j in range(2)] for i in range(2)]
    b = [[payoffs[i][j][1] for j in range(2)] for i in range(2)]
    den_p = b[0][0] - b[1][0] - b[0][1] + b[1][1]
    den_q = a[0][0] - a[0][1] - a[1][0] + a[1][1]
    if _eq(den_p, 0) or _eq(den_q, 0):
        return None
    p = (b[1][1] - b[1][0]) / den_p
    q = (a[1][1] - a[0][1]) / den_q
    if not (0 <= p <= 1 and 0 <= q <= 1):
        return None
    return {"p_a_strategy_1": p, "q_b_strategy_1": q}


def analyze(
    seller_a: str,
    seller_b: str,
    strategies_a: List[str],
    strategies_b: List[str],
    payoffs: List[List[List[float]]],
) -> Dict[str, Any]:
    br_a = best_responses_a(payoffs)
    br_b = best_responses_b(payoffs)
    nash = pure_nash(payoffs)

    def outcome(i: int, j: int) -> Dict[str, Any]:
        pa, pb = payoffs[i][j]
        return {
            "strategy_a": strategies_a[i],
            "strategy_b": strategies_b[j],
            "payoff_a": pa,
            "payoff_b": pb,
            "combined": pa + pb,
        }

    combined = [outcome(i, j) for i in range(2) for j in range(2)]
    highest = max(c["combined"] for c in combined)
    highest_outcomes = [c for c in combined if _eq(c["combined"], highest)]

    def dominant(player: int, names: List[str]):
        d = _dominance(payoffs, player)
        return None if d is None else {"strategy": names[d["index"]], "type": d["type"]}

    nash_out = [outcome(i, j) for i, j in nash]
    nash_set = set(nash)
    for c, (i, j) in zip(combined, [(i, j) for i in range(2) for j in range(2)]):
        c["is_nash"] = (i, j) in nash_set
        c["is_highest_combined"] = _eq(c["combined"], highest)

    # Plain-language incentives
    explanations = []
    for i, j in [(i, j) for i in range(2) for j in range(2)]:
        o = combined[i * 2 + j]
        a_ok = i in br_a[j]
        b_ok = j in br_b[i]
        explanations.append(
            f"({strategies_a[i]}, {strategies_b[j]}): {seller_a} "
            f"{'has no incentive to deviate' if a_ok else 'would do better switching to ' + strategies_a[1 - i]}; "
            f"{seller_b} "
            f"{'has no incentive to deviate' if b_ok else 'would do better switching to ' + strategies_b[1 - j]}."
        )

    mixed = None
    note = None
    if not nash:
        mixed = mixed_nash_2x2(payoffs)
        note = (
            "No pure-strategy Nash equilibrium exists. By Nash's theorem, "
            "a mixed-strategy equilibrium still exists."
        )

    return {
        "seller_a": seller_a,
        "seller_b": seller_b,
        "strategies_a": strategies_a,
        "strategies_b": strategies_b,
        "payoffs": payoffs,
        "best_responses_a": {strategies_b[j]: [strategies_a[i] for i in v] for j, v in br_a.items()},
        "best_responses_b": {strategies_a[i]: [strategies_b[j] for j in v] for i, v in br_b.items()},
        "dominant_strategy_a": dominant(0, strategies_a),
        "dominant_strategy_b": dominant(1, strategies_b),
        "nash_equilibria": nash_out,
        "combined_profits": combined,
        "highest_combined_profit": highest,
        "highest_combined_outcomes": highest_outcomes,
        "outcomes_analyzed": 4,
        "incentive_explanations": explanations,
        "mixed_equilibrium": mixed,
        "note": note,
    }