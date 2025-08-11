document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const chatMessages = document.getElementById("chat-messages");

    // --- State Management ---
    let conversationHistory = [];

    // --- Event Listeners ---
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userMessage = messageInput.value.trim();
        if (!userMessage) return;

        // Add user message to UI and history
        addMessageToUI(userMessage, "user");
        conversationHistory.push({ type: "human", content: userMessage });
        messageInput.value = "";

        // Show a thinking indicator
        const thinkingIndicator = addMessageToUI("Thinking...", "assistant", true);

        try {
            // Send the new message and the entire history to the backend
            const response = await fetch("/invoke", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_request: userMessage,
                    user_id: "default_user",
                    conversation_history: conversationHistory.slice(0, -1), // Send history *before* this message
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Update the history with the full history from the server
            conversationHistory = data.conversation_history || conversationHistory;

            // Remove the thinking indicator
            thinkingIndicator.remove();

            // The 'confirmation' field contains the agent's response for this turn
            const assistantResponse = data.confirmation || "Sorry, I couldn't process that.";
            addMessageToUI(assistantResponse, "assistant");

        } catch (error) {
            console.error("Error invoking workflow:", error);
            thinkingIndicator.remove();
            addMessageToUI("Sorry, something went wrong. Please try again.", "assistant");
        }
    });

    // --- UI Functions ---
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
