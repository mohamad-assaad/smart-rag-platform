import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "do",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
}


IMPORTANT_TERMS = {
    "renewal": 3,
    "risk": 3,
    "risks": 3,
    "support": 3,
    "tickets": 2,
    "customer": 2,
    "account": 2,
    "manager": 2,
    "response": 2,
    "onboarding": 2,
    "documentation": 2,
    "plan": 2,
    "action": 2,
    "actions": 2,
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize_text(text: str) -> list[str]:
    normalized_text = normalize_text(text)

    words = normalized_text.split()

    return [
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 2
    ]


def calculate_keyword_score(
    question: str,
    chunk_content: str,
) -> int:
    question_words = tokenize_text(question)
    chunk_words = tokenize_text(chunk_content)
    chunk_text = " ".join(chunk_words)

    score = 0

    for word in question_words:
        if word in chunk_words:
            score += IMPORTANT_TERMS.get(word, 1)

        elif word in chunk_text:
            score += 1

    return score