document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const chatMessages = document.getElementById("chat-messages");

    let conversationHistory = [];

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userMessage = messageInput.value.trim();
        if (!userMessage) return;

        addMessageToUI(userMessage, "user");
        conversationHistory.push({ type: "human", content: userMessage });
        messageInput.value = "";
        messageInput.focus();

        const thinkingIndicator = addMessageToUI("...", "assistant", true);

        const eventSource = new EventSource(`/invoke?messages=${encodeURIComponent(JSON.stringify(conversationHistory))}`);

        let assistantMessageElement = thinkingIndicator;
        let fullResponse = "";

        eventSource.onmessage = function(event) {
            assistantMessageElement.classList.remove("thinking");
            const chunk = JSON.parse(event.data);

            if (chunk.type === "content") {
                fullResponse += chunk.data;
                assistantMessageElement.querySelector("p").textContent = fullResponse;
            } else if (chunk.type === "tool_call") {
                // You could optionally display tool calls to the user for debugging
                console.log("Tool call:", chunk.data);
            } else if (chunk.type === "tool_end") {
                 console.log("Tool end:", chunk.data);
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };

        eventSource.onerror = function(err) {
            console.error("EventSource failed:", err);
            assistantMessageElement.querySelector("p").textContent = "Sorry, an error occurred.";
            assistantMessageElement.classList.remove("thinking");
            eventSource.close();
        };

        eventSource.addEventListener('end', function() {
            conversationHistory.push({ type: "ai", content: fullResponse });
            eventSource.close();
        });
    });

    function addMessageToUI(text, sender, isThinking = false) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);

        const p = document.createElement("p");
        p.textContent = text;
        messageElement.appendChild(p);

        if (isThinking) {
            messageElement.classList.add("thinking");
        }

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageElement;
    }
});
