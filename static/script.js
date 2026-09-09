let conversationId = crypto.randomUUID();


const chatForm =
    document.getElementById("chat-form");

const messageInput =
    document.getElementById("message-input");

const sendButton =
    document.getElementById("send-button");

const chatMessages =
    document.getElementById("chat-messages");

const newChatButton =
    document.getElementById("new-chat-button");

const errorMessage =
    document.getElementById("error-message");


/* =========================
   ADD MESSAGE
========================= */

function addMessage(
    role,
    content = ""
) {

    const message =
        document.createElement("div");

    message.classList.add(
        "message",
        role
    );


    const messageContent =
        document.createElement("div");

    messageContent.classList.add(
        "message-content"
    );


    if (
        role === "assistant" &&
        content
    ) {

        messageContent.innerHTML =
            DOMPurify.sanitize(
                marked.parse(content)
            );

    } else {

        messageContent.textContent =
            content;

    }


    message.appendChild(
        messageContent
    );


    chatMessages.appendChild(
        message
    );


    scrollToBottom();


    return messageContent;
}


/* =========================
   SCROLL
========================= */

function scrollToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


/* =========================
   ERROR
========================= */

function showError(message) {

    errorMessage.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );
}


function hideError() {

    errorMessage.textContent = "";

    errorMessage.classList.add(
        "hidden"
    );
}


/* =========================
   TYPING INDICATOR
========================= */

function showTypingIndicator() {

    const message =
        document.createElement("div");

    message.classList.add(
        "message",
        "assistant"
    );

    message.id =
        "typing-indicator";


    message.innerHTML = `
        <div class="message-content">
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;


    chatMessages.appendChild(
        message
    );


    scrollToBottom();
}


function removeTypingIndicator() {

    const indicator =
        document.getElementById(
            "typing-indicator"
        );

    if (indicator) {

        indicator.remove();

    }
}


/* =========================
   CLEAR CHAT UI
========================= */

function clearChatUI() {

    chatMessages.innerHTML = `
        <div class="welcome-message">

            <div class="welcome-icon">
                ✨
            </div>

            <h2>
                How can I help you?
            </h2>

            <p>
                Ask me about technology,
                science, programming,
                history, or anything else.
            </p>

        </div>
    `;
}


/* =========================
   SEND MESSAGE
========================= */

chatForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        const message =
            messageInput.value.trim();


        if (!message) {

            return;

        }


        hideError();


        /*
         * Display user message
         */

        addMessage(
            "user",
            message
        );


        /*
         * Clear input
         */

        messageInput.value = "";


        /*
         * Disable input
         */

        sendButton.disabled = true;

        messageInput.disabled = true;


        /*
         * Show typing indicator
         */

        showTypingIndicator();


        try {

            const response =
                await fetch(
                    "/chat/stream",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            conversation_id:
                                conversationId,

                            message:
                                message

                        })
                    }
                );


            /*
             * Check HTTP status
             */

            if (!response.ok) {

                let errorText =
                    "Unable to get a response.";

                try {

                    const errorData =
                        await response.json();

                    if (errorData.detail) {

                        errorText =
                            errorData.detail;

                    }

                } catch {

                    // Ignore JSON parsing error

                }


                throw new Error(
                    errorText
                );
            }


            /*
             * Remove typing indicator
             */

            removeTypingIndicator();


            /*
             * Create empty assistant message
             */

            const assistantMessage =
                addMessage(
                    "assistant",
                    ""
                );


            /*
             * Get response stream
             */

            if (!response.body) {

                throw new Error(
                    "Streaming is not supported by the server."
                );
            }


            const reader =
                response.body.getReader();


            const decoder =
                new TextDecoder();


            let fullResponse = "";


            /*
             * Read Gemini chunks
             */

            while (true) {

                const {
                    value,
                    done
                } = await reader.read();


                if (done) {

                    break;

                }


                const chunk =
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                /*
                 * Add chunk to complete response
                 */

                fullResponse += chunk;


                /*
                 * Convert Markdown → HTML
                 */

                const renderedHTML =
                    marked.parse(
                        fullResponse
                    );


                /*
                 * Sanitize generated HTML
                 */

                assistantMessage.innerHTML =
                    DOMPurify.sanitize(
                        renderedHTML
                    );


                scrollToBottom();

            }


            /*
             * Flush decoder
             */

            const remainingText =
                decoder.decode();


            if (remainingText) {

                fullResponse +=
                    remainingText;

                assistantMessage.innerHTML =
                    DOMPurify.sanitize(
                        marked.parse(
                            fullResponse
                        )
                    );

            }


        } catch (error) {

            console.error(
                "Chat error:",
                error
            );


            removeTypingIndicator();


            /*
             * If an assistant message was
             * partially created, don't leave
             * the user confused.
             */

            showError(
                error.message ||
                "Unable to get a response. Please try again."
            );

        } finally {

            /*
             * Re-enable input
             */

            sendButton.disabled = false;

            messageInput.disabled = false;

            messageInput.focus();

        }

    }
);


/* =========================
   NEW CHAT
========================= */

newChatButton.addEventListener(
    "click",
    async () => {

        hideError();


        try {

            await fetch(
                `/chat/${conversationId}`,
                {
                    method: "DELETE"
                }
            );

        } catch (error) {

            console.error(
                "Failed to clear conversation:",
                error
            );

        }


        /*
         * Generate new conversation ID
         */

        conversationId =
            crypto.randomUUID();


        /*
         * Clear UI
         */

        clearChatUI();


        /*
         * Focus input
         */

        messageInput.focus();

    }
);


/* =========================
   INITIALIZE
========================= */

messageInput.focus();