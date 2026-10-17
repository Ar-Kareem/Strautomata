#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import io
import keyword
import math
import re
import tokenize
from pathlib import Path
from typing import Any

from strategy_analysis_utils import (
    CODE_TAG_RE,
    HEURISTIC_TAGS,
    ML_TAGS,
    OPTIMIZATION_TAGS,
    SEARCH_TAGS,
    STOCHASTIC_TAGS,
    THINKING_RE,
    THOUGHT_TEXT_RULES,
    TREE_SEARCH_TAGS,
    CodeAnalysis,
    CodeFeatures,
    RunRecord,
    alignment_metrics,
    analyze_code,
    detect_text_tags,
    extract_code_from_output,
    extract_thinking,
    load_output_text,
    recursive_function_count,
    round_metric,
    safe_div,
    safe_read_text,
    weighted_tag_score,
    word_count,
)


IDENTIFIER_SIGNAL_TOKENS = {
    "move",
    "board",
    "state",
    "score",
    "value",
    "depth",
    "alpha",
    "beta",
    "search",
    "cache",
    "policy",
    "legal",
    "eval",
    "time",
    "heuristic",
    "best",
}
PY_KEYWORDS = set(keyword.kwlist)
PY_BUILTINS = {name.lower() for name in dir(__builtins__)}
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CONSTRAINT_KEYWORDS = {
    "legal",
    "valid",
    "format",
    "constraint",
    "disqualified",
    "must",
    "always",
    "timeout",
    "seconds",
    "required",
}
SEARCH_LEXICON = {
    "minimax",
    "alpha",
    "beta",
    "search",
    "depth",
    "ply",
    "mcts",
    "rollout",
    "uct",
    "ucb",
    "prune",
}
EVAL_LEXICON = {
    "evaluate",
    "evaluation",
    "heuristic",
    "score",
    "material",
    "mobility",
    "center",
    "central",
    "position",
    "territory",
}
ROBUSTNESS_LEXICON = {
    "legal",
    "valid",
    "fallback",
    "robust",
    "guard",
    "bound",
    "bounds",
    "safe",
    "default",
    "clamp",
}
STOCHASTIC_LEXICON = {
    "random",
    "stochastic",
    "sample",
    "probability",
    "distribution",
    "noise",
    "epsilon",
    "explore",
}
ACTION_LEXICON = {
    "generate",
    "evaluate",
    "score",
    "search",
    "sort",
    "prune",
    "select",
    "return",
    "fallback",
    "block",
    "control",
}
MODAL_WORDS = {"must", "should", "need", "always", "never", "cannot", "can't", "required"}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "their",
    "then",
    "than",
    "have",
    "has",
    "had",
    "will",
    "would",
    "could",
    "should",
    "must",
    "can",
    "all",
    "any",
    "are",
    "was",
    "were",
    "our",
    "you",
    "not",
    "out",
    "use",
    "using",
    "used",
    "also",
    "when",
    "where",
    "which",
    "what",
    "how",
    "while",
    "before",
    "after",
    "each",
    "over",
    "under",
    "very",
    "able",
}
STRATEGY_CONCEPT_PATTERNS: dict[str, list[str]] = {
    "lookahead": [r"\bminimax\b", r"\bsearch\b", r"\bdepth\b", r"\bply\b", r"\bmcts\b", r"\brollout\b"],
    "mobility": [r"\bmobility\b", r"\blegal moves?\b", r"\bgenerate moves?\b", r"\bnum_moves\b"],
    "center_control": [r"\bcenter\b", r"\bcentral\b"],
    "territory": [r"\bterritory\b", r"\bspace\b", r"\bregion\b"],
    "blocking": [r"\bblock\b", r"\btrap\b", r"\brestrict\b", r"\bcut off\b"],
    "transposition": [r"\btransposition\b", r"\bcache\b", r"\bmemo\b", r"\bzobrist\b"],
    "time_management": [r"\btime\b", r"\btimeout\b", r"\bdeadline\b", r"\bseconds?\b", r"\biterative\b"],
    "randomization": [r"\brandom\b", r"\bstochastic\b", r"\bsample\b", r"\bepsilon\b"],
    "legality": [r"\blegal\b", r"\bvalid\b", r"\bfallback\b", r"\brobust\b"],
    "connectivity": [r"\bconnect", r"\bcomponent", r"\bbfs\b", r"\bdfs\b", r"\bunion\b"],
}
ALL_STRATEGY_TERMS = (
    SEARCH_LEXICON
    | EVAL_LEXICON
    | ROBUSTNESS_LEXICON
    | STOCHASTIC_LEXICON
    | ACTION_LEXICON
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze strategy styles across logged model runs.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-path", type=Path, required=True)
    return parser.parse_args()


def combine_identifier_counts(features: CodeFeatures) -> dict[str, int]:
    counts: dict[str, int] = {}
    for bucket in (features.name_ref_counts, features.attr_ref_counts, features.func_name_counts):
        for key, value in bucket.items():
            counts[key] = counts.get(key, 0) + value
    return counts


def tokenize_words(text: str | None) -> list[str]:
    if not text:
        return []
    return [token.lower() for token in WORD_RE.findall(text)]


def content_vocab(text: str | None) -> set[str]:
    return {
        token
        for token in tokenize_words(text)
        if len(token) >= 3 and token not in STOPWORDS and not token.isdigit()
    }


def gini_coefficient(values: list[int]) -> float:
    if not values:
        return 0.0
    non_negative = sorted(max(0, value) for value in values)
    total = sum(non_negative)
    if total == 0:
        return 0.0
    n = len(non_negative)
    weighted_sum = sum((idx + 1) * value for idx, value in enumerate(non_negative))
    return (2.0 * weighted_sum) / (n * total) - (n + 1) / n


def zipf_slope(values: list[int]) -> float:
    freqs = sorted((value for value in values if value > 0), reverse=True)
    if len(freqs) < 2:
        return 0.0
    xs = [math.log(rank) for rank in range(1, len(freqs) + 1)]
    ys = [math.log(freq) for freq in freqs]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def identifier_metrics(
    features: CodeFeatures | None,
    code_token_count: int,
    nonempty_line_count: int,
) -> dict[str, float | int]:
    if not features:
        return {
            "identifier_name_ref_unique_count": 0,
            "identifier_attr_unique_count": 0,
            "identifier_func_unique_count": 0,
            "identifier_ref_total": 0,
            "identifier_ref_density": 0.0,
            "identifier_token_ratio": 0.0,
            "identifier_line_density": 0.0,
            "identifier_reuse_ratio": 0.0,
            "identifier_entropy": 0.0,
            "identifier_entropy_norm": 0.0,
            "identifier_top_ref_share": 0.0,
            "identifier_avg_len": 0.0,
            "identifier_median_len": 0.0,
            "identifier_long_ratio": 0.0,
            "identifier_short_ratio": 0.0,
            "identifier_underscore_ratio": 0.0,
            "identifier_keyword_ratio": 0.0,
            "identifier_builtin_ratio": 0.0,
            "identifier_semantic_count": 0,
            "identifier_semantic_ratio": 0.0,
            "identifier_prefix3_unique_count": 0,
            "identifier_prefix3_ratio": 0.0,
            "identifier_call_name_total": 0,
            "identifier_attr_ref_total": 0,
            "identifier_hhi": 0.0,
            "identifier_gini": 0.0,
            "identifier_zipf_slope": 0.0,
            "identifier_top_20pct_share": 0.0,
            "identifier_top5_share": 0.0,
            "identifier_single_use_ratio": 0.0,
        }

    id_counts = combine_identifier_counts(features)
    identifiers = sorted(id_counts.keys())
    identifier_count = len(identifiers)
    ref_total = int(sum(id_counts.values()))
    lengths = [len(name) for name in identifiers]
    lengths_sorted = sorted(lengths)
    median_len = lengths_sorted[len(lengths_sorted) // 2] if lengths_sorted else 0.0
    long_ratio = safe_div(sum(1 for n in identifiers if len(n) >= 12), identifier_count)
    short_ratio = safe_div(sum(1 for n in identifiers if len(n) <= 2), identifier_count)
    underscore_ratio = safe_div(sum(1 for n in identifiers if "_" in n), identifier_count)
    keyword_ratio = safe_div(sum(1 for n in identifiers if n in PY_KEYWORDS), identifier_count)
    builtin_ratio = safe_div(sum(1 for n in identifiers if n in PY_BUILTINS), identifier_count)
    semantic_count = sum(
        1 for name in identifiers if any(token in name for token in IDENTIFIER_SIGNAL_TOKENS)
    )
    prefix3 = {name[:3] for name in identifiers if len(name) >= 3}
    max_ref = max(id_counts.values(), default=0)
    freq_values = sorted(id_counts.values(), reverse=True)
    top_k = max(1, math.ceil(0.2 * identifier_count)) if identifier_count else 1
    top_20pct_share = safe_div(sum(freq_values[:top_k]), ref_total)
    top5_share = safe_div(sum(freq_values[:5]), ref_total)
    hhi = sum((count / ref_total) ** 2 for count in freq_values) if ref_total else 0.0
    gini = gini_coefficient(freq_values)
    slope = zipf_slope(freq_values)
    single_use_ratio = safe_div(sum(1 for count in freq_values if count == 1), identifier_count)

    entropy = 0.0
    if ref_total > 0:
        probs = [count / ref_total for count in id_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    entropy_norm = safe_div(entropy, math.log2(identifier_count)) if identifier_count > 1 else 0.0

    return {
        "identifier_name_ref_unique_count": len(features.name_refs),
        "identifier_attr_unique_count": len(features.attr_names),
        "identifier_func_unique_count": len(features.func_names),
        "identifier_ref_total": ref_total,
        "identifier_ref_density": round_metric(safe_div(ref_total, nonempty_line_count)),
        "identifier_token_ratio": round_metric(safe_div(identifier_count, max(1, code_token_count))),
        "identifier_line_density": round_metric(safe_div(identifier_count, nonempty_line_count)),
        "identifier_reuse_ratio": round_metric(safe_div(ref_total, max(1, identifier_count))),
        "identifier_entropy": round_metric(entropy),
        "identifier_entropy_norm": round_metric(entropy_norm),
        "identifier_top_ref_share": round_metric(safe_div(max_ref, max(1, ref_total))),
        "identifier_avg_len": round_metric(safe_div(sum(lengths), max(1, len(lengths)))),
        "identifier_median_len": round_metric(median_len),
        "identifier_long_ratio": round_metric(long_ratio),
        "identifier_short_ratio": round_metric(short_ratio),
        "identifier_underscore_ratio": round_metric(underscore_ratio),
        "identifier_keyword_ratio": round_metric(keyword_ratio),
        "identifier_builtin_ratio": round_metric(builtin_ratio),
        "identifier_semantic_count": semantic_count,
        "identifier_semantic_ratio": round_metric(safe_div(semantic_count, max(1, identifier_count))),
        "identifier_prefix3_unique_count": len(prefix3),
        "identifier_prefix3_ratio": round_metric(safe_div(len(prefix3), max(1, identifier_count))),
        "identifier_call_name_total": int(sum(features.call_name_counts.values())),
        "identifier_attr_ref_total": int(sum(features.attr_ref_counts.values())),
        "identifier_hhi": round_metric(hhi),
        "identifier_gini": round_metric(gini),
        "identifier_zipf_slope": round_metric(slope),
        "identifier_top_20pct_share": round_metric(top_20pct_share),
        "identifier_top5_share": round_metric(top5_share),
        "identifier_single_use_ratio": round_metric(single_use_ratio),
    }


def extract_comment_data(code_text: str) -> tuple[list[str], int, int]:
    if not code_text:
        return [], 0, 0
    lines = code_text.splitlines()
    comments: list[str] = []
    inline_count = 0
    full_line_count = 0
    try:
        for token_info in tokenize.generate_tokens(io.StringIO(code_text).readline):
            if token_info.type != tokenize.COMMENT:
                continue
            line_idx = max(0, token_info.start[0] - 1)
            prefix = lines[line_idx][: token_info.start[1]] if line_idx < len(lines) else ""
            if prefix.strip():
                inline_count += 1
            else:
                full_line_count += 1
            cleaned = token_info.string.lstrip("#").strip()
            if cleaned:
                comments.append(cleaned)
    except (tokenize.TokenError, IndentationError):
        for line in lines:
            if "#" not in line:
                continue
            prefix, _, suffix = line.partition("#")
            if not suffix.strip():
                continue
            if prefix.strip():
                inline_count += 1
            else:
                full_line_count += 1
            comments.append(suffix.strip())
    return comments, inline_count, full_line_count


def comment_alignment_metrics(
    comment_lines: list[str],
    inline_comment_count: int,
    full_comment_count: int,
    thought_text: str,
    output_text: str,
    code_text: str,
    features: CodeFeatures | None,
    nonempty_line_count: int,
) -> dict[str, float | int]:
    comment_text = "\n".join(comment_lines)
    comment_tokens = tokenize_words(comment_text)
    comment_vocab = content_vocab(comment_text)
    thought_vocab = content_vocab(thought_text)
    output_vocab = content_vocab(output_text)
    code_vocab = content_vocab(code_text)

    strategy_count = sum(1 for token in comment_tokens if token in ALL_STRATEGY_TERMS)
    robustness_count = sum(1 for token in comment_tokens if token in ROBUSTNESS_LEXICON)
    modal_count = sum(1 for token in comment_tokens if token in MODAL_WORDS)
    action_count = sum(1 for token in comment_tokens if token in ACTION_LEXICON)
    todo_count = sum(1 for line in comment_lines if re.search(r"\b(todo|fixme|hack|xxx)\b", line.lower()))
    question_count = sum(1 for line in comment_lines if line.strip().endswith("?"))

    identifier_vocab: set[str] = set()
    if features:
        identifier_vocab = {
            token.lower() for token in (features.name_refs | features.attr_names | features.func_names)
        }
    comment_identifier_overlap = comment_vocab & identifier_vocab

    return {
        "comment_tokenized_line_count": len(comment_lines),
        "comment_inline_count": inline_comment_count,
        "comment_full_line_count": full_comment_count,
        "comment_inline_ratio": round_metric(safe_div(inline_comment_count, max(1, len(comment_lines)))),
        "comment_word_count": len(comment_tokens),
        "comment_avg_words": round_metric(safe_div(len(comment_tokens), max(1, len(comment_lines)))),
        "comment_density_tokenized": round_metric(safe_div(len(comment_lines), nonempty_line_count)),
        "comment_strategy_term_density": round_metric(safe_div(strategy_count, max(1, len(comment_tokens)))),
        "comment_robustness_term_density": round_metric(
            safe_div(robustness_count, max(1, len(comment_tokens)))
        ),
        "comment_modal_density": round_metric(safe_div(modal_count, max(1, len(comment_tokens)))),
        "comment_action_density": round_metric(safe_div(action_count, max(1, len(comment_tokens)))),
        "comment_todo_ratio": round_metric(safe_div(todo_count, max(1, len(comment_lines)))),
        "comment_question_ratio": round_metric(safe_div(question_count, max(1, len(comment_lines)))),
        "comment_thought_jaccard": round_metric(
            safe_div(len(comment_vocab & thought_vocab), max(1, len(comment_vocab | thought_vocab)))
        ),
        "comment_output_jaccard": round_metric(
            safe_div(len(comment_vocab & output_vocab), max(1, len(comment_vocab | output_vocab)))
        ),
        "comment_code_jaccard": round_metric(
            safe_div(len(comment_vocab & code_vocab), max(1, len(comment_vocab | code_vocab)))
        ),
        "comment_identifier_precision": round_metric(
            safe_div(len(comment_identifier_overlap), max(1, len(comment_vocab)))
        ),
        "comment_identifier_coverage": round_metric(
            safe_div(len(comment_identifier_overlap), max(1, len(identifier_vocab)))
        ),
    }


def detect_strategy_concepts(text: str) -> set[str]:
    text_lower = (text or "").lower()
    hits: set[str] = set()
    for concept, patterns in STRATEGY_CONCEPT_PATTERNS.items():
        if any(re.search(pattern, text_lower) for pattern in patterns):
            hits.add(concept)
    return hits


def concept_translation_metrics(
    thought_text: str,
    code_text: str,
    output_text: str,
    comment_text: str,
) -> dict[str, float | int]:
    thought_concepts = detect_strategy_concepts(thought_text)
    code_concepts = detect_strategy_concepts(code_text)
    output_concepts = detect_strategy_concepts(output_text)
    comment_concepts = detect_strategy_concepts(comment_text)

    overlap = thought_concepts & code_concepts
    precision = safe_div(len(overlap), len(code_concepts))
    recall = safe_div(len(overlap), len(thought_concepts))
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else 0.0
    agreement_count = sum(
        1
        for concept in STRATEGY_CONCEPT_PATTERNS
        if int(concept in thought_concepts)
        + int(concept in code_concepts)
        + int(concept in output_concepts)
        + int(concept in comment_concepts)
        >= 3
    )

    metrics: dict[str, float | int] = {
        "concept_thought_count": len(thought_concepts),
        "concept_code_count": len(code_concepts),
        "concept_output_count": len(output_concepts),
        "concept_comment_count": len(comment_concepts),
        "concept_realization_precision": round_metric(precision),
        "concept_realization_recall": round_metric(recall),
        "concept_realization_f1": round_metric(f1),
        "concept_overreach_count": len(code_concepts - thought_concepts),
        "concept_underreach_count": len(thought_concepts - code_concepts),
        "concept_alignment_jaccard": round_metric(
            safe_div(len(thought_concepts & code_concepts), max(1, len(thought_concepts | code_concepts)))
        ),
        "concept_output_support_ratio": round_metric(
            safe_div(len(code_concepts & output_concepts), max(1, len(code_concepts)))
        ),
        "concept_comment_support_ratio": round_metric(
            safe_div(len(code_concepts & comment_concepts), max(1, len(code_concepts)))
        ),
        "concept_cross_source_agreement_ratio": round_metric(
            safe_div(agreement_count, len(STRATEGY_CONCEPT_PATTERNS))
        ),
    }

    for concept in sorted(STRATEGY_CONCEPT_PATTERNS):
        metrics[f"thought_concept_{concept}"] = int(concept in thought_concepts)
        metrics[f"code_concept_{concept}"] = int(concept in code_concepts)
        metrics[f"output_concept_{concept}"] = int(concept in output_concepts)
        metrics[f"comment_concept_{concept}"] = int(concept in comment_concepts)

    return metrics


def thought_code_translation_metrics(
    thought_text: str,
    code_text: str,
    output_text: str,
    features: CodeFeatures | None,
) -> dict[str, float | int]:
    thought_vocab = content_vocab(thought_text)
    code_vocab = content_vocab(code_text)
    output_vocab = content_vocab(output_text)

    thought_code_overlap = thought_vocab & code_vocab
    thought_output_overlap = thought_vocab & output_vocab
    code_output_overlap = code_vocab & output_vocab

    identifier_vocab: set[str] = set()
    if features:
        identifier_vocab = {
            token.lower() for token in (features.name_refs | features.attr_names | features.func_names)
        }

    thought_strategy_terms = thought_vocab & ALL_STRATEGY_TERMS
    code_strategy_terms = code_vocab & ALL_STRATEGY_TERMS
    overlap_strategy = thought_strategy_terms & code_strategy_terms
    strategy_precision = safe_div(len(overlap_strategy), len(code_strategy_terms))
    strategy_recall = safe_div(len(overlap_strategy), len(thought_strategy_terms))
    strategy_f1 = (
        2 * strategy_precision * strategy_recall / (strategy_precision + strategy_recall)
        if (strategy_precision and strategy_recall)
        else 0.0
    )
    thought_action_terms = thought_vocab & ACTION_LEXICON
    realized_action_terms = thought_action_terms & code_vocab

    return {
        "thought_content_vocab_size": len(thought_vocab),
        "code_content_vocab_size": len(code_vocab),
        "output_content_vocab_size": len(output_vocab),
        "thought_code_content_jaccard": round_metric(
            safe_div(len(thought_code_overlap), max(1, len(thought_vocab | code_vocab)))
        ),
        "thought_code_content_recall": round_metric(
            safe_div(len(thought_code_overlap), max(1, len(thought_vocab)))
        ),
        "thought_code_content_precision": round_metric(
            safe_div(len(thought_code_overlap), max(1, len(code_vocab)))
        ),
        "thought_output_content_jaccard": round_metric(
            safe_div(len(thought_output_overlap), max(1, len(thought_vocab | output_vocab)))
        ),
        "code_output_content_jaccard": round_metric(
            safe_div(len(code_output_overlap), max(1, len(code_vocab | output_vocab)))
        ),
        "thought_identifier_hit_ratio": round_metric(
            safe_div(len(thought_vocab & identifier_vocab), max(1, len(thought_vocab)))
        ),
        "output_identifier_hit_ratio": round_metric(
            safe_div(len(output_vocab & identifier_vocab), max(1, len(output_vocab)))
        ),
        "strategy_term_precision": round_metric(strategy_precision),
        "strategy_term_recall": round_metric(strategy_recall),
        "strategy_term_f1": round_metric(strategy_f1),
        "action_term_realization_ratio": round_metric(
            safe_div(len(realized_action_terms), max(1, len(thought_action_terms)))
        ),
    }


def prompt_constraint_metrics(run: RunRecord, thought_text: str, code_text: str, output_text: str) -> dict[str, float | int]:
    info = run.info if isinstance(run.info, dict) else {}
    prompt = info.get("prompt", "") if isinstance(info, dict) else ""
    prompt_text = prompt if isinstance(prompt, str) else ""
    prompt_lower = prompt_text.lower()

    prompt_tokens = tokenize_words(prompt_text)
    prompt_vocab = content_vocab(prompt_text)
    thought_vocab = content_vocab(thought_text)
    code_vocab = content_vocab(code_text)
    output_vocab = content_vocab(output_text)

    prompt_constraint_terms = {kw for kw in CONSTRAINT_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", prompt_lower)}
    thought_tokens = set(tokenize_words(thought_text))
    code_tokens = set(tokenize_words(code_text))
    output_tokens = set(tokenize_words(output_text))
    prompt_strategy_terms = prompt_vocab & ALL_STRATEGY_TERMS

    return {
        "prompt_len": len(prompt_text),
        "prompt_word_count": len(prompt_tokens),
        "prompt_constraint_count": len(prompt_constraint_terms),
        "prompt_constraint_coverage_thought": round_metric(
            safe_div(len(prompt_constraint_terms & thought_tokens), max(1, len(prompt_constraint_terms)))
        ),
        "prompt_constraint_coverage_code": round_metric(
            safe_div(len(prompt_constraint_terms & code_tokens), max(1, len(prompt_constraint_terms)))
        ),
        "prompt_constraint_coverage_output": round_metric(
            safe_div(len(prompt_constraint_terms & output_tokens), max(1, len(prompt_constraint_terms)))
        ),
        "prompt_strategy_term_count": len(prompt_strategy_terms),
        "prompt_strategy_coverage_thought": round_metric(
            safe_div(len(prompt_strategy_terms & thought_vocab), max(1, len(prompt_strategy_terms)))
        ),
        "prompt_strategy_coverage_code": round_metric(
            safe_div(len(prompt_strategy_terms & code_vocab), max(1, len(prompt_strategy_terms)))
        ),
        "prompt_strategy_coverage_output": round_metric(
            safe_div(len(prompt_strategy_terms & output_vocab), max(1, len(prompt_strategy_terms)))
        ),
        "prompt_thought_content_jaccard": round_metric(
            safe_div(len(prompt_vocab & thought_vocab), max(1, len(prompt_vocab | thought_vocab)))
        ),
        "prompt_code_content_jaccard": round_metric(
            safe_div(len(prompt_vocab & code_vocab), max(1, len(prompt_vocab | code_vocab)))
        ),
        "prompt_output_content_jaccard": round_metric(
            safe_div(len(prompt_vocab & output_vocab), max(1, len(prompt_vocab | output_vocab)))
        ),
        "prompt_mentions_policy_api": int("def policy" in prompt_lower),
        "prompt_mentions_move_format": int(bool(re.search(r"row,col", prompt_lower))),
        "prompt_mentions_time_budget": int(bool(re.search(r"\btime\b|\bseconds?\b|\btimeout\b", prompt_lower))),
    }


def literal_structure_metrics(code_text: str) -> dict[str, float | int]:
    defaults = {
        "numeric_literal_count": 0,
        "distinct_numeric_literal_count": 0,
        "numeric_negative_ratio": 0.0,
        "numeric_small_abs_ratio": 0.0,
        "numeric_integer_ratio": 0.0,
        "numeric_spread": 0.0,
        "literal_negative_one_count": 0,
        "literal_zero_count": 0,
        "literal_one_count": 0,
        "literal_board_dim_count": 0,
        "string_literal_count": 0,
        "string_format_hint_count": 0,
        "bool_literal_count": 0,
        "none_literal_count": 0,
        "list_literal_count": 0,
        "tuple_literal_count": 0,
        "dict_literal_count": 0,
        "set_literal_count": 0,
        "fstring_count": 0,
        "lambda_count": 0,
        "literal_token_density": 0.0,
        "policy_signature_exact": 0,
        "move_format_pattern_count": 0,
    }
    if not code_text:
        return defaults

    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        metrics = dict(defaults)
        metrics["policy_signature_exact"] = int(
            bool(re.search(r"def\s+policy\s*\(\s*board\s*\)\s*(?:->\s*str)?\s*:", code_text))
        )
        metrics["move_format_pattern_count"] = len(
            re.findall(r"\d,\d:\d,\d:\d,\d", code_text)
        )
        return metrics

    numeric_values: list[float] = []
    string_literals: list[str] = []
    bool_count = 0
    none_count = 0
    list_count = 0
    tuple_count = 0
    dict_count = 0
    set_count = 0
    fstring_count = 0
    lambda_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool):
                bool_count += 1
            elif value is None:
                none_count += 1
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                numeric_values.append(float(value))
            elif isinstance(value, str):
                string_literals.append(value)
        elif isinstance(node, ast.List):
            list_count += 1
        elif isinstance(node, ast.Tuple):
            tuple_count += 1
        elif isinstance(node, ast.Dict):
            dict_count += 1
        elif isinstance(node, ast.Set):
            set_count += 1
        elif isinstance(node, ast.JoinedStr):
            fstring_count += 1
        elif isinstance(node, ast.Lambda):
            lambda_count += 1

    numeric_count = len(numeric_values)
    distinct_numeric_count = len({round(value, 8) for value in numeric_values})
    negative_ratio = safe_div(sum(1 for value in numeric_values if value < 0), numeric_count)
    small_abs_ratio = safe_div(sum(1 for value in numeric_values if abs(value) <= 8), numeric_count)
    integer_ratio = safe_div(
        sum(1 for value in numeric_values if float(value).is_integer()),
        numeric_count,
    )
    numeric_spread = max(numeric_values) - min(numeric_values) if numeric_count else 0.0
    negative_one_count = sum(1 for value in numeric_values if value == -1)
    zero_count = sum(1 for value in numeric_values if value == 0)
    one_count = sum(1 for value in numeric_values if value == 1)
    board_dim_count = sum(1 for value in numeric_values if value in {6, 8})
    string_format_hint_count = sum(1 for value in string_literals if ":" in value and "," in value)
    literal_density = safe_div(
        numeric_count + len(string_literals) + bool_count + none_count,
        max(1, len(tokenize_words(code_text))),
    )

    return {
        "numeric_literal_count": numeric_count,
        "distinct_numeric_literal_count": distinct_numeric_count,
        "numeric_negative_ratio": round_metric(negative_ratio),
        "numeric_small_abs_ratio": round_metric(small_abs_ratio),
        "numeric_integer_ratio": round_metric(integer_ratio),
        "numeric_spread": round_metric(numeric_spread),
        "literal_negative_one_count": negative_one_count,
        "literal_zero_count": zero_count,
        "literal_one_count": one_count,
        "literal_board_dim_count": board_dim_count,
        "string_literal_count": len(string_literals),
        "string_format_hint_count": string_format_hint_count,
        "bool_literal_count": bool_count,
        "none_literal_count": none_count,
        "list_literal_count": list_count,
        "tuple_literal_count": tuple_count,
        "dict_literal_count": dict_count,
        "set_literal_count": set_count,
        "fstring_count": fstring_count,
        "lambda_count": lambda_count,
        "literal_token_density": round_metric(literal_density),
        "policy_signature_exact": int(
            bool(re.search(r"def\s+policy\s*\(\s*board\s*\)\s*(?:->\s*str)?\s*:", code_text))
        ),
        "move_format_pattern_count": len(re.findall(r"\d,\d:\d,\d:\d,\d", code_text)),
    }


def build_metrics(
    run: RunRecord,
    code_analysis: CodeAnalysis,
    thought_tags: set[str],
    alignment: dict[str, float],
) -> dict[str, float | int]:
    code_tags = code_analysis.tags
    features = code_analysis.features
    stats = code_analysis.stats

    tag_overlap = code_tags & thought_tags
    tag_union = code_tags | thought_tags
    code_only = code_tags - thought_tags
    thought_only = thought_tags - code_tags
    tag_symdiff = code_tags ^ thought_tags

    code_tag_count = len(code_tags)
    thought_tag_count = len(thought_tags)
    overlap_count = len(tag_overlap)
    union_count = len(tag_union)
    code_only_count = len(code_only)
    thought_only_count = len(thought_only)

    search_tag_count = len(code_tags & SEARCH_TAGS)
    tree_search_tag_count = len(code_tags & TREE_SEARCH_TAGS)
    optimization_tag_count = len(code_tags & OPTIMIZATION_TAGS)
    heuristic_tag_count = len(code_tags & HEURISTIC_TAGS)
    stochastic_tag_count = len(code_tags & STOCHASTIC_TAGS)
    ml_tag_count = len(code_tags & ML_TAGS)
    advanced_tag_count = search_tag_count + optimization_tag_count + heuristic_tag_count + ml_tag_count

    thought_sophistication_score = weighted_tag_score(thought_tags)
    code_sophistication_score = weighted_tag_score(code_tags)

    policy_func_present = 1 if (features and "policy" in features.func_names) else 0
    recursion_count = recursive_function_count(features)
    func_count = len(features.func_names) if features else 0
    call_count = features.call_count if features else 0
    attr_count = len(features.attr_names) if features else 0
    import_count = len(features.imports) if features else 0
    identifier_count = len(features.name_refs | features.attr_names | features.func_names) if features else 0
    for_count = features.for_count if features else 0
    while_count = features.while_count if features else 0
    if_count = features.if_count if features else 0
    try_count = features.try_count if features else 0
    with_count = features.with_count if features else 0
    return_count = features.return_count if features else 0
    assign_count = features.assign_count if features else 0
    comprehension_count = features.comprehension_count if features else 0
    max_control_depth = features.max_control_depth if features else 0
    avg_func_args = safe_div(sum(len(args) for args in features.func_args), len(features.func_args)) if features else 0.0
    max_func_args = max((len(args) for args in features.func_args), default=0) if features else 0

    loop_count = for_count + while_count
    control_stmt_count = loop_count + if_count + try_count + with_count
    nonempty_line_count = max(1, stats.nonempty_line_count)

    code_text = run.code_text or ""
    comment_lines, inline_comment_count, full_comment_count = extract_comment_data(code_text)
    comment_text = "\n".join(comment_lines)
    output_text = run.output_text or ""
    output_lower = output_text.lower()
    thought_text = run.thought_text or ""
    thought_lower = thought_text.lower()

    output_length = len(output_text)
    thought_length = len(thought_text)
    thought_words = word_count(thought_text)
    line_count = stats.line_count
    id_metrics = identifier_metrics(features, stats.approx_token_count, nonempty_line_count)
    comment_metrics = comment_alignment_metrics(
        comment_lines,
        inline_comment_count,
        full_comment_count,
        thought_text,
        output_text,
        code_text,
        features,
        nonempty_line_count,
    )
    concept_metrics = concept_translation_metrics(thought_text, code_text, output_text, comment_text)
    translation_metrics = thought_code_translation_metrics(thought_text, code_text, output_text, features)
    prompt_metrics = prompt_constraint_metrics(run, thought_text, code_text, output_text)
    literal_metrics = literal_structure_metrics(code_text)

    return {
        # Backward-compatible keys expected by existing analysis tooling.
        "precision": round_metric(alignment["precision"]),
        "recall": round_metric(alignment["recall"]),
        "f1": round_metric(alignment["f1"]),
        "code_len": stats.code_length,
        # Tag alignment coverage and consistency.
        "code_tag_count": code_tag_count,
        "thought_tag_count": thought_tag_count,
        "overlap_tag_count": overlap_count,
        "union_tag_count": union_count,
        "code_only_tag_count": code_only_count,
        "thought_only_tag_count": thought_only_count,
        "symdiff_tag_count": len(tag_symdiff),
        "tag_jaccard": round_metric(safe_div(overlap_count, union_count)),
        "tag_balance": round_metric(safe_div(code_tag_count - thought_tag_count, union_count)),
        "thought_coverage_gap": round_metric(safe_div(thought_only_count, thought_tag_count)),
        "implementation_overreach": round_metric(safe_div(code_only_count, code_tag_count)),
        # Algorithm/style profile.
        "search_tag_count": search_tag_count,
        "tree_search_tag_count": tree_search_tag_count,
        "optimization_tag_count": optimization_tag_count,
        "heuristic_tag_count": heuristic_tag_count,
        "stochastic_tag_count": stochastic_tag_count,
        "ml_tag_count": ml_tag_count,
        "advanced_tag_count": advanced_tag_count,
        "weighted_code_tag_score": round_metric(code_sophistication_score),
        "weighted_thought_tag_score": round_metric(thought_sophistication_score),
        "weighted_tag_gap": round_metric(code_sophistication_score - thought_sophistication_score),
        "has_tree_search": int(tree_search_tag_count > 0),
        "has_alpha_beta": int("alpha_beta" in code_tags),
        "has_mcts": int("mcts" in code_tags),
        "has_transposition_table": int("transposition_table" in code_tags),
        "has_move_ordering": int("move_ordering" in code_tags),
        "has_time_cutoff": int("time_cutoff" in code_tags),
        "has_random": int("random" in code_tags),
        "has_greedy": int("greedy" in code_tags),
        # Code shape and complexity proxies.
        "ast_parse_success": int(code_analysis.ast_parse_success),
        "policy_func_present": policy_func_present,
        "function_count": func_count,
        "avg_func_args": round_metric(avg_func_args),
        "max_func_args": max_func_args,
        "call_count": call_count,
        "unique_call_names": len(features.call_names) if features else 0,
        "unique_attr_names": attr_count,
        "import_count": import_count,
        "identifier_count": identifier_count,
        "for_count": for_count,
        "while_count": while_count,
        "if_count": if_count,
        "try_count": try_count,
        "with_count": with_count,
        "return_count": return_count,
        "assign_count": assign_count,
        "identifier_assign_sum": identifier_count + assign_count,
        "identifier_line_sum": identifier_count + line_count,
        "assign_line_sum": assign_count + line_count,
        "identifier_assign_line_sum": identifier_count + assign_count + line_count,
        "comprehension_count": comprehension_count,
        "loop_count": loop_count,
        "control_stmt_count": control_stmt_count,
        "max_control_depth": max_control_depth,
        "recursion_function_count": recursion_count,
        "branching_density": round_metric(safe_div(control_stmt_count, nonempty_line_count)),
        "call_density": round_metric(safe_div(call_count, nonempty_line_count)),
        "function_density": round_metric(safe_div(func_count, nonempty_line_count)),
        **id_metrics,
        # Code formatting/textual signals.
        "code_lines": stats.line_count,
        "code_nonempty_lines": stats.nonempty_line_count,
        "code_comment_lines": stats.comment_line_count,
        "code_comment_density": round_metric(safe_div(stats.comment_line_count, nonempty_line_count)),
        "code_avg_line_len": round_metric(stats.avg_line_length),
        "code_long_line_ratio": round_metric(stats.long_line_ratio),
        "code_token_count": stats.approx_token_count,
        # Response-format and planning-text signals.
        "output_len": output_length,
        "thought_len": thought_length,
        "thought_word_count": thought_words,
        "thought_to_code_ratio": round_metric(safe_div(thought_length, max(1, stats.code_length))),
        "output_to_code_ratio": round_metric(safe_div(output_length, max(1, stats.code_length))),
        "has_code_tags_in_output": int(bool(CODE_TAG_RE.search(output_text))),
        "has_thinking_tags_in_output": int(bool(THINKING_RE.search(output_text))),
        "mentions_legality": int(bool(re.search(r"\blegal\b|\bvalid move\b|\balways return\b|\bmust return\b", thought_lower))),
        "mentions_fallback": int(bool(re.search(r"\bfallback\b|\brobust\b|\bif no legal moves\b", thought_lower))),
        "mentions_time_budget": int(bool(re.search(r"\btime limit\b|\bdeadline\b|\bseconds?\b", thought_lower))),
        "mentions_search_depth": int(bool(re.search(r"\bdepth\b|\blookahead\b|\bply\b", thought_lower))),
        "mentions_mobility": int(bool("mobility" in thought_lower)),
        "mentions_center_control": int(bool("center" in thought_lower or "central" in thought_lower)),
        "output_contains_code_fence": int("```" in output_text),
        "output_contains_python_word": int("python" in output_lower),
        # Cross-source strategy translation and comment semantics.
        **comment_metrics,
        **concept_metrics,
        **translation_metrics,
        **prompt_metrics,
        **literal_metrics,
    }


def collect_game_arena_runs(root: Path) -> list[RunRecord]:
    base = root / "src" / "game_arena"
    if not base.exists():
        return []
    runs = []
    for output_path in base.rglob("1.output.txt"):
        if "trash" in output_path.parts:
            continue
        run_dir = output_path.parent
        if not run_dir.name.isdigit():
            continue
        parts = output_path.parts
        try:
            idx = parts.index("game_arena")
            game = parts[idx + 1]
            if parts[idx + 2] != "examples":
                continue
            world = parts[idx + 3]
            model = parts[idx + 4]
            run = parts[idx + 5]
        except (ValueError, IndexError):
            continue

        info_path = run_dir / "0.info.json"
        code_path = run_dir / "2.python_code.py"
        output_text = load_output_text(output_path)
        info = json.loads(safe_read_text(info_path)) if info_path.exists() else None
        code_text = safe_read_text(code_path) if code_path.exists() else extract_code_from_output(output_text)
        thought_text = extract_thinking(output_text)
        runs.append(
            RunRecord(
                game=game,
                world=world,
                model=model,
                run=run,
                run_dir=str(run_dir.relative_to(root)),
                info=info,
                output_text=output_text,
                thought_text=thought_text,
                code_text=code_text,
            )
        )
    return runs


def record_from_run(run: RunRecord) -> dict[str, Any]:
    code_analysis = analyze_code(run.code_text)
    code_tags = code_analysis.tags
    thought_tags = detect_text_tags(run.thought_text, THOUGHT_TEXT_RULES)
    alignment = alignment_metrics(thought_tags, code_tags)
    metrics = build_metrics(run, code_analysis, thought_tags, alignment)
    code_only = sorted(code_tags - thought_tags)
    thought_only = sorted(thought_tags - code_tags)
    code_tags_list = sorted(code_tags)
    thought_tags_list = sorted(thought_tags)
    code_length = code_analysis.stats.code_length
    return {
        "game": run.game,
        "world": run.world,
        "model": run.model,
        "run": run.run,
        "run_dir": run.run_dir,
        "code_tags": code_tags_list,
        "thought_tags": thought_tags_list,
        "code_length": code_length,
        "code_tags_str": ";".join(code_tags_list),
        "thought_tags_str": ";".join(thought_tags_list),
        "alignment_precision": round_metric(alignment["precision"]),
        "alignment_recall": round_metric(alignment["recall"]),
        "alignment_f1": round_metric(alignment["f1"]),
        "code_only_tags": code_only,
        "thought_only_tags": thought_only,
        "code_only_tags_str": ";".join(code_only),
        "thought_only_tags_str": ";".join(thought_only),
        "metrics": metrics,
    }


def main() -> None:
    args = parse_args()
    root = args.root
    json_path = args.json_path
    runs: list[RunRecord] = collect_game_arena_runs(root)
    records = [record_from_run(run) for run in runs]
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} run records to {json_path}")


if __name__ == "__main__":
    main()
