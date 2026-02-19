import wikipedia
import mysql.connector

# ---- DB CONNECTION ----
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="bookflix"
)
cursor = conn.cursor(dictionary=True)

# ---- FETCH BOOKS WITHOUT DATA ----
cursor.execute("""
    SELECT id, title
    FROM books
    WHERE about IS NULL OR author_details IS NULL
""")
books = cursor.fetchall()

for book in books:
    book_id = book["id"]
    title = book["title"]

    print(f"Fetching: {title}")

    # --- ABOUT BOOK ---
    try:
        about = wikipedia.summary(title, sentences=10)
    except:
        about = "Description coming soon."

    # --- AUTHOR (OPTIONAL) ---
    try:
        page = wikipedia.page(title)
        author = wikipedia.summary(page.title.split(" by ")[-1], sentences=6)
    except:
        author = "Author details coming soon."

    # --- SAVE TO DB ---
    cursor.execute("""
        UPDATE books
        SET about=%s, author_details=%s
        WHERE id=%s
    """, (about, author, book_id))

    conn.commit()

cursor.close()
conn.close()
print("Done.")
