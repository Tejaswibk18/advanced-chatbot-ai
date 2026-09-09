// =========================================================
// Conversation
// =========================================================

let conversationId = crypto.randomUUID();


// =========================================================
// DOM Elements
// =========================================================

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

const recentChats =
    document.getElementById("recent-chats");


// =========================================================
// Add Message
// =========================================================

function addMessage(
    role,
    content = ""
) {

    const messageElement =
        document.createElement("div");

    messageElement.classList.add(
        "message",
        role
    );


    const contentElement =
        document.createElement("div");

    contentElement.classList.add(
        "message-content"
    );


    if (
        role === "assistant" &&
        content
    ) {

        contentElement.innerHTML =
            DOMPurify.sanitize(
                marked.parse(content)
            );

    } else {

        contentElement.textContent =
            content;

    }


    messageElement.appendChild(
        contentElement
    );


    chatMessages.appendChild(
        messageElement
    );


    scrollToBottom();


    return contentElement;
}


// =========================================================
// Scroll To Bottom
// =========================================================

function scrollToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// =========================================================
// Error Handling
// =========================================================

function showError(
    message
) {

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


// =========================================================
// Typing Indicator
// =========================================================

function showTypingIndicator() {

    const messageElement =
        document.createElement("div");

    messageElement.classList.add(
        "message",
        "assistant"
    );

    messageElement.id =
        "typing-indicator";


    messageElement.innerHTML = `
        <div class="message-content">
            <div class="typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;


    chatMessages.appendChild(
        messageElement
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


// =========================================================
// Welcome Screen
// =========================================================

function showWelcomeMessage() {

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


// =========================================================
// Load Recent Chats
// =========================================================

async function loadRecentChats() {

    try {

        const response =
            await fetch(
                "/chat/recent"
            );


        if (!response.ok) {

            throw new Error(
                "Failed to load recent chats."
            );

        }


        const data =
            await response.json();


        recentChats.innerHTML = "";


        const conversations =
            data.conversations || [];


        if (
            conversations.length === 0
        ) {

            recentChats.innerHTML = `
                <div class="empty-chats">
                    No recent chats
                </div>
            `;

            return;
        }


        conversations.forEach(
            conversation => {

                const chatButton =
                    document.createElement(
                        "button"
                    );


                chatButton.classList.add(
                    "recent-chat"
                );


                chatButton.type =
                    "button";


                chatButton.textContent =
                    conversation.title;


                chatButton.title =
                    conversation.title;


                if (
                    conversation.conversation_id ===
                    conversationId
                ) {

                    chatButton.classList.add(
                        "active"
                    );

                }


                chatButton.addEventListener(
                    "click",
                    () => {

                        loadConversation(
                            conversation.conversation_id
                        );

                    }
                );


                recentChats.appendChild(
                    chatButton
                );

            }
        );

    } catch (error) {

        console.error(
            "Failed to load recent chats:",
            error
        );

    }
}


// =========================================================
// Load Previous Conversation
// =========================================================

async function loadConversation(
    id
) {

    hideError();


    try {

        const response =
            await fetch(
                `/chat/${id}`
            );


        if (!response.ok) {

            const errorData =
                await response.json()
                    .catch(
                        () => ({})
                    );


            throw new Error(
                errorData.detail ||
                "Failed to load conversation."
            );

        }


        const data =
            await response.json();


        conversationId =
            data.conversation_id;


        chatMessages.innerHTML = "";


        const messages =
            data.messages || [];


        if (
            messages.length === 0
        ) {

            showWelcomeMessage();

            return;

        }


        messages.forEach(
            message => {

                let role =
                    message.role;


                if (
                    role === "model"
                ) {

                    role = "assistant";

                }


                addMessage(
                    role,
                    message.content
                );

            }
        );


        await loadRecentChats();


        messageInput.focus();

    } catch (error) {

        console.error(
            "Failed to load conversation:",
            error
        );


        showError(
            error.message
        );

    }
}


// =========================================================
// Send Message
// =========================================================

chatForm.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const message =
            messageInput.value.trim();


        if (!message) {

            return;

        }


        hideError();


        // Show user message immediately.
        addMessage(
            "user",
            message
        );


        // Clear input.
        messageInput.value = "";


        // Disable input while generating.
        sendButton.disabled = true;

        messageInput.disabled = true;


        // Show typing indicator.
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

                        body: JSON.stringify(
                            {
                                conversation_id:
                                    conversationId,

                                message:
                                    message
                            }
                        )
                    }
                );


            if (!response.ok) {

                let errorMessageText =
                    "Unable to get a response.";


                try {

                    const errorData =
                        await response.json();


                    if (
                        errorData.detail
                    ) {

                        errorMessageText =
                            errorData.detail;

                    }

                } catch {

                    // Ignore JSON parsing error.
                }


                throw new Error(
                    errorMessageText
                );

            }


            removeTypingIndicator();


            const assistantMessage =
                addMessage(
                    "assistant",
                    ""
                );


            if (!response.body) {

                throw new Error(
                    "Streaming is not supported by the browser."
                );

            }


            const reader =
                response.body.getReader();


            const decoder =
                new TextDecoder();


            let fullResponse = "";


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


                fullResponse +=
                    chunk;


                assistantMessage.innerHTML =
                    DOMPurify.sanitize(
                        marked.parse(
                            fullResponse
                        )
                    );


                scrollToBottom();

            }


            // Process any remaining decoder data.
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


            // Refresh sidebar.
            await loadRecentChats();

        } catch (error) {

            console.error(
                "Chat error:",
                error
            );


            removeTypingIndicator();


            showError(
                error.message ||
                "Something went wrong."
            );

        } finally {

            sendButton.disabled =
                false;

            messageInput.disabled =
                false;

            messageInput.focus();

        }

    }
);


// =========================================================
// New Chat
// =========================================================

newChatButton.addEventListener(
    "click",
    () => {

        hideError();


        // Generate a new conversation ID.
        //
        // IMPORTANT:
        // We DO NOT delete the previous conversation.

        conversationId =
            crypto.randomUUID();


        // Clear only the current UI.
        showWelcomeMessage();


        // Remove active state from old chats.
        document
            .querySelectorAll(
                ".recent-chat"
            )
            .forEach(
                button => {

                    button.classList.remove(
                        "active"
                    );

                }
            );


        messageInput.focus();

    }
);


// =========================================================
// Initial Application Load
// =========================================================

loadRecentChats();

messageInput.focus();

