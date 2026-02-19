from db import get_db_connection
import random

# ===============================
# CONFIG
# ===============================
MAX_BOOKS = 5

# Mood → Category fallback mapping
# Used ONLY when user does NOT specify category
MOOD_CATEGORY_MAP = {
    "sad": ["Fantasy", "Comedy", "Adventure"],
    "stressed": ["Fantasy", "Comedy"],
    "happy": ["Comedy", "Adventure"],
    "romantic": ["Romance", "Love Story"],
    "motivated": ["Popular", "Adventure"],
    "neutral": []
}


# ===============================
# CORE RECOMMENDER
# ===============================
def recommend_books(mood: str = "neutral", category: str = None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    books = []

    try:
        # ===============================
        # 1️⃣ CATEGORY OVERRIDE (HIGHEST PRIORITY)
        # ===============================
        if category:
            cursor.execute(
                """
                SELECT b.id
                FROM books b
                JOIN categories c ON b.category_id = c.id
                WHERE c.name = %s
                ORDER BY RAND()
                LIMIT %s
                """,
                (category, MAX_BOOKS)
            )
            books = cursor.fetchall()

        # ===============================
        # 2️⃣ MOOD-BASED SELECTION (ONLY IF NO CATEGORY)
        # ===============================
        if not books:
            categories = MOOD_CATEGORY_MAP.get(mood, [])

            if categories:
                placeholders = ",".join(["%s"] * len(categories))
                cursor.execute(
                    f"""
                    SELECT b.id
                    FROM books b
                    JOIN categories c ON b.category_id = c.id
                    WHERE c.name IN ({placeholders})
                    ORDER BY RAND()
                    LIMIT %s
                    """,
                    (*categories, MAX_BOOKS)
                )
                books = cursor.fetchall()

        # ===============================
        # 3️⃣ FINAL FALLBACK (ANY BOOKS)
        # ===============================
        if not books:
            cursor.execute(
                """
                SELECT id
                FROM books
                ORDER BY RAND()
                LIMIT %s
                """,
                (MAX_BOOKS,)
            )
            books = cursor.fetchall()

    except Exception:
        books = []

    finally:
        cursor.close()
        conn.close()

    # ===============================
    # FINAL SAFETY
    # ===============================
    if not books:
        return {"book_ids": []}

    # Ensure max 5 (extra safety)
    selected = random.sample(books, min(MAX_BOOKS, len(books)))

    return {
        "book_ids": [b["id"] for b in selected]
    }
