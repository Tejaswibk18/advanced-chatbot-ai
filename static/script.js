// =========================================================
// Conversation
// =========================================================

let conversationId =
    crypto.randomUUID();

let documentId = null;
let documentName = null;


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

// Document elements

const uploadDocumentButton =
    document.getElementById("upload-document");

const documentInput =
    document.getElementById("document-input");

const documentInfo =
    document.getElementById("document-info");

const documentNameElement =
    document.getElementById("document-name");

const removeDocumentButton =
    document.getElementById("remove-document");


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
// Add Generated Image
// =========================================================

function addGeneratedImage(
    imageData
) {

    const messageElement =
        document.createElement("div");

    messageElement.classList.add(
        "message",
        "assistant"
    );

    const contentElement =
        document.createElement("div");

    contentElement.classList.add(
        "message-content"
    );

    const imageWrapper =
        document.createElement("div");

    imageWrapper.classList.add(
        "generated-image-wrapper"
    );

    const image =
        document.createElement("img");

    image.classList.add(
        "generated-image"
    );

    image.src =
        imageData.url;

    image.alt =
        imageData.prompt ||
        "Generated image";

    image.loading =
        "lazy";

    imageWrapper.appendChild(
        image
    );

    contentElement.appendChild(
        imageWrapper
    );

    messageElement.appendChild(
        contentElement
    );

    chatMessages.appendChild(
        messageElement
    );

    scrollToBottom();
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

    errorMessage.textContent =
        "";

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

        recentChats.innerHTML =
            "";

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
                await response
                    .json()
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

        // Previous version of the UI does not
        // persist document_id yet.
        documentId = null;
        documentName = null;

        if (documentInfo) {
            documentInfo.classList.add(
                "hidden"
            );
        }

        if (documentNameElement) {
            documentNameElement.textContent =
                "Document";
        }

        chatMessages.innerHTML =
            "";

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

                    role =
                        "assistant";
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
// Process Stream Event
// =========================================================

function processStreamEvent(
    event,
    assistantMessage
) {

    // -----------------------------------------------------
    // Text
    // -----------------------------------------------------

    if (
        event.type === "text"
    ) {

        const text =
            event.content || "";

        assistantMessage.fullResponse +=
            text;

        assistantMessage.element.innerHTML =
            DOMPurify.sanitize(
                marked.parse(
                    assistantMessage.fullResponse
                )
            );

        scrollToBottom();

        return;
    }


    // -----------------------------------------------------
    // Image
    // -----------------------------------------------------

    if (
        event.type === "image"
    ) {

        addGeneratedImage(
            event
        );

        return;
    }


    // -----------------------------------------------------
    // Error
    // -----------------------------------------------------

    if (
        event.type === "error"
    ) {

        throw new Error(
            event.content ||
            "An error occurred."
        );
    }
}


// =========================================================
// Document Upload
// =========================================================

async function uploadDocument(file) {

    if (!file) {
        return;
    }

    const allowedExtensions = [
        ".pdf",
        ".docx",
        ".txt"
    ];

    const fileName =
        file.name.toLowerCase();

    const isAllowed =
        allowedExtensions.some(
            extension =>
                fileName.endsWith(extension)
        );

    if (!isAllowed) {

        showError(
            "Only PDF, DOCX and TXT files are supported."
        );

        return;
    }

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    hideError();

    try {

        // Disable pin button while uploading
        uploadDocumentButton.disabled =
            true;

        uploadDocumentButton.textContent =
            "⏳";

        const response =
            await fetch(
                "/documents/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

        let data = {};

        try {

            data =
                await response.json();

        } catch {

            data = {};
        }

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to upload document."
            );
        }

        // ---------------------------------------------
        // Save document information
        // ---------------------------------------------

        documentId =
            data.document_id;

        documentName =
            data.file_name;

        // ---------------------------------------------
        // Update UI
        // ---------------------------------------------

        if (documentNameElement) {

            documentNameElement.textContent =
                documentName;
        }

        if (documentInfo) {

            documentInfo.classList.remove(
                "hidden"
            );
        }

        console.log(
            "Document uploaded successfully:",
            data
        );

    } catch (error) {

        console.error(
            "Document upload error:",
            error
        );

        showError(
            error.message ||
            "Failed to upload document."
        );

    } finally {

        uploadDocumentButton.disabled =
            false;

        uploadDocumentButton.textContent =
            "📎";

        // Reset file input so the same
        // file can be selected again.
        documentInput.value = "";
    }
}


// =========================================================
// Document Upload Events
// =========================================================

// Open file picker when the pin button is clicked.

if (
    uploadDocumentButton &&
    documentInput
) {

    uploadDocumentButton.addEventListener(
        "click",
        () => {

            documentInput.click();
        }
    );


    // Handle selected file

    documentInput.addEventListener(
        "change",
        () => {

            const file =
                documentInput.files[0];

            if (file) {

                uploadDocument(file);
            }
        }
    );
}


// =========================================================
// Remove Document
// =========================================================

if (
    removeDocumentButton
) {

    removeDocumentButton.addEventListener(
        "click",
        () => {

            documentId = null;

            documentName = null;

            if (documentInfo) {

                documentInfo.classList.add(
                    "hidden"
                );
            }

            if (documentNameElement) {

                documentNameElement.textContent =
                    "Document";
            }

            hideError();
        }
    );
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

        addMessage(
            "user",
            message
        );

        messageInput.value =
            "";

        sendButton.disabled =
            true;

        messageInput.disabled =
            true;

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
                                    message,

                                document_id:
                                    documentId
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


            const assistantMessageElement =
                addMessage(
                    "assistant",
                    ""
                );


            const assistantMessage = {

                element:
                    assistantMessageElement,

                fullResponse:
                    ""
            };


            if (!response.body) {

                throw new Error(
                    "Streaming is not supported by the browser."
                );
            }


            const reader =
                response.body.getReader();

            const decoder =
                new TextDecoder();

            let buffer =
                "";


            while (true) {

                const {
                    value,
                    done
                } =
                    await reader.read();

                if (done) {
                    break;
                }


                buffer +=
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                const lines =
                    buffer.split("\n");


                buffer =
                    lines.pop();


                for (
                    const line of lines
                ) {

                    if (
                        !line.trim()
                    ) {

                        continue;
                    }


                    const event =
                        JSON.parse(
                            line
                        );


                    processStreamEvent(
                        event,
                        assistantMessage
                    );
                }
            }


            // -------------------------------------------------
            // Process remaining data
            // -------------------------------------------------

            buffer +=
                decoder.decode();


            if (
                buffer.trim()
            ) {

                const event =
                    JSON.parse(
                        buffer
                    );

                processStreamEvent(
                    event,
                    assistantMessage
                );
            }


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

        conversationId =
            crypto.randomUUID();

        // Clear document association
        documentId = null;

        documentName = null;

        if (documentInfo) {

            documentInfo.classList.add(
                "hidden"
            );
        }

        if (documentNameElement) {

            documentNameElement.textContent =
                "Document";
        }

        showWelcomeMessage();

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