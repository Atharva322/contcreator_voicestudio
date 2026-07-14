import re


URL_PATTERN = re.compile(r"https?://\S+")
SPACE_PATTERN = re.compile(r"\s+")


def normalize_post_text(text: str) -> str:
    cleaned = text.replace("\r", "\n").strip()
    cleaned = SPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()


def dedupe_posts(existing_texts: set[str], incoming_texts: list[str]) -> tuple[list[str], int]:
    accepted: list[str] = []
    seen = {fingerprint_text(text) for text in existing_texts}
    skipped = 0

    for text in incoming_texts:
        normalized = normalize_post_text(text)
        fingerprint = fingerprint_text(normalized)
        if not normalized or fingerprint in seen:
            skipped += 1
            continue
        seen.add(fingerprint)
        accepted.append(normalized)

    return accepted, skipped


def fingerprint_text(text: str) -> str:
    without_urls = URL_PATTERN.sub("", text.lower())
    return SPACE_PATTERN.sub(" ", without_urls).strip()
