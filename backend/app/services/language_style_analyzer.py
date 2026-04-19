"""
Language Style Analyzer — Extract linguistic features from user messages.

Analyzes user messages to learn their communication style over time:
- Formality level (casual vs formal)
- Emoji usage frequency
- Sentence complexity
- Vocabulary preference (standard, religious, modern)
- Common phrases

Uses exponential moving average to gradually adapt to user's style.
"""
import re
from typing import Dict
from collections import Counter


# ──────────────────────────────────────────
# Linguistic feature extraction
# ──────────────────────────────────────────


def analyze_formality(message: str) -> float:
    """
    Analyze formality level: 0 = very casual, 1 = very formal.

    Indicators:
    - Formal greetings: "selamünaleyküm", "merhaba efendim"
    - Casual greetings: "slm", "mrb", "naber", "selam"
    - Formal language: "sizin", "buyurun", "lütfen", "saygılarımla"
    - Casual language: "ya", "yaa", "abi", "kanka", "lan"
    """
    lower = message.lower()

    formal_score = 0
    casual_score = 0

    # Formal indicators
    formal_words = [
        "selamünaleyküm", "merhaba efendim", "saygılarımla",
        "rica ederim", "lütfen", "buyurun", "sizinle",
        "müsaadenizle", "izninizle",
    ]
    for word in formal_words:
        if word in lower:
            formal_score += 2

    # Casual indicators
    casual_words = [
        "slm", "mrb", "selam", "naber", "nasılsın",
        "ya", "yaa", "abi", "abla", "kanka", "knk",
        "bişey", "nolur", "noluyor", "napıyorsun",
    ]
    for word in casual_words:
        if word in lower:
            casual_score += 2

    # Shorthand/slang
    if re.search(r'\b(bi|bişi|nası|niye|neden|bi de)\b', lower):
        casual_score += 1

    # Formal punctuation (question mark, proper capitalization)
    if message[0].isupper() if message else False:
        formal_score += 0.5

    total = formal_score + casual_score
    if total == 0:
        return 0.5  # Neutral

    return formal_score / total


def count_emojis(message: str) -> int:
    """Count emoji characters in message."""
    # Unicode emoji ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(message)
    return len(emojis)


def calculate_avg_sentence_length(message: str) -> float:
    """
    Calculate average sentence length in words.
    0-1 scale: 0 = very short, 1 = very long.
    """
    # Split by sentence delimiters
    sentences = re.split(r'[.!?\n]+', message)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 0.5

    total_words = sum(len(s.split()) for s in sentences)
    avg_words = total_words / len(sentences)

    # Normalize: 1-5 words = 0, 20+ words = 1
    normalized = min((avg_words - 1) / 19, 1.0)
    return max(normalized, 0.0)


def detect_religious_vocabulary(message: str) -> int:
    """Count religious/spiritual terms in message."""
    lower = message.lower()

    religious_terms = [
        "inşallah", "inşaallah", "maşallah", "maşaallah",
        "elhamdülillah", "hamdolsun", "bismillah",
        "allah", "rabbim", "peygamber", "namaz", "dua",
        "kur'an", "kuran", "sure", "ayet", "hadis",
        "cennet", "cehennem", "günah", "sevap", "takva",
        "şükür", "sabır", "tevbe", "niyaz", "münacaat",
    ]

    count = sum(1 for term in religious_terms if term in lower)
    return count


def detect_informal_speech(message: str) -> bool:
    """Detect informal/slang speech patterns."""
    lower = message.lower()

    informal_patterns = [
        r'\bbişey\b', r'\bnolur\b', r'\nnaber\b',
        r'\bknk\b', r'\byaa\b', r'\blaan\b',
        r'\baq\b', r'\baq\b', r'\bvalla\b',
        r'\bbi de\b', r'\bnası\b', r'\bniye\b',
    ]

    for pattern in informal_patterns:
        if re.search(pattern, lower):
            return True

    return False


def extract_frequent_words(message: str) -> list:
    """Extract most common non-trivial words (for common_phrases)."""
    # Remove punctuation and lowercase
    words = re.findall(r'\b\w+\b', message.lower())

    # Filter out stopwords
    stopwords = {
        "bir", "bu", "şu", "o", "ve", "veya", "ama", "fakat",
        "çok", "çünkü", "için", "gibi", "kadar", "da", "de",
        "mi", "mı", "mu", "mü", "ne", "nasıl", "neden",
    }

    meaningful_words = [w for w in words if w not in stopwords and len(w) > 3]

    # Count frequency
    counter = Counter(meaningful_words)
    return [word for word, count in counter.most_common(5)]


