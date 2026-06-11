import os
import re

_WORD_RE = re.compile(r"[a-zA-Z']+")
_CURLY_QUOTES = str.maketrans("‘’", "''")


def check_words_in_corpus(text: str) -> dict:
    """Check whether every word in a piece of text appears in the allowed word corpus.

    The corpus is loaded from the file path given by the WORD_CORPUS_PATH
    environment variable. The file should contain one word per line.

    Args:
        text (str): The text to check, e.g. a draft explanation.
    """
    corpus_path = os.environ["WORD_CORPUS_PATH"]
    with open(corpus_path) as f:
        corpus = {line.strip().lower() for line in f if line.strip()}

    text = text.translate(_CURLY_QUOTES)
    words = (w.lower().strip("'") for w in _WORD_RE.findall(text))
    words_not_in_corpus = sorted({w for w in words if w and w not in corpus})

    return {
        "all_words_in_corpus": len(words_not_in_corpus) == 0,
        "words_not_in_corpus": words_not_in_corpus,
    }
