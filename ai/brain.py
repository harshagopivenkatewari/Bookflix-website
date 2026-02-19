from typing import Optional
from ai.recommender import recommend_books
from ai.llm import ask_llm
from db import get_db_connection

# GREETING TRACKER 
# ===============================
greeted_users = set()

# CATEGORY KEYWORDS (DB-ALIGNED)
# ===============================
CATEGORY_KEYWORDS = {
    "Comedy": ["comedy", "funny", "humor", "humour"],
    "Fantasy": ["fantasy", "magic"],
    "Horror": ["horror", "scary", "fear"],
    "Romance": ["romance", "romantic", "love"],
    "Science Fiction": ["sci fi", "science fiction", "scifi"],
    "Adventure": ["adventure", "journey"],
    "Mystery": ["mystery", "detective", "crime"]
}

# MOOD DETECTION
# ===============================
def detect_mood(text: str) -> Optional[str]:
    text = text.lower()
    mood_map = {
        "sad": ["sad", "lonely", "depressed", "down", "low", "upset"],
        "happy": ["happy", "excited", "joy", "cheerful"],
        "stressed": ["stressed", "tired", "burnout", "pressure", "overwhelmed"],
        "romantic": ["romantic", "crush"],
        "motivated": ["motivated", "inspire", "success", "growth"]
    }
    for mood, words in mood_map.items():
        if any(w in text for w in words):
            return mood
    return None

# CATEGORY DETECTION
# ===============================
def detect_category(text: str) -> Optional[str]:
    text = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return category
    return None

# INTENT DETECTION
# ===============================
def detect_intent(text: str) -> str:
    text = text.lower()

    if any(w in text for w in ["hi", "hello", "hey"]):
        return "greet"

    if any(w in text for w in [
        "membership", "bookflix membership", "about bookflix membership",
        "premium", "subscription", "plans"
    ]):
        return "membership"

    if any(w in text for w in [
        "fetch wishlist", "show wishlist",
        "fetch books from wishlist"
    ]):
        return "fetch_wishlist"

    if any(w in text for w in [
        "fetch cart", "show cart",
        "fetch books from cart"
    ]):
        return "fetch_cart"

    if any(w in text for w in [
        "find", "recommend", "suggest",
        "best book", "good book", "books"
    ]):
        return "recommend"

    return "chat"


# FETCH BOOK DETAILS (STRICT DB)
# ===============================
def get_book_details(book_ids: list) -> list:
    if not book_ids:
        return []

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    placeholders = ",".join(["%s"] * len(book_ids))
    cursor.execute(
        f"""
        SELECT
            b.id,
            b.title,
            b.about,
            c.name AS category
        FROM books b
        JOIN categories c ON b.category_id = c.id
        WHERE b.id IN ({placeholders})
        """,
        tuple(book_ids)
    )

    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books

# FETCH WISHLIST / CART
# ===============================
def fetch_user_wishlist(user_id: int) -> list:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT book_id FROM wishlist WHERE user_id = %s",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r["book_id"] for r in rows]

def fetch_user_cart(user_id: int) -> list:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT book_id FROM cart WHERE user_id = %s",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r["book_id"] for r in rows]

# MAIN HANDLER
# ===============================
def handle_ai_chat(message: str, user_id: int) -> dict:
    mood = detect_mood(message)
    category = detect_category(message)
    intent = detect_intent(message)

    # ---------- GREETING ----------
    if intent == "greet" and user_id not in greeted_users:
        greeted_users.add(user_id)
        return {
            "reply": (
                "Hi there\n"
                "I’m your BookFlix personal assistant.\n"
                "Tell me your mood or what kind of book you’d like to read."
            ),
            "book_ids": []
        }

    # ---------- MEMBERSHIP INFO ----------
    if "membership" in message.lower():
        return {
            "reply": (
                "**BookFlix Membership Benefits**\n\n"
                "Read books online anytime\n"
                "Download PDFs for offline reading\n"
                "Listen to audiobooks\n"
                "Get **extra 15% discount** on physical book purchases\n\n"
                "Perfect if you love reading without limits."
            ),
            "book_ids": []
        }

    # ---------- FETCH WISHLIST ----------
    if intent == "fetch_wishlist":
        book_ids = fetch_user_wishlist(user_id)
        return {
            "reply": "Here are the books from your wishlist ❤️",
            "book_ids": book_ids
        }

    # ---------- FETCH CART ----------
    if intent == "fetch_cart":
        book_ids = fetch_user_cart(user_id)
        return {
            "reply": "Here are the books in your cart 🛒",
            "book_ids": book_ids
        }

    # ---------- CATEGORY-BASED RECOMMEND ----------
    if intent == "recommend" and category:
        rec = recommend_books(category=category)
        book_ids = rec.get("book_ids", [])

        if not book_ids:
            return {
                "reply": "I couldn’t find books in that category right now.",
                "book_ids": []
            }

        books = get_book_details(book_ids)
        book_context = "\n".join(
            f"- {b['title']}: {b['about'][:100] if b['about'] else 'A great read.'}"
            for b in books
        )

        return {
            "reply": f"Here are some {category.lower()} books you might enjoy:\n{book_context}",
            "book_ids": book_ids
        }

    # ---------- MOOD-BASED RECOMMEND ----------
    if mood:
        rec = recommend_books(mood=mood)
        book_ids = rec.get("book_ids", [])

        if not book_ids:
            return {
                "reply": "I couldn’t find books right now, but I’m here with you.",
                "book_ids": []
            }

        books = get_book_details(book_ids)

        mood_intro = {
            "sad": (
                "Some days feel heavier than others, and that’s okay.\n"
                "A comforting story can make things feel a little lighter."
            ),
            "happy": (
                "It’s great that you’re feeling upbeat.\n"
                "These stories help keep that positive vibe going."
            ),
            "stressed": (
                "When life feels overwhelming, slowing down helps.\n"
                "These books are good for unwinding."
            ),
            "romantic": (
                "When emotions are in the air, stories feel deeper.\n"
                "These books lean into connection and feeling."
            ),
            "motivated": (
                "That drive you’re feeling is powerful.\n"
                "These stories match that energy."
            )
        }.get(mood, "")

        book_context = "\n".join(
            f"- {b['title']}: {b['about'][:100] if b['about'] else 'A meaningful read.'}"
            for b in books
        )

        return {
            "reply": f"{mood_intro}\n\nHere are some books for you:\n{book_context}",
            "book_ids": book_ids
        }

    # ---------- FALLBACK CHAT ----------
    return {
        "reply": ask_llm(message),
        "book_ids": []
    }
