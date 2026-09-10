from __future__ import annotations

import re

from app.models.schemas import VocabularyCandidate


VOCABULARY_LIBRARY: dict[str, tuple[str, str]] = {
    "apple": ("a round fruit", "I see a red apple."),
    "astronomy": ("the scientific study of stars, planets, and space", "Astronomy helps us understand the universe."),
    "ball": ("a round toy for playing", "I can roll the ball."),
    "blue": ("the color of the sky", "The sky is blue."),
    "cat": ("a small animal that says meow", "The cat is soft."),
    "challenge": ("something difficult that needs effort", "Learning a language can be a rewarding challenge."),
    "confident": ("sure of your abilities or ideas", "She felt confident during the conversation."),
    "dog": ("an animal that can bark", "The dog is happy."),
    "fascinated": ("extremely interested in something", "I am fascinated by astronomy."),
    "happy": ("feeling good and cheerful", "I feel happy when I play."),
    "improve": ("to become better", "Daily practice can improve your speaking skills."),
    "memorable": ("worth remembering because it is special", "We had a memorable trip last summer."),
    "opportunity": ("a chance to do something", "This conversation is an opportunity to practise."),
    "play": ("to have fun with a game or toy", "I like to play outside."),
    "red": ("the color of an apple", "I see a red ball."),
    "sun": ("the bright star in our sky", "The sun is warm."),
    "thoughtful": ("showing care and attention", "That was a thoughtful answer."),
}


def extract_vocabulary(message: str, limit: int = 2) -> list[VocabularyCandidate]:
    """Return useful tracked words that occur in the learner's message."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", message.lower())
    extracted: list[VocabularyCandidate] = []
    seen: set[str] = set()
    for word in words:
        if word in seen or word not in VOCABULARY_LIBRARY:
            continue
        meaning, example_sentence = VOCABULARY_LIBRARY[word]
        extracted.append(
            VocabularyCandidate(word=word, meaning=meaning, example_sentence=example_sentence)
        )
        seen.add(word)
        if len(extracted) == limit:
            break
    return extracted