const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');

// Function to add a message to the chat
function addMessage(label, content) {
    const messageDiv = document.createElement('div');
    
    // Add appropriate class based on label
    if (label.toLowerCase().startsWith('you:')) {
        messageDiv.className = 'message user-message';
    } else {
        messageDiv.className = 'message assistant-message';
    }
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'message-label';
    labelDiv.textContent = label;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format the content - handle bullet points
    const formattedContent = formatMessage(content);
    contentDiv.innerHTML = formattedContent;
    
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Function to format message content (convert bullet points to HTML)
function formatMessage(text) {
    // Split by lines
    const lines = text.split('\n');
    let inList = false;
    let html = '';
    
    lines.forEach(line => {
        const trimmed = line.trim();
        
        // Check if line is a bullet point
        if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            const listItem = trimmed.substring(1).trim();
            html += `<li>${escapeHtml(listItem)}</li>`;
        } else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            if (trimmed) {
                html += `<div>${escapeHtml(trimmed)}</div>`;
            } else {
                html += '<br>';
            }
        }
    });
    
    if (inList) {
        html += '</ul>';
    }
    
    return html || escapeHtml(text);
}

// Function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Function to send message
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addMessage('You:', message);
    
    // Clear input
    userInput.value = '';
    userInput.disabled = true;
    sendButton.disabled = true;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Add assistant response
        addMessage('Assistant:', data.response);
        
        // Check if user wants to quit
        if (data.quit) {
            userInput.disabled = true;
            sendButton.disabled = true;
            userInput.placeholder = 'Session ended. Refresh to start again.';
        } else {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    } catch (error) {
        addMessage('Assistant:', `Error: ${error.message}`);
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

// Event listeners
sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Focus input on load
userInput.focus();

