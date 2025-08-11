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

        chatForm.querySelector('button').disabled = true;
        messageInput.disabled = true;

        const assistantMessageElement = addMessageToUI("...", "assistant", true);
        let fullResponse = "";

        try {
            const response = await fetch("/invoke", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: conversationHistory }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // This is a simplified way to handle the stream.
            // A more robust implementation would use EventSource or ndjson.
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const textChunk = decoder.decode(value, { stream: true });
                // SSE format is "data: {...}\n\n"
                const jsonChunks = textChunk.split('\n\n').filter(Boolean);

                for (const jsonChunk of jsonChunks) {
                    if (jsonChunk.startsWith('data: ')) {
                        const jsonData = jsonChunk.substring(6);
                        const chunk = JSON.parse(jsonData);

                        assistantMessageElement.classList.remove("thinking");

                        if (chunk.type === "content") {
                            fullResponse += chunk.data;
                            assistantMessageElement.querySelector("p").textContent = fullResponse;
                        } else if (chunk.type === "tool_start") {
                            addMessageToUI(`Using tool: ${chunk.name} with input ${JSON.stringify(chunk.input)}`, "system");
                        } else if (chunk.type === "tool_end") {
                            addMessageToUI(`Tool Result: ${chunk.data}`, "system");
                        }
                    }
                }
                 chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            conversationHistory.push({ type: "ai", content: fullResponse });

        } catch (error) {
            console.error("Error invoking workflow:", error);
            assistantMessageElement.querySelector("p").textContent = "Sorry, an error occurred.";
        } finally {
            assistantMessageElement.classList.remove("thinking");
            reenableForm();
        }
    });

    function reenableForm() {
        chatForm.querySelector('button').disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }

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
