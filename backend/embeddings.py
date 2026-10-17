"""Summaries and embeddings for semantic search over transactions.

Each scored transaction gets a one-sentence summary written the way a person
would describe it, embedded with all-MiniLM-L6-v2 (384 numbers), and stored in
Postgres next to its risk score (pgvector).
"""
from datetime import datetime

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Sparkov category codes -> words people actually use in questions.
CATEGORY_NAMES = {
    "entertainment": "entertainment",
    "food_dining": "food and dining",
    "gas_transport": "gas and transport",
    "grocery_net": "online grocery",
    "grocery_pos": "in-store grocery",
    "health_fitness": "health and fitness",
    "home": "home",
    "kids_pets": "kids and pets",
    "misc_net": "online miscellaneous",
    "misc_pos": "in-store miscellaneous",
    "personal_care": "personal care",
    "shopping_net": "online shopping",
    "shopping_pos": "in-store shopping",
    "travel": "travel",
}

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def time_of_day(hour):
    if hour < 6:
        return "late night"
    if hour < 12:
        return "morning"
    if hour < 18:
        return "afternoon"
    return "evening"


def build_summary(txn, risk_score, risk_level, reasons):
    """One sentence describing a scored transaction.

    txn needs: merchant, category, amount, trans_time (datetime or ISO string), cc_num.
    """
    when = txn["trans_time"]
    if isinstance(when, str):
        when = datetime.fromisoformat(when)
    category = CATEGORY_NAMES.get(txn["category"], txn["category"].replace("_", " "))
    return (
        f"{risk_level.upper()} risk (score {risk_score:.2f}): "
        f"${float(txn['amount']):,.2f} {category} purchase at {txn['merchant']} "
        f"on {when:%A %d %b %Y} at {when:%H:%M} ({time_of_day(when.hour)}), "
        f"card ending {str(txn['cc_num'])[-4:]}. "
        f"Reasons: {'; '.join(reasons)}."
    )


def embed(texts):
    """Embed a list of texts. Vectors are normalised to length 1, so cosine distance
    compares meaning (direction) only."""
    vectors = get_model().encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()


def to_pgvector(vector):
    """Format a vector as pgvector's text input, e.g. '[0.1,0.2,...]', for use with ::vector."""
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"
