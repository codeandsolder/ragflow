import json
import os
from typing import Dict, List, Optional

BASELINE_FILE = os.getenv("BENCHMARK_BASELINE_FILE")


def _fmt_seconds(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}s"


def _fmt_ms(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value * 1000.0:.2f}ms"


def _fmt_qps(qps: Optional[float]) -> str:
    if qps is None or qps <= 0:
        return "n/a"
    return f"{qps:.2f}"


def _calc_qps(total_duration_s: Optional[float], total_requests: int) -> Optional[float]:
    if total_duration_s is None or total_duration_s <= 0:
        return None
    return total_requests / total_duration_s


def load_baseline() -> Optional[dict]:
    if not BASELINE_FILE or not os.path.exists(BASELINE_FILE):
        return None
    try:
        with open(BASELINE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_baseline(data: dict) -> None:
    if not BASELINE_FILE:
        return
    try:
        with open(BASELINE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _pct_change(current: Optional[float], baseline: Optional[float]) -> Optional[str]:
    if current is None or baseline is None or baseline == 0:
        return None
    change = ((current - baseline) / baseline) * 100
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"


def _regression_marker(pct: Optional[str], lower_is_better: bool = True) -> str:
    if pct is None:
        return ""
    try:
        val = float(pct.replace("%", "").replace("+", ""))
        if lower_is_better:
            return " [REGRESSION]" if val > 5 else (" [IMPROVED]" if val < -5 else "")
        else:
            return " [IMPROVED]" if val > 5 else (" [REGRESSION]" if val < -5 else "")
    except Exception:
        return ""


def render_report(lines: List[str]) -> str:
    return "\n".join(lines).strip() + "\n"


def chat_report(
    *,
    interface: str,
    concurrency: int,
    total_duration_s: Optional[float],
    iterations: int,
    success: int,
    failure: int,
    model: str,
    total_stats: Dict[str, Optional[float]],
    first_token_stats: Dict[str, Optional[float]],
    errors: List[str],
    created: Dict[str, str],
) -> str:
    baseline = load_baseline()
    baseline_key = f"{interface}_{concurrency}_{model}"
    base = (baseline or {}).get(baseline_key, {}) if baseline else {}

    lines = [
        f"Interface: {interface}",
        f"Concurrency: {concurrency}",
        f"Iterations: {iterations}",
        f"Success: {success}",
        f"Failure: {failure}",
        f"Model: {model}",
    ]
    for key, value in created.items():
        lines.append(f"{key}: {value}")

    qps = _calc_qps(total_duration_s, iterations)
    qps_pct = _pct_change(qps, base.get("qps"))
    lines.append(
        f"QPS (requests / total duration): {_fmt_qps(qps)}{qps_pct or ''}{_regression_marker(qps_pct, lower_is_better=False)}"
    )

    total_avg_pct = _pct_change(total_stats["avg"], base.get("total_latency_avg"))
    total_p50_pct = _pct_change(total_stats["p50"], base.get("total_latency_p50"))
    lines.append(
        "Latency (total): "
        f"avg={_fmt_ms(total_stats['avg'])}{total_avg_pct or ''}, min={_fmt_ms(total_stats['min'])}, "
        f"p50={_fmt_ms(total_stats['p50'])}{total_p50_pct or ''}, p90={_fmt_ms(total_stats['p90'])}, p95={_fmt_ms(total_stats['p95'])}"
    )

    ft_avg_pct = _pct_change(first_token_stats["avg"], base.get("first_token_latency_avg"))
    ft_p50_pct = _pct_change(first_token_stats["p50"], base.get("first_token_latency_p50"))
    lines.append(
        "Latency (first token): "
        f"avg={_fmt_ms(first_token_stats['avg'])}{ft_avg_pct or ''}, min={_fmt_ms(first_token_stats['min'])}, "
        f"p50={_fmt_ms(first_token_stats['p50'])}{ft_p50_pct or ''}, p90={_fmt_ms(first_token_stats['p90'])}, p95={_fmt_ms(first_token_stats['p95'])}"
    )

    lines.append(f"Total Duration: {_fmt_seconds(total_duration_s)}")

    if errors:
        lines.append("Errors: " + "; ".join(errors[:5]))

    save_baseline({
        **(baseline or {}),
        baseline_key: {
            "qps": qps,
            "total_latency_avg": total_stats["avg"],
            "total_latency_p50": total_stats["p50"],
            "first_token_latency_avg": first_token_stats["avg"],
            "first_token_latency_p50": first_token_stats["p50"],
        }
    })

    return render_report(lines)


def retrieval_report(
    *,
    interface: str,
    concurrency: int,
    total_duration_s: Optional[float],
    iterations: int,
    success: int,
    failure: int,
    stats: Dict[str, Optional[float]],
    errors: List[str],
    created: Dict[str, str],
) -> str:
    baseline = load_baseline()
    baseline_key = f"{interface}_{concurrency}"
    base = (baseline or {}).get(baseline_key, {}) if baseline else {}

    lines = [
        f"Interface: {interface}",
        f"Concurrency: {concurrency}",
        f"Iterations: {iterations}",
        f"Success: {success}",
        f"Failure: {failure}",
    ]
    for key, value in created.items():
        lines.append(f"{key}: {value}")

    qps = _calc_qps(total_duration_s, iterations)
    qps_pct = _pct_change(qps, base.get("qps"))
    lines.append(
        f"QPS (requests / total duration): {_fmt_qps(qps)}{qps_pct or ''}{_regression_marker(qps_pct, lower_is_better=False)}"
    )

    avg_pct = _pct_change(stats["avg"], base.get("latency_avg"))
    p50_pct = _pct_change(stats["p50"], base.get("latency_p50"))
    lines.append(
        f"Latency: avg={_fmt_ms(stats['avg'])}{avg_pct or ''}, min={_fmt_ms(stats['min'])}, p50={_fmt_ms(stats['p50'])}{p50_pct or ''}, p90={_fmt_ms(stats['p90'])}, p95={_fmt_ms(stats['p95'])}"
    )

    lines.append(f"Total Duration: {_fmt_seconds(total_duration_s)}")

    if errors:
        lines.append("Errors: " + "; ".join(errors[:5]))

    save_baseline({
        **(baseline or {}),
        baseline_key: {
            "qps": qps,
            "latency_avg": stats["avg"],
            "latency_p50": stats["p50"],
        }
    })

    return render_report(lines)
