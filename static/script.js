document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const chatMessages = document.getElementById("chat-messages");

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const userMessage = messageInput.value.trim();
        if (!userMessage) {
            return;
        }

        // Display user's message
        addMessage(userMessage, "user");
        messageInput.value = "";

        // Show a thinking indicator
        const thinkingIndicator = addMessage("Thinking...", "assistant", true);

        try {
            // Send message and user_id to the backend
            const response = await fetch("/invoke", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    user_request: userMessage,
                    user_id: "default_user" // Hardcoded for demonstration
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove the thinking indicator
            thinkingIndicator.remove();

            // The 'confirmation' field contains the final, user-facing message.
            const assistantResponse = data.confirmation || "Sorry, I couldn't process that.";
            addMessage(assistantResponse, "assistant");

        } catch (error) {
            console.error("Error invoking workflow:", error);
            thinkingIndicator.remove();
            addMessage("Sorry, something went wrong. Please try again.", "assistant");
        }
    });

    function addMessage(text, sender, isThinking = false) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender);

        const p = document.createElement("p");
        p.textContent = text;
        messageElement.appendChild(p);

        if (isThinking) {
            messageElement.classList.add("thinking");
        }

        chatMessages.appendChild(messageElement);
        // Scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageElement;
    }
});
