// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;
let isDarkMode = true;

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, themeToggle;

document.addEventListener('DOMContentLoaded', () => {
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    themeToggle = document.getElementById('themeToggle');
    
    loadThemePreference();
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

function setupEventListeners() {
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewSession);
    }

    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        themeToggle.addEventListener('keydown', (e) => {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }
}

function toggleTheme() {
    isDarkMode = !isDarkMode;
    
    if (isDarkMode) {
        document.documentElement.classList.remove('light-mode');
    } else {
        document.documentElement.classList.add('light-mode');
    }
    
    try {
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    } catch (e) {
        console.log('localStorage not available:', e);
    }
    
    if (themeToggle) {
        themeToggle.setAttribute('aria-label', isDarkMode ? 'Switch to light mode' : 'Switch to dark mode');
    }
}

function loadThemePreference() {
    try {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            isDarkMode = false;
            document.documentElement.classList.add('light-mode');
            if (themeToggle) {
                themeToggle.setAttribute('aria-label', 'Switch to dark mode');
            }
        } else {
            isDarkMode = true;
            if (themeToggle) {
                themeToggle.setAttribute('aria-label', 'Switch to light mode');
            }
        }
    } catch (e) {
        console.log('localStorage not available:', e);
        isDarkMode = true;
        if (themeToggle) {
            themeToggle.setAttribute('aria-label', 'Switch to light mode');
        }
    }
}

async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    addMessage(query, 'user');

    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();
        
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources, isWelcome) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + type + (isWelcome ? ' welcome-message' : '');
    messageDiv.id = 'message-' + messageId;
    
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    let html = '<div class="message-content">' + displayContent + '</div>';
    
    if (sources && sources.length > 0) {
        const parsedSources = sources.map(s => {
            if (s.includes('<a ') && s.includes('</a>')) {
                return s;
            }
            const match = s.match(/\[([^\]]+)\]\(([^)]+)\)/);
            if (match) {
                const text = match[1];
                const url = match[2];
                return '<a href="' + url + '" target="_blank" rel="noopener noreferrer" class="source-link">' + text + '</a>';
            }
            return s;
        }).join(', ');

        html += '<details class="sources-collapsible"><summary class="sources-header">Sources</summary><div class="sources-content">' + parsedSources + '</div></details>';
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function createNewSession() {
    currentSessionId = null;
    if (chatMessages) {
        chatMessages.innerHTML = '';
        addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
    }
}

async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(API_URL + '/courses');
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => '<div class="course-title-item">' + title + '</div>')
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}
