import re

import requests

WORDS_URL = "https://xkcd.com/simplewriter/words.js"


def fetch_words(url: str = WORDS_URL) -> list[str]:
    """Download the XKCD Simple Writer word list and return it as a list of words."""
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = "utf-8"

    match = re.search(r'__WORDS\s*=\s*"([^"]*)"', response.text)
    if not match:
        raise ValueError("Could not find __WORDS list in response")

    return [word.replace("’", "'") for word in match.group(1).split("|")]


def write_words(words: list[str], output_path: str) -> None:
    """Write the words to a file, one per line."""
    with open(output_path, "w") as f:
        f.write("\n".join(words) + "\n")


if __name__ == "__main__":
    words = sorted(set(fetch_words()))
    write_words(words, "xkcd-words.txt")
    print(f"Wrote {len(words)} words to xkcd-words.txt")