# ──────────────────────────────────────────
# Style update with exponential moving average
# ──────────────────────────────────────────


def extract_language_features(user_message: str, current_style: dict) -> dict:
    """
    Extract linguistic features from user message.
    Updates current_style using exponential moving average (EMA).

    EMA formula: new_value = 0.9 * old_value + 0.1 * observed_value
    This gives 90% weight to history, 10% to new observation.
    """
    # Extract features from current message
    formality = analyze_formality(user_message)
    emoji_count = count_emojis(user_message)
    avg_sentence_len = calculate_avg_sentence_length(user_message)
    religious_count = detect_religious_vocabulary(user_message)
    is_informal = detect_informal_speech(user_message)

    # Determine vocabulary preference
    vocab_pref = current_style.get("vocabulary_preference", "standard")
    if religious_count >= 2:
        vocab_pref = "religious"
    elif is_informal:
        vocab_pref = "modern"

    # Update with exponential moving average
    updated_style = {
        "formality_level": 0.9 * current_style.get("formality_level", 0.5) + 0.1 * formality,
        "emoji_usage": 0.9 * current_style.get("emoji_usage", 0.0) + 0.1 * (1.0 if emoji_count > 0 else 0.0),
        "sentence_complexity": 0.9 * current_style.get("sentence_complexity", 0.6) + 0.1 * avg_sentence_len,
        "vocabulary_preference": vocab_pref,
        "common_phrases": current_style.get("common_phrases", []),  # Updated separately
        "address_style": current_style.get("address_style", "sen"),  # Detected from "siz" usage
        "response_length_pref": current_style.get("response_length_pref", "medium"),
        "last_updated": None,  # Will be set by caller with datetime
    }

    # Detect address style (sen vs siz)
    if any(word in user_message.lower() for word in ["sizin", "sizi", "size", "siz"]):
        updated_style["address_style"] = "siz"

    # Update common phrases (keep top 10)
    frequent_words = extract_frequent_words(user_message)
    existing_phrases = current_style.get("common_phrases", [])
    combined = existing_phrases + frequent_words
    # Count and keep top 10
    phrase_counter = Counter(combined)
    updated_style["common_phrases"] = [word for word, _ in phrase_counter.most_common(10)]

    return updated_style


# ──────────────────────────────────────────
# Tone evolution based on relationship duration
# ──────────────────────────────────────────


def evolve_conversational_tone(
    interaction_count: int,
    relationship_duration_days: int,
) -> str:
    """
    Evolve conversational tone based on interaction history.

    Tone progression:
    - Day 1-5 interactions: polite_formal
    - Day 6-20 interactions: warm_friendly
    - Day 21+ interactions OR 30+ days: empathetic_guide
    - 30+ days relationship: spiritual_companion
    """
    if relationship_duration_days >= 30:
        return "spiritual_companion"
    elif interaction_count >= 20:
        return "empathetic_guide"
    elif interaction_count >= 5:
        return "warm_friendly"
    else:
        return "polite_formal"


def get_tone_instruction(tone: str) -> str:
    """
    Get AI prompt instruction for a given tone.
    Used in conversation orchestration prompts.
    """
    tone_map = {
        "polite_formal": "Saygılı ve dikkatli ol. 'Sizi dinliyorum', 'Size yardımcı olmak isterim' gibi ifadeler kullan.",
        "warm_friendly": "Samimi ve dostane ol. 'Seni dinliyorum', 'Nasılsın bugün?' gibi samimi ifadeler kullan.",
        "empathetic_guide": "Şefkatli ve anlayışlı bir rehber gibi ol. 'Anlıyorum, bu gerçekten zor', 'Seninle bu yolculuktayım' gibi empatik ifadeler kullan.",
        "spiritual_companion": "Manevi bir dost/kardeş gibi ol. 'Kardeşim', 'Yine buradayız', 'Birlikte devam edelim inşaAllah' gibi yakın ifadeler kullan.",
    }
    return tone_map.get(tone, "Samimi ama saygılı ol.")
