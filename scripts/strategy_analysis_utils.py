#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import warnings
from dataclasses import dataclass
from typing import Any


TAG_ORDER = [
    "minimax",
    "alpha_beta",
    "mcts",
    "expectimax",
    "iterative_deepening",
    "transposition_table",
    "time_cutoff",
    "random",
    "greedy",
    "heuristic_eval",
    "heuristic_material",
    "heuristic_mobility",
    "heuristic_center_control",
    "heuristic_connectivity",
    "move_ordering",
    "opening_book",
    "quiescence",
    "neural_policy",
]

TREE_SEARCH_TAGS = {"minimax", "mcts", "expectimax"}
SEARCH_TAGS = TREE_SEARCH_TAGS | {"alpha_beta", "iterative_deepening", "quiescence"}
OPTIMIZATION_TAGS = {"transposition_table", "move_ordering", "time_cutoff", "opening_book"}
HEURISTIC_TAGS = {
    "heuristic_eval",
    "heuristic_material",
    "heuristic_mobility",
    "heuristic_center_control",
    "heuristic_connectivity",
}
STOCHASTIC_TAGS = {"random", "greedy"}
ML_TAGS = {"neural_policy"}

TAG_COMPLEXITY_WEIGHTS: dict[str, float] = {
    "minimax": 2.0,
    "alpha_beta": 2.4,
    "mcts": 2.8,
    "expectimax": 2.2,
    "iterative_deepening": 1.5,
    "transposition_table": 1.8,
    "time_cutoff": 1.2,
    "random": -1.0,
    "greedy": -0.3,
    "heuristic_eval": 1.2,
    "heuristic_material": 0.8,
    "heuristic_mobility": 0.9,
    "heuristic_center_control": 0.6,
    "heuristic_connectivity": 0.9,
    "move_ordering": 1.4,
    "opening_book": 0.8,
    "quiescence": 1.7,
    "neural_policy": 2.2,
}

CODE_TEXT_RULES = {
    "minimax": [r"\bminimax\b", r"\bnega[-_ ]?max\b"],
    "alpha_beta": [r"alpha[-_ ]?beta", r"\balpha\b.*\bbeta\b", r"\bprun"],
    "mcts": [
        r"\bmcts\b",
        r"\buct\b",
        r"\bucb\b",
        r"\brollout\b",
        r"\bsimulation\b",
        r"monte[- ]?carlo",
    ],
    "expectimax": [r"\bexpectimax\b"],
    "iterative_deepening": [r"iterative deepening", r"\bfor\s+depth\s+in\s+range\b", r"\bmax_depth\b"],
    "transposition_table": [r"transposition", r"zobrist", r"lru_cache", r"\bmemo\b", r"\bcache\b"],
    "time_cutoff": [r"time_limit", r"deadline", r"time\.time\(", r"perf_counter", r"monotonic", r"max_time"],
    "random": [r"\brandom\b", r"np\.random", r"numpy\.random", r"\brandint\b", r"\bshuffle\b"],
    "greedy": [r"\bgreedy\b"],
    "heuristic_eval": [r"\bevaluate\b", r"\bheuristic\b", r"score_position"],
    "heuristic_material": [r"\bmaterial\b", r"piece_count", r"count_pieces", r"num_pieces"],
    "heuristic_mobility": [r"\bmobility\b", r"legal_moves", r"generate_moves", r"num_moves"],
    "heuristic_center_control": [r"\bcenter\b", r"\bcentral\b"],
    "heuristic_connectivity": [r"\bconnect", r"\bcomponent", r"\bbfs\b", r"\bdfs\b", r"\bunion\b"],
    "move_ordering": [r"move ordering", r"\bsorted\(\s*moves\b", r"\bmoves\.sort\b", r"order_moves"],
    "opening_book": [r"opening", r"\bbook\b"],
    "quiescence": [r"\bquiesc"],
    "neural_policy": [r"\btorch\b", r"\btensorflow\b", r"\bneural\b", r"\bnetwork\b"],
}

