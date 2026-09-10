from __future__ import annotations

from app.models.schemas import PracticeSuggestion, VocabularyItem


def build_practice_suggestions(words: list[VocabularyItem]) -> list[PracticeSuggestion]:
    """Create short, actionable prompts from the learner's saved vocabulary."""
    if not words:
        return [
            PracticeSuggestion(
                word="first word",
                focus="Start a collection",
                prompt="Say one fun word with your grown-up and it will appear here.",
            )
        ]
    action_prompts = {
        "red": "Can you find something red and say, 'I see red!'?",
        "blue": "Can you point to something blue?",
        "cat": "Can you make a cat sound and say, 'A cat!'?",
        "dog": "Can you make a dog sound and say, 'A dog!'?",
        "ball": "Can you roll a ball and say, 'Roll the ball!'?",
        "apple": "Can you pretend to take a bite and say, 'An apple!'?",
        "happy": "Can you make a happy face and say, 'I am happy!'?",
        "play": "Can you choose a toy and say, 'I play!'?",
    }
    suggestions: list[PracticeSuggestion] = []
    for word in words[:3]:
        suggestions.append(
            PracticeSuggestion(
                word=word.word,
                focus="Say and show it",
                prompt=action_prompts.get(word.word, f"Say '{word.word}' and show me something about it."),
            )
        )
    return suggestions