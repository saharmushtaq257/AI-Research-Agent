"""The research crew: ONE agent, ONE task.

Flow:  topic -> agent searches DuckDuckGo -> reads best pages -> writes report
"""

import os
from datetime import datetime

from crewai import LLM, Agent, Crew, Process, Task

from tools import ReadPageTool, WebSearchTool

# Groq models that actually exist right now.
# llama-3.3-70b-versatile and llama-3.1-8b-instant were shut off on
# 2026-08-16 — do NOT use them, no matter what an old tutorial says.
AVAILABLE_MODELS = {
    "GPT-OSS 120B (best quality)": "groq/openai/gpt-oss-120b",
    "GPT-OSS 20B (fastest)": "groq/openai/gpt-oss-20b",
}
DEFAULT_MODEL = "groq/openai/gpt-oss-120b"


def build_crew(model: str = DEFAULT_MODEL, searches: int = 4) -> Crew:
    llm = LLM(
        model=model,          # LiteLLM format: groq/<the model id from Groq>
        temperature=0.3,      # low = sticks to the sources, less invention
        max_tokens=4000,
    )

    researcher = Agent(
        role="Senior Research Analyst",
        goal="Research {topic} and write an accurate, well-sourced report.",
        backstory=(
            "You have spent years turning messy web sources into clear briefings. "
            "You search broadly first, then read only the few pages that actually "
            "matter. You never invent a statistic, a quote, or a URL. When the "
            "evidence is thin or sources disagree, you say so instead of papering "
            "over it."
        ),
        tools=[WebSearchTool(), ReadPageTool()],
        llm=llm,
        max_iter=searches * 3,     # room to search, read, then write
        allow_delegation=False,    # single agent — nobody to delegate to
        verbose=True,
    )

    research_task = Task(
        description=(
            "Research this topic in depth: {topic}\n\n"
            "Today is {today}. Prefer recent sources.\n"
            "Extra instructions from the user (may be empty): {context}\n\n"
            "Do this in order:\n"
            f"1. Run about {searches} DIFFERENT web_search queries. Vary the angle: "
            "what it is, recent developments, key numbers, criticisms, who the "
            "main players are. Do not repeat the same query.\n"
            "2. Pick the 2-4 most useful URLs and read_page each one.\n"
            "3. Note where sources disagree rather than silently picking one.\n"
            "4. Then write the final report. Do not call any more tools once you "
            "start writing."
        ),
        expected_output=(
            "A markdown report of roughly 700-1000 words with these sections:\n\n"
            "# <Title>\n"
            "## Executive Summary\n"
            "3-5 bullets, takeaways only.\n"
            "## Background\n"
            "What this is and why it matters.\n"
            "## Key Findings\n"
            "3-5 subsections with real specifics: numbers, names, dates.\n"
            "## Open Questions\n"
            "Where sources conflict or evidence is weak.\n"
            "## Sources\n"
            "Numbered list of the URLs you actually opened, one line each on what "
            "it contributed.\n\n"
            "Rules: no invented statistics, no made-up URLs, no filler. "
            "Do not wrap the whole document in a code fence."
        ),
        agent=researcher,
    )

    return Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential,
        max_rpm=25,   # stays under Groq's free-tier request limit
        verbose=True,
    )


def run_research(
    topic: str,
    context: str = "",
    model: str = DEFAULT_MODEL,
    searches: int = 4,
) -> str:
    """Run the agent and return the report as a markdown string."""
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set.")

    crew = build_crew(model=model, searches=searches)
    result = crew.kickoff(
        inputs={
            "topic": topic,
            "context": context or "none",
            "today": datetime.now().strftime("%d %B %Y"),
        }
    )
    return str(result)


if __name__ == "__main__":
    # Lets you test without Streamlit:  python research_crew.py
    from dotenv import load_dotenv

    load_dotenv()
    print(run_research(input("Topic: ")))
