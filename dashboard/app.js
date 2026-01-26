// Dashboard App for MAYC #11555 Content Pipeline

const STORAGE_KEY = 'mayc_drafts_status';

// State
let drafts = [];
let currentFilter = 'all';

// DOM Elements
const container = document.getElementById('drafts-container');
const pendingCount = document.getElementById('pending-count');
const approvedCount = document.getElementById('approved-count');
const rejectedCount = document.getElementById('rejected-count');
const toast = document.getElementById('toast');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDrafts();
    setupFilters();
});

// Load drafts from JSON file
async function loadDrafts() {
    try {
        const response = await fetch('drafts.json');
        if (!response.ok) {
            throw new Error('Failed to load drafts');
        }
        drafts = await response.json();

        // Load saved statuses from localStorage
        const savedStatuses = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        drafts.forEach(draft => {
            if (savedStatuses[draft.id]) {
                draft.status = savedStatuses[draft.id];
            }
        });

        updateStats();
        renderDrafts();
    } catch (error) {
        console.error('Error loading drafts:', error);
        container.innerHTML = '<p class="no-drafts">No drafts available. Run the pipeline to generate content.</p>';
    }
}

// Setup filter buttons
function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderDrafts();
        });
    });
}

// Update stats display
function updateStats() {
    const counts = { pending: 0, approved: 0, rejected: 0 };
    drafts.forEach(draft => {
        counts[draft.status] = (counts[draft.status] || 0) + 1;
    });

    pendingCount.textContent = counts.pending;
    approvedCount.textContent = counts.approved;
    rejectedCount.textContent = counts.rejected;
}

// Render drafts
function renderDrafts() {
    const filtered = currentFilter === 'all'
        ? drafts
        : drafts.filter(d => d.status === currentFilter);

    if (filtered.length === 0) {
        container.innerHTML = `<p class="no-drafts">No ${currentFilter === 'all' ? '' : currentFilter + ' '}drafts found.</p>`;
        return;
    }

    container.innerHTML = filtered.map(draft => createDraftCard(draft)).join('');

    // Attach event listeners
    container.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', handleAction);
    });
}

// Create draft card HTML
function createDraftCard(draft) {
    const sourceUrl = draft.source?.url || '#';
    const sourceUsername = draft.source?.username || 'unknown';
    const sourceText = draft.source?.text || '';
    const createdAt = new Date(draft.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    return `
        <div class="draft-card ${draft.status}" data-id="${draft.id}">
            <div class="source-section">
                <div class="source-header">
                    <span class="source-label">Inspired by</span>
                    <a href="${sourceUrl}" target="_blank" class="source-username">@${sourceUsername}</a>
                </div>
                <p class="source-text">${escapeHtml(sourceText)}</p>
            </div>

            <div class="draft-section">
                <div class="draft-label">Your Draft</div>
                <p class="draft-text">${escapeHtml(draft.draft)}</p>

                <div class="actions">
                    <button class="action-btn btn-copy" data-action="copy" data-id="${draft.id}">
                        📋 Copy
                    </button>
                    ${draft.status !== 'approved' ? `
                        <button class="action-btn btn-approve" data-action="approve" data-id="${draft.id}">
                            ✓ Approve
                        </button>
                    ` : ''}
                    ${draft.status !== 'rejected' ? `
                        <button class="action-btn btn-reject" data-action="reject" data-id="${draft.id}">
                            ✗ Reject
                        </button>
                    ` : ''}
                    ${draft.status !== 'pending' ? `
                        <button class="action-btn btn-reset" data-action="reset" data-id="${draft.id}">
                            ↺ Reset
                        </button>
                    ` : ''}
                </div>

                <div class="draft-meta">
                    <span>${createdAt}</span>
                    <span class="status-badge ${draft.status}">${draft.status}</span>
                </div>
            </div>
        </div>
    `;
}

// Handle button actions
function handleAction(event) {
    const btn = event.currentTarget;
    const action = btn.dataset.action;
    const id = btn.dataset.id;

    const draft = drafts.find(d => d.id === id);
    if (!draft) return;

    switch (action) {
        case 'copy':
            copyToClipboard(draft.draft);
            showToast('Copied to clipboard!');
            break;
        case 'approve':
            updateStatus(id, 'approved');
            showToast('Draft approved!');
            break;
        case 'reject':
            updateStatus(id, 'rejected');
            showToast('Draft rejected');
            break;
        case 'reset':
            updateStatus(id, 'pending');
            showToast('Status reset');
            break;
    }
}

// Update draft status
function updateStatus(id, status) {
    const draft = drafts.find(d => d.id === id);
    if (draft) {
        draft.status = status;

        // Save to localStorage
        const savedStatuses = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
        savedStatuses[id] = status;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(savedStatuses));

        updateStats();
        renderDrafts();
    }
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

// Show toast notification
function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show', 'success');

    setTimeout(() => {
        toast.classList.remove('show', 'success');
    }, 2000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
