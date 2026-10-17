from typing import Iterable, Optional

def _render_section(title: str, lines: Iterable[str]) -> str:
    """
    Render a single markdown-style section with bullet points.
    """
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return ""

    body = "\n".join(f"- {line}" for line in lines)
    return f"# {title}\n\n{body}"


def _render_raw_section(title: str, content: str) -> str:
    """
    Render a section where the caller provides preformatted content
    (e.g., code blocks, mixed formatting).
    """
    content = content.strip()
    if not content:
        return ""
    return f"# {title}\n\n{content}"


def render_prompt(
    *,
    role: Iterable[str] = [],
    objective: Iterable[str] = [],
    signature_block: str = '',
    state: Iterable[str] = [],
    action: Iterable[str] = [],
    constraints: Iterable[str] = [],
    output_format: Iterable[str] = [],
    notes: Optional[Iterable[str]] = [],
    example_output: Optional[str] = '',
) -> str:
    """
    Compose a structured prompt using markdown-style headings and lists.
    All inputs are either lists of strings (rendered as bullet points)
    or raw strings for preformatted blocks.
    """

    sections: list[str] = []
    if role:
        sections.append(_render_section("Role", role))
    if objective:
        sections.append(_render_section("Objective", objective))
    if signature_block:
        sections.append(_render_raw_section("Required API", signature_block))
    if state:
        sections.append(_render_section("State Representation", state))
    if action:
        sections.append(_render_section("Action / Return Format", action))
    if constraints:
        sections.append(_render_section("Constraints", constraints))
    if output_format:
        sections.append(_render_section("Output Format Requirements", output_format))

    if notes:
        sections.append(_render_section("Notes", notes))
    if example_output:
        sections.append(_render_raw_section("Example Output", example_output))
    return "\n\n".join(section for section in sections if section).strip() + "\n"


def render_prompt_pre_filled(
    *,
    game_name: str,
    signature_block: str,
    state: Iterable[str],
    action: Iterable[str],
) -> str:
    return render_prompt(
        role=[
            "You are an AI competing in a gaming arena."
        ],
        objective=[
            f"Write a complete Python file that provides the next move for a {game_name}.",
            "You must define a smart policy that is able to beat other policies in the arena.",
            "You will be disqualified if you do not return a legal move string. Therefore, you must always return a legal move string.",
        ],
        signature_block="The provided python file must implement the following API:\n" + signature_block,
        state=state,
        action=action,
        constraints=[
            "You may use any standard Python imports, including numpy.",
            "Your code is allowed 1 second of execution time on a modern 3GHz CPU.",
        ],
        output_format=[
            "Output your strategy before providing the Python source code for your policy.",
            "Output the Python source code for your policy surrounded by `<code>...</code>` tags.",
        ],
        example_output=(
            "The strategy for this policy is...\n"
            "<code>\n"
            "...\n"
            "</code>"
        ),
    )

def render_prompt_for_live_play(
    *,
    game_name: str,
    state: Iterable[str],
    action: Iterable[str],
    example_action: str = '...',
) -> str:
    """This function is only used when attempting to make an LLM play live turn-by-turn, which means this is not the main prompt for this project."""
    return render_prompt(
        role=[
            "You are an AI competing in a gaming arena."
        ],
        objective=[
            f"You will be provided with the current state of the game for a {game_name}.",
            "Your have to provide your next move for the game.",
        ],
        state=state,
        action=action,
        output_format=[
            "Output your next action as a described in the 'Action / Return Format' section using a json",
            "Example response:",
            '{"action": ' + example_action + '}',
        ],
    )