THOUGHT_TEXT_RULES = {
    "minimax": [r"\bminimax\b", r"\bnega[- ]?max\b"],
    "alpha_beta": [r"alpha[- ]?beta", r"alpha beta"],
    "mcts": [r"\bmcts\b", r"monte carlo", r"\buct\b", r"\bucb\b", r"rollout"],
    "expectimax": [r"\bexpectimax\b"],
    "iterative_deepening": [r"iterative deepening", r"increasing depth", r"progressive depth"],
    "transposition_table": [r"transposition", r"zobrist", r"hash table", r"memo"],
    "time_cutoff": [r"time limit", r"time cutoff", r"deadline", r"\bseconds\b"],
    "random": [r"\brandom\b", r"\bstochastic\b"],
    "greedy": [r"\bgreedy\b"],
    "heuristic_eval": [r"heuristic", r"evaluation", r"\bscore\b"],
    "heuristic_material": [r"material", r"piece count", r"count pieces"],
    "heuristic_mobility": [r"mobility", r"legal moves"],
    "heuristic_center_control": [r"center", r"central"],
    "heuristic_connectivity": [r"connected", r"connectivity", r"components"],
    "move_ordering": [r"move ordering", r"order moves", r"sort moves"],
    "opening_book": [r"opening book", r"\bopening\b"],
    "quiescence": [r"\bquiescence\b"],
    "neural_policy": [r"neural", r"network", r"policy network"],
}

THINKING_RE = re.compile(r"<thinking>(.*?)</thinking>", re.IGNORECASE | re.DOTALL)
CODE_TAG_RE = re.compile(r"<code>(.*?)</code>", re.IGNORECASE | re.DOTALL)
FENCED_CODE_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


@dataclass
class RunRecord:
    game: str | None
    world: str
    model: str
    run: str
    run_dir: str
    info: dict[str, Any] | None
    output_text: str | None
    thought_text: str | None
    code_text: str | None


@dataclass
class CodeStats:
    code_length: int
    line_count: int
    nonempty_line_count: int
    comment_line_count: int
    avg_line_length: float
    long_line_ratio: float
    approx_token_count: int


@dataclass
class CodeAnalysis:
    tags: set[str]
    features: "CodeFeatures | None"
    stats: CodeStats
    ast_parse_success: bool


