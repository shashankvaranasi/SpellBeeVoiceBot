"""
Spell Bee Game Processor

Manages game state and provides function handlers for LLM-driven game flow.
The LLM (Gemini) calls these functions to interact with the game state,
and RTVIServerMessageFrames are pushed to update the frontend UI.
"""

import random
from loguru import logger

from word_list import WORD_LIST, get_words_by_difficulty


class SpellBeeGame:
    """Manages the state of a single Spell Bee game session."""

    def __init__(self):
        self.score = 0
        self.total_words = 0
        self.correct_count = 0
        self.incorrect_count = 0
        self.current_word = None
        self.current_word_info = None
        self.word_history = []
        self.used_words = set()
        self.difficulty = "medium"  # Start with medium
        self.game_active = True
        self.max_words = 10  # Game ends after 10 words

        # Build shuffled word pool
        self._word_pool = list(WORD_LIST)
        random.shuffle(self._word_pool)
        self._pool_index = 0

        logger.info("SpellBeeGame initialized")

    def get_next_word(self) -> dict:
        """Get the next word from the pool."""
        if self._pool_index >= len(self._word_pool):
            # Reshuffle if we run out
            random.shuffle(self._word_pool)
            self._pool_index = 0

        word_info = self._word_pool[self._pool_index]
        self._pool_index += 1

        # Skip already used words
        while word_info["word"] in self.used_words and self._pool_index < len(
            self._word_pool
        ):
            word_info = self._word_pool[self._pool_index]
            self._pool_index += 1

        self.current_word = word_info["word"].upper()
        self.current_word_info = word_info
        self.used_words.add(word_info["word"])
        self.total_words += 1

        logger.info(f"New word #{self.total_words}: {self.current_word}")

        return word_info

    def check_spelling(self, user_spelling: str) -> dict:
        """
        Check the user's spelling against the current word.

        Args:
            user_spelling: The letters the user spelled out

        Returns:
            dict with 'correct', 'expected', 'given', 'score' fields
        """
        if not self.current_word:
            return {"error": "No word is currently active"}

        # Normalize: remove spaces, dashes, dots, and convert to uppercase
        cleaned = (
            user_spelling.upper()
            .replace(" ", "")
            .replace("-", "")
            .replace(".", "")
            .replace(",", "")
        )

        is_correct = cleaned == self.current_word

        if is_correct:
            self.correct_count += 1
            self.score += 10
        else:
            self.incorrect_count += 1

        result = {
            "correct": is_correct,
            "expected": self.current_word,
            "given": cleaned,
            "word": self.current_word_info["word"],
            "score": self.score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "total_words": self.total_words,
        }

        self.word_history.append(
            {
                "word": self.current_word_info["word"],
                "correct": is_correct,
                "user_answer": cleaned,
            }
        )

        logger.info(
            f"Spelling check: expected={self.current_word}, "
            f"got={cleaned}, correct={is_correct}"
        )

        return result

    def get_game_state(self) -> dict:
        """
        Gathers all relevant game data to send to the Browser.
        This dictionary is what turns into the JSON updates for the UI.
        """
        return {
            "type": "game_state",
            "score": self.score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "total_words": self.total_words,
            "max_words": self.max_words,
            "current_word": self.current_word_info["word"]
            if self.current_word_info
            else None,
            "difficulty": self.current_word_info["difficulty"]
            if self.current_word_info
            else None,
            "game_active": self.game_active,
            "word_history": self.word_history,
        }

    def end_game(self) -> dict:
        """End the game and return final summary."""
        self.game_active = False

        percentage = (
            (self.correct_count / self.total_words * 100) if self.total_words > 0 else 0
        )

        summary = {
            "type": "game_over",
            "final_score": self.score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "total_words": self.total_words,
            "percentage": round(percentage, 1),
            "word_history": self.word_history,
        }

        logger.info(
            f"Game ended: {self.correct_count}/{self.total_words} correct ({percentage:.1f}%)"
        )

        return summary


# ─── LLM Function Tool Definitions ──────────────────────────
# These are registered with the Gemini LLM service for function calling

SPELL_BEE_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "present_new_word",
                "description": (
                    "Present the next word in the spell bee game. Call this to get a new word "
                    "to present to the user. The function returns the word, its definition, and "
                    "an example sentence. You should then say the word clearly, provide the "
                    "definition, use it in a sentence, and then say the word again. "
                    "Spell out each letter clearly for the user to hear."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "check_user_spelling",
                "description": (
                    "Check if the user's spelling of the current word is correct. "
                    "Call this after the user has finished spelling out the letters. "
                    "Extract the individual letters the user said and concatenate them "
                    "into a single string (e.g., if user said 'A P P L E', pass 'APPLE'). "
                    "Ignore any filler words like 'um', 'uh', etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "spelling": {
                            "type": "string",
                            "description": (
                                "The letters the user spelled, concatenated into a single string. "
                                "For example, if the user said 'R H Y T H M', pass 'RHYTHM'."
                            ),
                        },
                    },
                    "required": ["spelling"],
                },
            },
            {
                "name": "get_current_score",
                "description": (
                    "Get the current game score and statistics. "
                    "Call this when the user asks about their score or progress."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "end_spell_bee_game",
                "description": (
                    "End the spell bee game and get the final summary. "
                    "Call this when the user wants to stop playing, or after the "
                    "maximum number of words has been reached."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]
    }
]
