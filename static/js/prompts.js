/**
 * Prompt Management JavaScript for Synapse AI Web Application
 * 
 * This file handles the frontend functionality for system prompt management,
 * including editing, validation, testing, and history management.
 */

// Global state
let currentPromptData = null;
let promptHistory = [];

// Initialize the prompt management interface
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentPrompt();
    loadPromptHistory();
});

/**
 * Show a specific tab and hide others
 */
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.prompt-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected tab content
    const selectedContent = document.getElementById(`${tabName}-tab`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    // Add active class to selected tab
    const selectedTab = event.target;
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tabName === 'current') {
        loadCurrentPrompt();
    } else if (tabName === 'history') {
        loadPromptHistory();
    }
}

/**
 * Load the current system prompt and display it
 */
async function loadCurrentPrompt() {
    try {
        const response = await fetch('/api/prompt/current');
        const data = await response.json();
        
        if (response.ok) {
            currentPromptData = data;
            displayCurrentPrompt(data);
            displayPromptStats(data.stats);
            
            // Also populate the editor if it's empty
            const editor = document.getElementById('prompt-editor');
            if (editor && !editor.value.trim()) {
                editor.value = data.prompt;
            }
        } else {
            showError('current-prompt-display', data.message || 'Failed to load current prompt');
        }
    } catch (error) {
        console.error('Error loading current prompt:', error);
        showError('current-prompt-display', 'Failed to load current prompt');
    }
}

/**
 * Display the current prompt in the current tab
 */
function displayCurrentPrompt(data) {
    const display = document.getElementById('current-prompt-display');
    if (!display) return;
    
    display.innerHTML = `
        <div style="background: white; padding: 15px; border-radius: 6px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
            <div style="font-size: 14px; color: #666; margin-bottom: 10px;">
                Length: ${data.length} characters | Last updated: ${formatDate(data.timestamp)}
            </div>
            <div style="line-height: 1.6; color: #333; white-space: pre-wrap;">${escapeHtml(data.prompt)}</div>
        </div>
    `;
}

/**
 * Display prompt statistics
 */
function displayPromptStats(stats) {
    const statsContainer = document.getElementById('prompt-stats');
    if (!statsContainer || !stats) return;
    
    statsContainer.innerHTML = `
        <div class="stat-card">
            <div class="stat-number">${stats.total_prompts || 0}</div>
            <div class="stat-label">Total Prompts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.custom_prompts || 0}</div>
            <div class="stat-label">Custom Prompts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.current_prompt_length || 0}</div>
            <div class="stat-label">Current Length</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.config_version || 'N/A'}</div>
            <div class="stat-label">Config Version</div>
        </div>
    `;
}

/**
 * Validate the prompt in the editor
 */
async function validatePrompt() {
    const editor = document.getElementById('prompt-editor');
    const resultDiv = document.getElementById('validation-result');
    
    if (!editor || !resultDiv) return;
    
    const prompt = editor.value.trim();
    
    if (!prompt) {
        showValidationResult(false, 'Please enter a prompt to validate');
        return;
    }
    
    // Show loading state
    resultDiv.innerHTML = '<div class="loading"></div>Validating prompt...';
    
    try {
        const response = await fetch('/api/prompt/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: prompt })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showValidationResult(data.valid, data.valid ? data.message : data.error);
        } else {
            showValidationResult(false, data.message || 'Validation failed');
        }
    } catch (error) {
        console.error('Error validating prompt:', error);
        showValidationResult(false, 'Failed to validate prompt');
    }
}

/**
 * Show validation result
 */