class CodeFeatures(ast.NodeVisitor):
    def __init__(self) -> None:
        self.func_names: set[str] = set()
        self.func_name_counts: dict[str, int] = {}
        self.func_args: list[set[str]] = []
        self.call_names: set[str] = set()
        self.call_name_counts: dict[str, int] = {}
        self.attr_names: set[str] = set()
        self.attr_ref_counts: dict[str, int] = {}
        self.imports: set[str] = set()
        self.name_refs: set[str] = set()
        self.name_ref_counts: dict[str, int] = {}
        self.call_count = 0
        self.for_count = 0
        self.while_count = 0
        self.if_count = 0
        self.try_count = 0
        self.with_count = 0
        self.return_count = 0
        self.assign_count = 0
        self.comprehension_count = 0
        self.max_control_depth = 0
        self._current_control_depth = 0
        self._func_stack: list[str] = []
        self.func_calls_within: dict[str, set[str]] = {}

    def _inc(self, bucket: dict[str, int], key: str) -> None:
        bucket[key] = bucket.get(key, 0) + 1

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        func_name = node.name.lower()
        self.func_names.add(func_name)
        self._inc(self.func_name_counts, func_name)
        arg_names = {arg.arg.lower() for arg in node.args.args}
        self.func_args.append(arg_names)
        self.func_calls_within.setdefault(func_name, set())
        self._func_stack.append(func_name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        func_name = node.name.lower()
        self.func_names.add(func_name)
        self._inc(self.func_name_counts, func_name)
        arg_names = {arg.arg.lower() for arg in node.args.args}
        self.func_args.append(arg_names)
        self.func_calls_within.setdefault(func_name, set())
        self._func_stack.append(func_name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        self.call_count += 1
        called_name: str | None = None
        if isinstance(node.func, ast.Name):
            called_name = node.func.id.lower()
            self.call_names.add(called_name)
            self._inc(self.call_name_counts, called_name)
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr.lower()
            self.attr_names.add(called_name)
            self._inc(self.attr_ref_counts, called_name)
        if self._func_stack and called_name:
            self.func_calls_within[self._func_stack[-1]].add(called_name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        key = node.id.lower()
        self.name_refs.add(key)
        self._inc(self.name_ref_counts, key)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        key = node.attr.lower()
        self.attr_names.add(key)
        self._inc(self.attr_ref_counts, key)
        self.generic_visit(node)

    def _enter_control(self) -> None:
        self._current_control_depth += 1
        self.max_control_depth = max(self.max_control_depth, self._current_control_depth)

    def _exit_control(self) -> None:
        self._current_control_depth = max(0, self._current_control_depth - 1)

    def visit_For(self, node: ast.For) -> None:
        self.for_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_While(self, node: ast.While) -> None:
        self.while_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_If(self, node: ast.If) -> None:
        self.if_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_Try(self, node: ast.Try) -> None:
        self.try_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_With(self, node: ast.With) -> None:
        self.with_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.with_count += 1
        self._enter_control()
        self.generic_visit(node)
        self._exit_control()

    def visit_Return(self, node: ast.Return) -> None:
        self.return_count += 1
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.assign_count += 1
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.assign_count += 1
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.assign_count += 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.comprehension_count += 1
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.comprehension_count += 1
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.comprehension_count += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.comprehension_count += 1
        self.generic_visit(node)


def safe_read_text(path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def round_metric(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def word_count(text: str | None) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text))


def compute_code_stats(code_text: str | None) -> CodeStats:
    text = code_text or ""
    code_length = len(text)
    lines = text.splitlines()
    line_count = len(lines)
    stripped_lines = [line.strip() for line in lines]
    nonempty_lines = [line for line in stripped_lines if line]
    nonempty_line_count = len(nonempty_lines)
    comment_line_count = sum(1 for line in nonempty_lines if line.startswith("#"))
    avg_line_length = safe_div(sum(len(line) for line in lines), line_count)
    long_line_count = sum(1 for line in lines if len(line) > 100)
    long_line_ratio = safe_div(long_line_count, line_count)
    approx_token_count = word_count(text)
    return CodeStats(
        code_length=code_length,
        line_count=line_count,
        nonempty_line_count=nonempty_line_count,
        comment_line_count=comment_line_count,
        avg_line_length=avg_line_length,
        long_line_ratio=long_line_ratio,
        approx_token_count=approx_token_count,
    )


def weighted_tag_score(tags: set[str]) -> float:
    return float(sum(TAG_COMPLEXITY_WEIGHTS.get(tag, 0.0) for tag in tags))


def recursive_function_count(features: CodeFeatures | None) -> int:
    if not features:
        return 0
    return sum(1 for func_name, calls in features.func_calls_within.items() if func_name in calls)


def extract_text_from_json(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for key in ("content", "text", "output", "response"):
            value = obj.get(key)
            if isinstance(value, str):
                return value
        if "choices" in obj and isinstance(obj["choices"], list):
            parts = []
            for choice in obj["choices"]:
                if isinstance(choice, dict):
                    msg = choice.get("message")
                    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                        parts.append(msg["content"])
                        continue
                    if isinstance(choice.get("text"), str):
                        parts.append(choice["text"])
            if parts:
                return "\n".join(parts)
    if isinstance(obj, list):
        parts = []
        for item in obj:
            text = extract_text_from_json(item)
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts)
    return ""


def load_output_text(path) -> str | None:
    if not path.exists():
        return None
    if path.suffix == ".txt":
        return safe_read_text(path)
    if path.suffix == ".json":
        data = json.loads(safe_read_text(path))
        text = extract_text_from_json(data)
        return text if text else None
    return None


def strip_code_blocks(text: str) -> str:
    text = CODE_TAG_RE.sub(" ", text)
    text = FENCED_CODE_RE.sub(" ", text)
    return text


def extract_thinking(text: str | None) -> str | None:
    if not text:
        return None
    match = THINKING_RE.search(text)
    if match:
        return match.group(1).strip()
    stripped = strip_code_blocks(text)
    return stripped.strip() if stripped.strip() else None


def extract_code_from_output(text: str | None) -> str | None:
    if not text:
        return None
    candidates = []
    for regex in (CODE_TAG_RE, FENCED_CODE_RE):
        for match in regex.finditer(text):
            snippet = match.group(1).strip()
            if snippet:
                candidates.append(snippet)
    if not candidates:
        return None
    return max(candidates, key=len)


def detect_text_tags(text: str | None, rules: dict[str, list[str]]) -> set[str]:
    if not text:
        return set()
    text_lower = text.lower()
    tags = set()
    for tag, patterns in rules.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                tags.add(tag)
                break
    return tags


def extract_code_features(code_text: str) -> CodeFeatures | None:
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=SyntaxWarning)
            tree = ast.parse(code_text)
    except SyntaxError:
        return None
    features = CodeFeatures()
    features.visit(tree)
    return features


def analyze_code(code_text: str | None) -> CodeAnalysis:
    stats = compute_code_stats(code_text)
    if not code_text:
        return CodeAnalysis(tags=set(), features=None, stats=stats, ast_parse_success=False)

    tags = detect_text_tags(code_text, CODE_TEXT_RULES)
    features = extract_code_features(code_text)
    if not features:
        return CodeAnalysis(tags=tags, features=None, stats=stats, ast_parse_success=False)

    func_names = features.func_names
    call_names = features.call_names
    arg_sets = features.func_args
    names = features.name_refs | features.attr_names
    imports = features.imports
    all_signal_names = func_names | call_names | names

    if {"minimax", "negamax"} & all_signal_names:
        tags.add("minimax")
    if any({"alpha", "beta"} <= args for args in arg_sets):
        tags.add("alpha_beta")
    if {"mcts", "uct", "ucb", "rollout"} & all_signal_names:
        tags.add("mcts")
    if "expectimax" in all_signal_names:
        tags.add("expectimax")
    if {"evaluate", "heuristic", "score", "score_position"} & all_signal_names:
        tags.add("heuristic_eval")
    if "random" in imports or "random" in names or {"choice", "randint", "shuffle"} & all_signal_names:
        tags.add("random")
    if "time" in imports or "time" in names or {"perf_counter", "monotonic", "deadline", "time_limit"} & all_signal_names:
        if re.search(r"time\.time\(|perf_counter|monotonic|deadline|time_limit|max_time", code_text):
            tags.add("time_cutoff")
    if {"lru_cache", "cache", "memo", "transposition", "zobrist"} & all_signal_names:
        tags.add("transposition_table")
    if {"sorted", "sort", "order_moves"} & all_signal_names and {"moves", "legal_moves"} & all_signal_names:
        tags.add("move_ordering")
    if {"depth", "max_depth"} & all_signal_names and features.for_count > 0 and {"minimax", "alpha_beta"} & tags:
        tags.add("iterative_deepening")
    if {"book", "opening"} & all_signal_names:
        tags.add("opening_book")
    if {"mobility", "legal_moves", "generate_moves", "num_moves"} & all_signal_names:
        tags.add("heuristic_mobility")
    if {"material", "piece_count", "count_pieces", "num_pieces"} & all_signal_names:
        tags.add("heuristic_material")
    if {"center", "central"} & all_signal_names:
        tags.add("heuristic_center_control")
    if {"connectivity", "connected", "component", "bfs", "dfs", "union"} & all_signal_names:
        tags.add("heuristic_connectivity")
    if {"quiescence", "quiesce"} & all_signal_names:
        tags.add("quiescence")
    if {"torch", "tensorflow", "keras"} & (imports | names):
        tags.add("neural_policy")

    return CodeAnalysis(tags=tags, features=features, stats=stats, ast_parse_success=True)


def alignment_metrics(thought_tags: set[str], code_tags: set[str]) -> dict[str, float]:
    if not thought_tags and not code_tags:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    intersection = thought_tags & code_tags
    precision = len(intersection) / len(code_tags) if code_tags else 0.0
    recall = len(intersection) / len(thought_tags) if thought_tags else 0.0
    if precision and recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    return {"precision": precision, "recall": recall, "f1": f1}
