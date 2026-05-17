"""
llm.py
------
Takes a user query + retrieved fund chunks and generates a
structured, comparative answer using LLaMA 3 via Groq API.
English only. Outputs structured markdown with tables.

Standalone test:
    python rag/llm.py
"""

import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from retriever import retrieve

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a precise mutual fund data analyst for Indian retail investors.

You will receive data about Large Cap mutual funds and a user question.
Your job is to answer in a structured, easy-to-read format using markdown.

STRICT RULES:
- Always respond in English only
- Always include a comparison table when multiple funds are involved
- Use this exact table format:

| Fund Name | 1Y Return | 3Y Return | 5Y Return | Sharpe | Sortino | Assessment |
|-----------|-----------|-----------|-----------|--------|---------|------------|
| Fund A    | x%        | x%        | x%        | x      | x       | Good/Avg   |

- After the table, add a short "Key Takeaway" section (2-3 lines max)
- If only one fund is asked about, still show a single-row table for clarity
- Never make up numbers — only use what is in the context
- End every response with: > ⚠️ Past performance does not guarantee future returns. This is not financial advice.
- Keep the total response under 300 words"""


def build_context(hits: list[dict]) -> str:
    context_parts = []
    for i, hit in enumerate(hits, 1):
        context_parts.append(f"--- Fund {i} ---\n{hit['chunk_text']}")
    return "\n\n".join(context_parts)


def ask(query: str, top_k: int = 5) -> dict:
    hits    = retrieve(query, top_k=top_k)
    context = build_context(hits)

    user_message = f"""Here is data about relevant mutual funds:

{context}

User question: {query}

Respond with a markdown table comparing the relevant funds, followed by a Key Takeaway."""

    client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,
        max_tokens  = 600,
    )

    answer     = response.choices[0].message.content
    funds_used = [h["fund_name"] for h in hits]

    return {
        "query"      : query,
        "answer"     : answer,
        "funds_used" : funds_used,
    }


if __name__ == "__main__":
    test_queries = [
        "Which large cap fund gave the best 3 year returns?",
        "Compare SBI and HDFC large cap fund",
        "Which fund has the best risk adjusted returns?",
    ]

    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print(f"{'='*60}")
        result = ask(q)
        print(result["answer"])
