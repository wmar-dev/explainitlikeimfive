import pytest

from tools import check_words_in_corpus


@pytest.fixture
def corpus_path(tmp_path, monkeypatch):
    path = tmp_path / "corpus.txt"
    path.write_text("a\ndon't\nfun\nis\nit\nlight\nno\nof\nsimple\ntiny\nworry\n")
    monkeypatch.setenv("WORD_CORPUS_PATH", str(path))
    return path


def test_all_words_in_corpus(corpus_path):
    result = check_words_in_corpus("A tiny light is simple.")
    assert result == {"all_words_in_corpus": True, "words_not_in_corpus": []}


def test_reports_missing_words(corpus_path):
    result = check_words_in_corpus("A photon is a tiny particle of light.")
    assert result == {
        "all_words_in_corpus": False,
        "words_not_in_corpus": ["particle", "photon"],
    }


def test_is_case_insensitive(corpus_path):
    result = check_words_in_corpus("A TINY Light")
    assert result == {"all_words_in_corpus": True, "words_not_in_corpus": []}


def test_strips_surrounding_punctuation(corpus_path):
    result = check_words_in_corpus("Is it fun? Tiny is great!")
    assert result == {"all_words_in_corpus": False, "words_not_in_corpus": ["great"]}


def test_strips_leading_and_trailing_apostrophes(corpus_path):
    result = check_words_in_corpus("'tiny' is fun")
    assert result == {"all_words_in_corpus": True, "words_not_in_corpus": []}


def test_contraction_with_straight_apostrophe(corpus_path):
    result = check_words_in_corpus("Don't worry, it is tiny.")
    assert result == {"all_words_in_corpus": True, "words_not_in_corpus": []}


def test_contraction_with_curly_apostrophe(corpus_path):
    result = check_words_in_corpus("Don’t worry, it is tiny.")
    assert result == {"all_words_in_corpus": True, "words_not_in_corpus": []}


def test_missing_words_are_deduped_and_sorted(corpus_path):
    result = check_words_in_corpus("photon photon zebra apple")
    assert result["words_not_in_corpus"] == ["apple", "photon", "zebra"]


def test_raises_when_corpus_path_not_set(monkeypatch):
    monkeypatch.delenv("WORD_CORPUS_PATH", raising=False)
    with pytest.raises(KeyError):
        check_words_in_corpus("hello")