function showValidationResult(isValid, message) {
    const resultDiv = document.getElementById('validation-result');
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
        <div class="validation-result ${isValid ? 'validation-success' : 'validation-error'}">
            ${isValid ? '✓' : '✗'} ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Test the prompt with a sample message
 */
async function testPrompt() {
    const editor = document.getElementById('prompt-editor');
    const resultDiv = document.getElementById('test-result');
    
    if (!editor || !resultDiv) return;
    
    const prompt = editor.value.trim();
    
    if (!prompt) {
        resultDiv.innerHTML = `
            <div class="validation-result validation-error">
                ✗ Please enter a prompt to test
            </div>
        `;
        return;
    }
    
    // Show loading state
    resultDiv.innerHTML = '<div class="loading"></div>Testing prompt...';
    
    try {
        const response = await fetch('/api/prompt/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                prompt: prompt,
                test_message: "Hello, how are you?"
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showTestResult(data);
        } else {
            resultDiv.innerHTML = `
                <div class="validation-result validation-error">
                    ✗ ${escapeHtml(data.message || 'Test failed')}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error testing prompt:', error);
        resultDiv.innerHTML = `
            <div class="validation-result validation-error">
                ✗ Failed to test prompt
            </div>
        `;
    }
}

/**
 * Show test result
 */
function showTestResult(data) {
    const resultDiv = document.getElementById('test-result');
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
        <div class="test-result">
            <div class="test-message">Test Message: "${escapeHtml(data.test_message)}"</div>
            <div class="test-response">${escapeHtml(data.response)}</div>
            <div style="margin-top: 10px; font-size: 12px; color: #666;">
                Response length: ${data.response_length} characters | 
                Tested at: ${formatDate(data.timestamp)}
            </div>
        </div>
    `;
}

/**
 * Save the current prompt in the editor
 */
async function savePrompt() {
    const editor = document.getElementById('prompt-editor');
    const nameInput = document.getElementById('prompt-name');
    
    if (!editor) return;
    
    const prompt = editor.value.trim();
    const name = nameInput ? nameInput.value.trim() : '';
    
    if (!prompt) {
        alert('Please enter a prompt to save');
        return;
    }
    
    // Show loading state
    const saveButton = event.target;
    const originalText = saveButton.textContent;
    saveButton.innerHTML = '<div class="loading"></div>Saving...';
    saveButton.disabled = true;
    
    try {
        const response = await fetch('/api/prompt/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                prompt: prompt,
                name: name || undefined
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Prompt saved successfully: ${data.prompt_name}`);
            
            // Clear the name input
            if (nameInput) {
                nameInput.value = '';
            }
            
            // Reload current prompt and history
            loadCurrentPrompt();
            loadPromptHistory();
        } else {
            alert(`Failed to save prompt: ${data.message}`);
        }
    } catch (error) {
        console.error('Error saving prompt:', error);
        alert('Failed to save prompt');
    } finally {
        // Restore button state
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    }
}

/**
 * Load prompt history
 */
async function loadPromptHistory() {
    const historyList = document.getElementById('prompt-history-list');
    if (!historyList) return;
    
    historyList.innerHTML = 'Loading prompt history...';
    
    try {
        const response = await fetch('/api/prompt/history');
        const data = await response.json();
        
        if (response.ok) {
            promptHistory = data.history || [];
            displayPromptHistory(promptHistory);
        } else {
            showError('prompt-history-list', data.message || 'Failed to load prompt history');
        }
    } catch (error) {
        console.error('Error loading prompt history:', error);
        showError('prompt-history-list', 'Failed to load prompt history');
    }
}

/**
 * Display prompt history
 */
function displayPromptHistory(history) {
    const historyList = document.getElementById('prompt-history-list');
    if (!historyList) return;
    
    if (history.length === 0) {
        historyList.innerHTML = `
            <div style="text-align: center; color: #666; padding: 40px;">
                No prompt history available
            </div>
        `;
        return;
    }
    
    const historyHtml = history.map((prompt, index) => `
        <div class="prompt-history-item">
            <div class="prompt-history-header">
                <div class="prompt-name">
                    ${escapeHtml(prompt.name)}
                    ${prompt.is_default ? '<span style="color: #28a745; font-size: 12px;">(Default)</span>' : ''}
                </div>
                <div class="prompt-date">${formatDate(prompt.created_at)}</div>
            </div>
            <div class="prompt-preview">${escapeHtml(prompt.prompt.substring(0, 200))}${prompt.prompt.length > 200 ? '...' : ''}</div>
            <div class="prompt-actions">
                <button class="btn btn-secondary" onclick="viewPrompt(${index})">View Full</button>
                <button class="btn btn-primary" onclick="restorePrompt(${index})">Restore</button>
                <button class="btn btn-warning" onclick="editPrompt(${index})">Edit</button>
            </div>
        </div>
    `).join('');
    
    historyList.innerHTML = historyHtml;
}

/**
 * View a full prompt from history
 */
function viewPrompt(index) {
    if (index < 0 || index >= promptHistory.length) return;
    
    const prompt = promptHistory[index];
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 8px; max-width: 80%; max-height: 80%; overflow-y: auto;">
            <h3>${escapeHtml(prompt.name)}</h3>
            <p style="color: #666; margin-bottom: 20px;">Created: ${formatDate(prompt.created_at)}</p>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; white-space: pre-wrap; line-height: 1.6; margin-bottom: 20px;">
                ${escapeHtml(prompt.prompt)}
            </div>
            <button class="btn btn-secondary" onclick="this.parentElement.parentElement.remove()">Close</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

/**
 * Restore a prompt from history
 */
async function restorePrompt(index) {
    if (index < 0 || index >= promptHistory.length) return;
    
    const prompt = promptHistory[index];
    
    if (!confirm(`Are you sure you want to restore "${prompt.name}" as the current prompt?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/prompt/restore', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ index: index })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Prompt restored successfully: ${data.prompt_name}`);
            loadCurrentPrompt();
        } else {
            alert(`Failed to restore prompt: ${data.message}`);
        }
    } catch (error) {
        console.error('Error restoring prompt:', error);
        alert('Failed to restore prompt');
    }
}

/**
 * Edit a prompt from history
 */
function editPrompt(index) {
    if (index < 0 || index >= promptHistory.length) return;
    
    const prompt = promptHistory[index];
    const editor = document.getElementById('prompt-editor');
    const nameInput = document.getElementById('prompt-name');
    
    if (editor) {
        editor.value = prompt.prompt;
    }
    
    if (nameInput) {
        nameInput.value = prompt.name;
    }
    
    // Switch to editor tab
    showTab('editor');
    
    // Update tab button states
    const tabs = document.querySelectorAll('.prompt-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    tabs[1].classList.add('active'); // Editor tab is second
}

/**
 * Utility function to show error messages
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div style="color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 6px;">
                Error: ${escapeHtml(message)}
            </div>
        `;
    }
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Utility function to format dates
 */
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (error) {
        return dateString;
    }
}