/**
 * IndusTech AI Assistant Floating Widget
 * Asynchronous, non-blocking UI integration for RAG recommendations & industrial assistance.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Create floating widget button & chat drawer dynamically
    const widgetHTML = `
        <div id="ai-widget-container" style="position: fixed; bottom: 25px; right: 25px; z-index: 9999; font-family: sans-serif;">
            <!-- Floating Button -->
            <button id="ai-widget-toggle" style="background: linear-gradient(135deg, #2563eb, #1e40af); color: white; border: none; padding: 14px 20px; border-radius: 50px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4); display: flex; align-items: center; gap: 8px; transition: transform 0.2s;">
                <span>✨ AI Assistant</span>
            </button>

            <!-- Chat Drawer -->
            <div id="ai-chat-drawer" style="display: none; position: absolute; bottom: 65px; right: 0; width: 360px; height: 480px; background: #ffffff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); flex-direction: column; overflow: hidden; border: 1px solid #e2e8f0;">
                <!-- Header -->
                <div style="background: #1e293b; color: white; padding: 16px; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 15px;">IndusTech AI Advisor</div>
                        <div style="font-size: 11px; color: #94a3b8; font-weight: normal;">RAG Semantic Engine</div>
                    </div>
                    <button id="ai-chat-close" style="background: none; border: none; color: #94a3b8; font-size: 18px; cursor: pointer;">✕</button>
                </div>

                <!-- Chat Body -->
                <div id="ai-chat-messages" style="flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; font-size: 13px; background: #f8fafc;">
                    <div style="background: #e2e8f0; color: #1e293b; padding: 10px 14px; border-radius: 12px; max-width: 85%;">
                        Hello! I am your IndusTech AI Assistant. Ask me about job matches, suppliers, or industrial products!
                    </div>
                </div>

                <!-- Input Area -->
                <div style="padding: 12px; background: white; border-top: 1px solid #e2e8f0; display: flex; gap: 8px;">
                    <input type="text" id="ai-chat-input" placeholder="Type a message or skill..." style="flex: 1; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; outline: none; font-size: 13px;">
                    <button id="ai-chat-send" style="background: #2563eb; color: white; border: none; padding: 10px 14px; border-radius: 8px; font-weight: 600; cursor: pointer;">Send</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", widgetHTML);

    const toggleBtn = document.getElementById("ai-widget-toggle");
    const drawer = document.getElementById("ai-chat-drawer");
    const closeBtn = document.getElementById("ai-chat-close");
    const sendBtn = document.getElementById("ai-chat-send");
    const input = document.getElementById("ai-chat-input");
    const messages = document.getElementById("ai-chat-messages");

    toggleBtn.addEventListener("click", () => {
        drawer.style.display = drawer.style.display === "none" ? "flex" : "none";
    });

    closeBtn.addEventListener("click", () => {
        drawer.style.display = "none";
    });

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Render User Message
        const userMsg = document.createElement("div");
        userMsg.style.cssText = "background: #2563eb; color: white; padding: 10px 14px; border-radius: 12px; max-width: 85%; align-self: flex-end;";
        userMsg.textContent = text;
        messages.appendChild(userMsg);
        input.value = "";
        messages.scrollTop = messages.scrollHeight;

        // Render Loading Indicator
        const loadingMsg = document.createElement("div");
        loadingMsg.style.cssText = "background: #e2e8f0; color: #64748b; padding: 10px 14px; border-radius: 12px; max-width: 85%; align-self: flex-start;";
        loadingMsg.textContent = "Searching platform context...";
        messages.appendChild(loadingMsg);
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch("/api/v1/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            messages.removeChild(loadingMsg);

            const aiMsg = document.createElement("div");
            aiMsg.style.cssText = "background: #ffffff; border: 1px solid #e2e8f0; color: #1e293b; padding: 10px 14px; border-radius: 12px; max-width: 88%; align-self: flex-start; box-shadow: 0 2px 4px rgba(0,0,0,0.05); white-space: pre-wrap;";
            aiMsg.textContent = data.reply || "Sorry, I couldn't fetch a response right now.";
            messages.appendChild(aiMsg);
            messages.scrollTop = messages.scrollHeight;
        } catch (err) {
            loadingMsg.textContent = "Error connecting to AI service.";
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});
