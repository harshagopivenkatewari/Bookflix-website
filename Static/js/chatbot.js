
function toggleChatbot(){
  const pageLayout = document.getElementById("pageLayout");
  if (!pageLayout) return;

  pageLayout.classList.toggle("chat-open");
}

/* ================= CHAT MESSAGE ================= */
function appendMessage(text, sender){
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const msg = document.createElement("div");

  msg.style.margin = "8px 0";
  msg.style.padding = "10px";
  msg.style.borderRadius = "8px";
  msg.style.maxWidth = "85%";
  msg.style.wordWrap = "break-word";

  if (sender === "user") {
    msg.style.background = "#7c3aed";
    msg.style.marginLeft = "auto";
    msg.innerText = text;
  } else {
    msg.style.background = "#2a2a2a";
    msg.innerText = text;
  }

  chatBody.appendChild(msg);
  chatBody.scrollTop = chatBody.scrollHeight;
}

/* ================= BOOK TILES ================= */
function appendBookTiles(books){
  const chatBody = document.getElementById("chatBody");
  if (!chatBody || !Array.isArray(books)) return;

  const wrapper = document.createElement("div");
  wrapper.style.display = "grid";
  wrapper.style.gridTemplateColumns = "repeat(auto-fill, minmax(120px, 1fr))";
  wrapper.style.gap = "12px";
  wrapper.style.marginTop = "12px";

  books.forEach(book => {
    const card = document.createElement("div");
    card.style.background = "#1e1e1e";
    card.style.borderRadius = "10px";
    card.style.padding = "8px";
    card.style.cursor = "pointer";
    card.style.textAlign = "center";
    card.style.transition = "0.2s";

    card.onmouseenter = () => card.style.transform = "scale(1.05)";
    card.onmouseleave = () => card.style.transform = "scale(1)";

    card.onclick = () => {
      window.location.href = `/book-details?book_id=${book.id}`;
    };

    const img = document.createElement("img");
    img.src = `/static/${book.image_path}`;
    img.style.width = "100%";
    img.style.height = "160px";
    img.style.objectFit = "cover";
    img.style.borderRadius = "8px";

    const title = document.createElement("div");
    title.innerText = book.title;
    title.style.fontSize = "13px";
    title.style.marginTop = "6px";
    title.style.color = "#ddd";

    card.appendChild(img);
    card.appendChild(title);
    wrapper.appendChild(card);
  });

  chatBody.appendChild(wrapper);
  chatBody.scrollTop = chatBody.scrollHeight;
}

/* ================= SEND CHAT ================= */
function sendChat(){
  const input = document.getElementById("chatInput");
  const chatBody = document.getElementById("chatBody");
  if (!input || !chatBody) return;

  const message = input.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  input.value = "";

  fetch("/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  })
  .then(res => res.json())
  .then(data => {
    appendMessage(data.reply || "🤖 I didn’t understand that.", "bot");

    if (data.book_ids && data.book_ids.length > 0) {
      fetch("/api/books/by-ids", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: data.book_ids })
      })
      .then(res => res.json())
      .then(books => {
        appendBookTiles(books);
      });
    }
  })
  .catch(() => {
    appendMessage("⚠️ Something went wrong.", "bot");
  });
}

/* ================= ENTER KEY ================= */
document.addEventListener("keydown", function(e){
  if (e.key === "Enter") {
    const active = document.activeElement;
    if (active && active.id === "chatInput") {
      sendChat();
    }
  }
});
