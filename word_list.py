"""
Spell Bee Word List

Organized by difficulty level with definitions and example sentences.
Each word entry contains:
- word: The word to spell
- definition: Simple definition
- sentence: Example sentence using the word
- difficulty: easy / medium / hard
"""

WORD_LIST = [
    # ─── EASY WORDS ──────────────────────────────────────────
    {
        "word": "apple",
        "definition": "A round fruit with red or green skin",
        "sentence": "She picked a ripe apple from the tree.",
        "difficulty": "easy",
    },
    {
        "word": "happy",
        "definition": "Feeling or showing pleasure and contentment",
        "sentence": "The children were happy to see the clown.",
        "difficulty": "easy",
    },
    {
        "word": "tiger",
        "definition": "A large wild cat with orange fur and black stripes",
        "sentence": "The tiger prowled silently through the jungle.",
        "difficulty": "easy",
    },
    {
        "word": "river",
        "definition": "A large natural stream of water flowing to the sea",
        "sentence": "They crossed the river using a wooden bridge.",
        "difficulty": "easy",
    },
    {
        "word": "music",
        "definition": "Vocal or instrumental sounds combined in a pleasing way",
        "sentence": "The music filled the entire concert hall.",
        "difficulty": "easy",
    },
    {
        "word": "ocean",
        "definition": "A very large expanse of sea",
        "sentence": "The ocean stretched endlessly before them.",
        "difficulty": "easy",
    },
    {
        "word": "dance",
        "definition": "To move rhythmically to music",
        "sentence": "They learned to dance the waltz together.",
        "difficulty": "easy",
    },
    {
        "word": "garden",
        "definition": "A piece of ground used for growing flowers or vegetables",
        "sentence": "She planted roses in her garden.",
        "difficulty": "easy",
    },
    {
        "word": "bridge",
        "definition": "A structure carrying a road over a river or obstacle",
        "sentence": "The old stone bridge connected the two villages.",
        "difficulty": "easy",
    },
    {
        "word": "planet",
        "definition": "A celestial body moving in orbit around a star",
        "sentence": "Earth is the third planet from the sun.",
        "difficulty": "easy",
    },
    # ─── MEDIUM WORDS ─────────────────────────────────────────
    {
        "word": "rhythm",
        "definition": "A strong regular repeated pattern of movement or sound",
        "sentence": "The drummer kept a steady rhythm throughout the song.",
        "difficulty": "medium",
    },
    {
        "word": "calendar",
        "definition": "A chart showing the days, weeks, and months of a year",
        "sentence": "She marked the important dates on her calendar.",
        "difficulty": "medium",
    },
    {
        "word": "necessary",
        "definition": "Required to be done; essential",
        "sentence": "It is necessary to wear a seatbelt while driving.",
        "difficulty": "medium",
    },
    {
        "word": "separate",
        "definition": "To cause to move or be apart",
        "sentence": "Please separate the colored clothes from the whites.",
        "difficulty": "medium",
    },
    {
        "word": "library",
        "definition": "A building or room containing collections of books",
        "sentence": "She spent every Saturday afternoon at the library.",
        "difficulty": "medium",
    },
    {
        "word": "beautiful",
        "definition": "Pleasing to the senses or mind aesthetically",
        "sentence": "The sunset over the mountains was beautiful.",
        "difficulty": "medium",
    },
    {
        "word": "February",
        "definition": "The second month of the year",
        "sentence": "February is the shortest month of the year.",
        "difficulty": "medium",
    },
    {
        "word": "surprise",
        "definition": "An unexpected event or thing",
        "sentence": "The birthday party was a complete surprise.",
        "difficulty": "medium",
    },
    {
        "word": "knowledge",
        "definition": "Facts, information, and skills acquired through experience",
        "sentence": "Knowledge is the key to solving complex problems.",
        "difficulty": "medium",
    },
    {
        "word": "Wednesday",
        "definition": "The day of the week after Tuesday",
        "sentence": "Our team meeting is scheduled for Wednesday.",
        "difficulty": "medium",
    },
    # ─── HARD WORDS ───────────────────────────────────────────
    {
        "word": "accommodate",
        "definition": "To provide lodging or sufficient space for",
        "sentence": "The hotel can accommodate up to five hundred guests.",
        "difficulty": "hard",
    },
    {
        "word": "bureaucracy",
        "definition": "A system of government with many complicated rules",
        "sentence": "The bureaucracy made the approval process very slow.",
        "difficulty": "hard",
    },
    {
        "word": "conscientious",
        "definition": "Wishing to do what is right; thorough and careful",
        "sentence": "She is a conscientious worker who never misses a deadline.",
        "difficulty": "hard",
    },
    {
        "word": "mischievous",
        "definition": "Causing or showing a fondness for causing trouble playfully",
        "sentence": "The mischievous kitten knocked over the vase.",
        "difficulty": "hard",
    },
    {
        "word": "onomatopoeia",
        "definition": "The formation of a word from a sound associated with it",
        "sentence": "Buzz and hiss are examples of onomatopoeia.",
        "difficulty": "hard",
    },
    {
        "word": "entrepreneur",
        "definition": "A person who sets up a business taking on financial risks",
        "sentence": "The young entrepreneur launched a successful startup.",
        "difficulty": "hard",
    },
    {
        "word": "pharmaceutical",
        "definition": "Relating to the preparation and dispensing of medicines",
        "sentence": "The pharmaceutical company developed a new vaccine.",
        "difficulty": "hard",
    },
    {
        "word": "acquaintance",
        "definition": "A person one knows slightly but is not a close friend",
        "sentence": "He is merely an acquaintance, not a close friend.",
        "difficulty": "hard",
    },
    {
        "word": "surveillance",
        "definition": "Close observation, especially of a suspected person",
        "sentence": "The police kept the suspect under constant surveillance.",
        "difficulty": "hard",
    },
    {
        "word": "questionnaire",
        "definition": "A set of printed questions used for a survey",
        "sentence": "Please fill out this questionnaire about your experience.",
        "difficulty": "hard",
    },
]


def get_words_by_difficulty(difficulty: str) -> list:
    """Get all words of a specific difficulty level."""
    return [w for w in WORD_LIST if w["difficulty"] == difficulty]


def get_all_words() -> list:
    """Get all words from the word list."""
    return WORD_LIST
