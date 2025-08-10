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
            // Send message to the backend
            const response = await fetch("/invoke", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ user_request: userMessage }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Determine the final response to show
            // We can show the 'schedule' or 'confirmation' part of the response.
            // Let's create a summary.
            const assistantResponse = `Research: ${data.research_findings}\n\nSchedule: ${data.schedule}\n\nConfirmation: ${data.confirmation}`;

            // Remove the thinking indicator
            thinkingIndicator.remove();

            // Display assistant's final response
            addMessage(data.schedule || "Sorry, I couldn't process that.", "assistant");

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
