let currentUser = "";
let refreshTimer = null;
let presenceTimer = null;
let selectedColor = "rosa";
let lastMessageCount = 0;

const loginScreen = document.getElementById("loginScreen");
const chatContainer = document.getElementById("chatContainer");
const loginBtn = document.getElementById("loginBtn");
const passwordInput = document.getElementById("passwordInput");
const loginError = document.getElementById("loginError");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const chatBody = document.getElementById("chatBody");
const typingIndicator = document.getElementById("typingIndicator");

for (const option of document.querySelectorAll(".color-option")) {
    option.addEventListener("click", () => {
        selectedColor = option.dataset.color;
        document.querySelectorAll(".color-option").forEach((item) => {
            const active = item === option;
            item.classList.toggle("selected", active);
            item.setAttribute("aria-pressed", String(active));
        });
    });
}

async function login() {
    loginBtn.disabled = true;
    loginError.textContent = "";
    try {
        const res = await fetch("/api/login", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ color: selectedColor, password: passwordInput.value })
        });
        const data = await res.json();
        if (!res.ok || data.status !== "success") {
            loginError.textContent = data.message || "No fue posible iniciar sesión.";
            return;
        }
        currentUser = data.user;
        loginScreen.classList.add("hidden");
        chatContainer.classList.remove("hidden");
        document.getElementById("youBadge").textContent = data.label.toUpperCase();
        chatContainer.classList.add(currentUser === "rosa" ? "user-rosa" : "user-azul");
        await refreshChat();
        await updatePresence(false);
        refreshTimer = setInterval(refreshChat, 1800);
        presenceTimer = setInterval(() => updatePresence(Boolean(messageInput.value.trim())), 4000);
        messageInput.focus();
    } catch (error) {
        loginError.textContent = "Error al conectar con el servidor.";
    } finally { loginBtn.disabled = false; }
}

async function refreshChat() {
    try {
        const [messagesRes, statusRes] = await Promise.all([fetch("/api/messages"), fetch("/api/status")]);
        if (!messagesRes.ok || !statusRes.ok) throw new Error("Error de actualización");
        const [messages, statuses] = await Promise.all([messagesRes.json(), statusRes.json()]);
        renderMessages(messages);
        const otherUser = currentUser === "rosa" ? "azul" : "rosa";
        const other = statuses[otherUser];
        const active = Boolean(other && other.active);
        document.getElementById("statusText").textContent = active ? "La otra persona está activa" : "La otra persona está desconectada";
        document.getElementById("statusDot").classList.toggle("active", active);
        typingIndicator.classList.toggle("hidden", !(active && other.typing));
        document.getElementById("typingText").textContent = "La otra persona está escribiendo…";
    } catch (error) { console.error(error); }
}

function renderMessages(messages) {
    const wasAtBottom = chatBody.scrollHeight - chatBody.scrollTop - chatBody.clientHeight < 80;
    chatBody.replaceChildren();
    messages.forEach((msg) => {
        const isMe = msg.sender === currentUser;
        const msgDiv = document.createElement("article");
        msgDiv.className = `message ${isMe ? "me" : "other"} ${msg.sender === "rosa" ? "from-rosa" : "from-azul"}`;
        const sender = document.createElement("span");
        sender.className = "sender-tag";
        sender.textContent = isMe ? "TÚ" : (msg.sender === "rosa" ? "ROSA" : "AZUL");
        const paragraph = document.createElement("p");
        paragraph.textContent = msg.text;
        const meta = document.createElement("div");
        meta.className = "time-container";
        const time = document.createElement("span");
        time.className = "time";
        time.textContent = msg.time;
        meta.appendChild(time);
        // Ambos participantes pueden eliminar cualquier mensaje de la conversación.
        const del = document.createElement("button");
        del.className = "delete-btn";
        del.type = "button";
        del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6m4-6v6M6 7l1 14h10l1-14M9 7V4h6v3"/></svg>';
        del.setAttribute("aria-label", `Eliminar mensaje de ${isMe ? "tu conversación" : "la otra persona"}`);
        del.addEventListener("click", () => deleteMessage(msg.id));
        meta.appendChild(del);
        msgDiv.append(sender, paragraph, meta);
        chatBody.appendChild(msgDiv);
    });
    if (messages.length !== lastMessageCount || wasAtBottom) chatBody.scrollTop = chatBody.scrollHeight;
    lastMessageCount = messages.length;
}

async function updatePresence(isTyping) {
    if (!currentUser) return;
    try {
        await fetch("/api/presence", { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: currentUser, is_typing: isTyping }) });
    } catch (error) { console.error(error); }
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentUser) return;
    sendBtn.disabled = true;
    try {
        const res = await fetch("/api/messages", { method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sender: currentUser, text }) });
        if (!res.ok) throw new Error("No se pudo enviar el mensaje.");
        messageInput.value = "";
        await updatePresence(false);
        await refreshChat();
        messageInput.focus();
    } catch (error) { alert("No se pudo enviar el mensaje. Comprueba tu conexión."); }
    finally { sendBtn.disabled = false; }
}

async function deleteMessage(id) {
    try {
        const res = await fetch("/api/messages/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id }) });
        if (!res.ok) throw new Error("No se pudo eliminar.");
        await refreshChat();
    } catch (error) { alert("No se pudo eliminar el mensaje."); }
}

loginBtn.addEventListener("click", login);
passwordInput.addEventListener("keydown", (event) => { if (event.key === "Enter") login(); });
sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("input", () => updatePresence(Boolean(messageInput.value.trim())));
messageInput.addEventListener("keydown", (event) => { if (event.key === "Enter") sendMessage(); });
window.addEventListener("beforeunload", () => {
    if (currentUser) navigator.sendBeacon("/api/presence", new Blob([JSON.stringify({ user: currentUser, is_typing: false })], { type: "application/json" }));
    clearInterval(refreshTimer); clearInterval(presenceTimer);
});
