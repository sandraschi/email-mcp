"""Shared creative email workflow templates -- used by both MCP tools and REST API."""

WORKFLOW_TEMPLATES: dict[str, str] = {
    "love-letter": "Write a love letter. Make it {tone} and {mood}. The recipient is my {recipient}. Sign it with love. Output format: {fmt_text}",
    "breakup": "Write a breakup email to my {recipient}. Make it {tone} and {mood}. Output format: {fmt_text}",
    "thank-you": "Write a warm thank-you note to my {recipient}. Make it {tone}. Output format: {fmt_text}",
    "complaint": "Write a {mood} complaint letter to my {recipient}. Make it {tone}. Output format: {fmt_text}",
    "apology": "Write an apology email to my {recipient}. Make it {tone}. Output format: {fmt_text}",
    "fan-mail": "Write an enthusiastic fan letter to my {recipient}. Make it {tone}. Output format: {fmt_text}",
    "hate-mail": "Write a hilariously passive-aggressive email to my {recipient}. Make it comedic and over-the-top, not actually mean. Tone: {tone}. Output format: {fmt_text}",
}

FORMAT_INSTRUCTIONS: dict[str, str] = {
    "text": "Return ONLY the email body as plain text.",
    "ascii": "Include a large ASCII art illustration at the top. Use characters like @ # % * / \\ | ( ) - + = . Make it impressive.",
    "svg": "Return an inline SVG document wrapped in ```svg ... ``` that renders the email as a decorative card, max 800x600, then the text below.",
}
