import os

from openai import OpenAI


def generate_mock_llm_answer(
    question: str,
    context_chunks: list[str],
) -> str:
    if not context_chunks:
        return "I could not find enough context to answer this question."

    combined_context = "\n".join(context_chunks).lower()

    answer_parts = []

    if "renewal" in combined_context:
        answer_parts.append(
            "The customer has a renewal-related risk because the renewal date is close."
        )

    if "support" in combined_context:
        answer_parts.append(
            "There are support concerns because the customer had multiple support issues or open support tickets."
        )

    if "response times" in combined_context:
        answer_parts.append(
            "The customer also expects faster response times, which may impact satisfaction."
        )

    if "onboarding" in combined_context:
        answer_parts.append(
            "The customer asked for better onboarding documentation."
        )

    if not answer_parts:
        answer_parts.append(
            "The retrieved context contains relevant information, but no specific risk pattern was detected by the mock LLM."
        )

    recommendation = (
        "Recommended next action: the account manager should contact the customer before renewal, "
        "review open support tickets, and prepare a clear follow-up plan."
    )

    return " ".join(answer_parts) + " " + recommendation


def generate_openai_llm_answer(
    question: str,
    context_chunks: list[str],
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "OpenAI is not configured, so a local fallback answer was generated. "
            + generate_mock_llm_answer(
                question=question,
                context_chunks=context_chunks,
            )
        )

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key)

    context = "\n\n".join(
        [
            f"Chunk {index + 1}:\n{chunk}"
            for index, chunk in enumerate(context_chunks)
        ]
    )

    prompt = f"""
You are an AI assistant for a Smart RAG platform.

Answer the user's question using ONLY the provided context chunks.

Rules:
- If the answer is not in the context, say you do not have enough information.
- Be concise.
- Mention risks and recommended next actions when relevant.
- Do not invent facts.

Context:
{context}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You answer CRM/customer risk questions using retrieved RAG context.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content or ""

    except Exception:
        return (
            "[OPENAI FALLBACK - MOCK USED] "
            "OpenAI is currently unavailable, so a local fallback answer was generated. "
            + generate_mock_llm_answer(
                question=question,
                context_chunks=context_chunks,
            )
        )


def generate_llm_answer(
    question: str,
    context_chunks: list[str],
) -> str:
    use_openai = os.getenv("USE_OPENAI_LLM", "false").lower() == "true"

    if use_openai:
        return generate_openai_llm_answer(
            question=question,
            context_chunks=context_chunks,
        )

    return generate_mock_llm_answer(
        question=question,
        context_chunks=context_chunks,
    )


def get_llm_status() -> dict:
    use_openai = os.getenv("USE_OPENAI_LLM", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if use_openai and api_key:
        return {
            "provider": "openai",
            "model": model,
            "enabled": True,
            "api_key_configured": True,
        }

    if use_openai and not api_key:
        return {
            "provider": "mock",
            "model": "mock-llm",
            "enabled": False,
            "api_key_configured": False,
            "reason": "USE_OPENAI_LLM is true but OPENAI_API_KEY is missing",
        }

    return {
        "provider": "mock",
        "model": "mock-llm",
        "enabled": True,
        "api_key_configured": bool(api_key),
        "reason": "USE_OPENAI_LLM is false",
    }