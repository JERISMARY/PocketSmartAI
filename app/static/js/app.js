/**
 * PocketSmart AI — Main JavaScript
 * Handles form submission, results rendering, loading states,
 * quota-aware error handling, and duplicate-request prevention.
 */

// ─── Utilities ────────────────────────────────────────────────────────────────
const formatINR = (amount) => {
  if (typeof amount !== 'number' || isNaN(amount)) return '₹0';
  return '₹' + Math.round(amount).toLocaleString('en-IN');
};

const escapeHtml = (str) => {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(String(str || '')));
  return div.innerHTML;
};

const showAlert = (containerId, message, type = 'error') => {
  const container = document.getElementById(containerId);
  if (!container) return;
  const icons = { error: '⚠️', success: '✅', warning: '⚡', info: 'ℹ️' };
  container.innerHTML = `
    <div class="alert alert-${type}" role="alert">
      <span>${icons[type] || '⚠️'}</span>
      <span>${escapeHtml(message)}</span>
    </div>`;
  container.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

const clearAlert = (containerId) => {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = '';
};

// ─── Loading State ────────────────────────────────────────────────────────────
const loading = {
  overlay: null,
  text: null,

  init() {
    this.overlay = document.getElementById('loading-overlay');
    this.text = document.getElementById('loading-text');
  },

  show(message = 'Analyzing your request...') {
    if (this.overlay) {
      this.overlay.classList.add('active');
      if (this.text) this.text.textContent = message;
    }
  },

  hide() {
    if (this.overlay) this.overlay.classList.remove('active');
  },

  setText(message) {
    if (this.text) this.text.textContent = message;
  }
};

// ─── Submit Guard — prevents duplicate requests ───────────────────────────────
let _isSubmitting = false;

function lockSubmit(btn) {
  if (_isSubmitting) return false;
  _isSubmitting = true;
  if (btn) {
    btn.disabled = true;
    btn._origText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-sm"></span> Analyzing...';
  }
  return true;
}

function unlockSubmit(btn) {
  _isSubmitting = false;
  if (btn && btn._origText) {
    btn.disabled = false;
    btn.innerHTML = btn._origText;
  }
}

// ─── Results Renderer ─────────────────────────────────────────────────────────
const resultsRenderer = {
  render(data, plannerType) {
    const section = document.getElementById('results-section');
    if (!section) return;

    // Guard: make sure budget_summary exists
    if (!data || !data.budget_summary) {
      console.error('PocketSmart: Missing budget_summary in response', data);
      return;
    }

    const { budget_summary, budget_allocation, recommendations, summary, ai_notes, outfit_analysis } = data;

    const remaining = budget_summary.remaining;
    const remainingClass = remaining >= 0 ? 'remaining' : 'over-budget';
    const remainingLabel = remaining >= 0 ? 'Remaining Budget' : 'Over Budget';

    // Budget overview
    const overviewHtml = `
      <div class="budget-overview animate-fade-in">
        <div class="budget-stat stagger-1">
          <div class="budget-stat-label">Total Budget</div>
          <div class="budget-stat-value total">${formatINR(budget_summary.total_budget)}</div>
        </div>
        <div class="budget-stat stagger-2">
          <div class="budget-stat-label">Estimated Spend</div>
          <div class="budget-stat-value spent">${formatINR(budget_summary.estimated_spend)}</div>
        </div>
        <div class="budget-stat stagger-3">
          <div class="budget-stat-label">${escapeHtml(remainingLabel)}</div>
          <div class="budget-stat-value ${remainingClass}">${formatINR(Math.abs(remaining))}</div>
        </div>
      </div>`;

    // AI Summary
    const summaryHtml = summary ? `
      <div class="ai-summary-box animate-fade-in stagger-2">
        <h4><span style="font-size:1.1rem">📋</span> Plan Overview</h4>
        <p>${escapeHtml(summary)}</p>
        ${outfit_analysis && outfit_analysis !== 'No image provided' ? `
          <div class="outfit-analysis-box">
            <h5>👗 Outfit Analysis</h5>
            <p>${escapeHtml(outfit_analysis)}</p>
          </div>` : ''}
      </div>` : '';

    // Budget Allocation
    const totalBudget = budget_summary.total_budget;
    const allocationHtml = budget_allocation && budget_allocation.length ? `
      <div class="allocation-section animate-fade-in stagger-3">
        <h4><span>💰</span> Budget Allocation</h4>
        <div class="allocation-grid">
          ${budget_allocation.map(item => {
            const pct = Math.min(item.percentage || (item.allocated_budget/totalBudget*100), 100);
            return `
            <div class="allocation-item">
              <div class="allocation-row">
                <span class="allocation-category">${escapeHtml(item.category)}</span>
                <div>
                  <span class="allocation-amount">${formatINR(item.allocated_budget)}</span>
                  <span class="allocation-pct">${pct.toFixed(1)}%</span>
                </div>
              </div>
              <div class="allocation-bar">
                <div class="allocation-bar-fill" style="width:${pct}%"></div>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>` : '';

    // Recommendations
    const recsHtml = recommendations && recommendations.length ? `
      <div class="recommendations-section animate-fade-in stagger-4">
        <h4><span>🎯</span> Top Recommendations <span class="rec-count">${recommendations.length} items</span></h4>
        <div class="recommendations-grid">
          ${recommendations.map((rec, i) => `
            <div class="rec-card stagger-${Math.min(i+1,5)}">
              <span class="rec-badge-demo">Est. Price</span>
              <div>
                <span class="rec-card-category">${escapeHtml(rec.category)}</span>
              </div>
              <div class="rec-card-header">
                <div class="rec-card-name">${escapeHtml(rec.name)}</div>
                <div class="rec-card-price">${formatINR(rec.estimated_price * rec.quantity)}</div>
              </div>
              ${rec.quantity > 1 ? `<div style="font-size:0.8rem;color:var(--text-muted);font-weight:500">Qty: ${rec.quantity} × ${formatINR(rec.estimated_price)}</div>` : ''}
              
              <div class="rec-card-platform">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>
                ${escapeHtml(rec.platform)}
              </div>
              
              ${rec.style ? `<div style="margin-top:0.25rem"><span class="rec-card-style">${escapeHtml(rec.style)}</span></div>` : ''}
              ${rec.reason ? `<div class="rec-card-reason">${escapeHtml(rec.reason)}</div>` : ''}
              ${rec.url ? `<a href="${escapeHtml(rec.url)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm" style="margin-top:auto;align-self:flex-start">View Product ↗</a>` : ''}
            </div>`).join('')}
        </div>
      </div>` : '<p class="text-center text-muted mt-xl">No recommendations generated.</p>';

    // AI Notes
    const notesHtml = ai_notes ? `
      <div class="ai-notes-box animate-fade-in stagger-5">
        <strong>💡 AI Stylist Note:</strong> ${escapeHtml(ai_notes)}
      </div>` : '';

    // Inject into DOM
    document.getElementById('results-budget-overview').innerHTML = overviewHtml;
    document.getElementById('results-summary').innerHTML = summaryHtml;
    document.getElementById('results-allocation').innerHTML = allocationHtml;
    document.getElementById('results-recommendations').innerHTML = recsHtml;
    document.getElementById('results-notes').innerHTML = notesHtml;

    // ── KEY FIX: override inline display:none with explicit display:block ──
    section.style.display = 'block';
    section.classList.add('visible');

    setTimeout(() => {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
};

// ─── Generic Planner Form Handler ─────────────────────────────────────────────
function setupPlannerForm(formId, endpoint, plannerType, alertContainerId = 'form-alert') {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('[type="submit"]');
    if (!lockSubmit(submitBtn)) return; // Block duplicate submission

    clearAlert(alertContainerId);
    loading.show('Analyzing your request...');

    setTimeout(() => loading.setText('Generating personalized recommendations...'), 2000);

    try {
      const formData = new FormData(form);

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle specific error types
        if (response.status === 429) {
          showAlert(alertContainerId,
            'AI recommendations are temporarily unavailable because the Gemini API quota has been reached. Please try again later.',
            'warning');
        } else if (response.status === 503) {
          showAlert(alertContainerId,
            'AI service is not configured. Please add your GEMINI_API_KEY to the .env file.',
            'warning');
        } else if (response.status === 401) {
          showAlert(alertContainerId, 'Your session has expired. Please log in again.', 'error');
          setTimeout(() => window.location.href = '/login', 2000);
        } else {
          showAlert(alertContainerId, data.error || 'An error occurred. Please try again.', 'error');
        }
        return;
      }

      // Render results
      resultsRenderer.render(data, plannerType);

    } catch (err) {
      console.error('Form submission error:', err);
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        showAlert(alertContainerId, 'Network error. Please check your connection.', 'error');
      } else {
        showAlert(alertContainerId, 'An unexpected error occurred. Please try again.', 'error');
      }
    } finally {
      loading.hide();
      unlockSubmit(submitBtn);
    }
  });
}

// ─── Checkbox Styling ─────────────────────────────────────────────────────────
function initCheckboxStyles() {
  document.querySelectorAll('.checkbox-label').forEach(label => {
    const input = label.querySelector('input[type="checkbox"]');
    if (!input) return;

    const update = () => label.classList.toggle('checked', input.checked);
    input.addEventListener('change', update);
    update();
  });
}

// ─── Toggle Styling ───────────────────────────────────────────────────────────
function initToggleStyles() {
  document.querySelectorAll('.toggle-input').forEach(input => {
    const label = input.nextElementSibling;
    if (!label) return;

    const update = () => label.classList.toggle('active', input.checked);
    input.addEventListener('change', update);
    update();
  });
}

// ─── Image Upload Preview ─────────────────────────────────────────────────────
function initImageUpload() {
  const uploadArea = document.getElementById('image-upload-area');
  const fileInput = document.getElementById('outfit_image');
  const preview = document.getElementById('image-preview');
  if (!uploadArea || !fileInput) return;

  uploadArea.addEventListener('click', () => fileInput.click());

  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });

  uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));

  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) {
      fileInput.files = e.dataTransfer.files;
      showImagePreview(file, preview, uploadArea);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) {
      showImagePreview(fileInput.files[0], preview, uploadArea);
    }
  });
}

function showImagePreview(file, preview, uploadArea) {
  // Validate
  const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) {
    showAlert('form-alert', 'Please upload a JPG, PNG, or WEBP image.', 'error');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showAlert('form-alert', 'Image must be smaller than 5MB.', 'error');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    if (preview) {
      preview.src = e.target.result;
      preview.style.display = 'block';
    }
    if (uploadArea) {
      uploadArea.querySelector('.upload-hint').textContent = `📎 ${file.name} (${(file.size/1024).toFixed(0)}KB)`;
    }
  };
  reader.readAsDataURL(file);
}

// ─── Number Input Formatting ──────────────────────────────────────────────────
function initBudgetInput() {
  const budgetInput = document.getElementById('budget');
  if (!budgetInput) return;
  budgetInput.addEventListener('blur', () => {
    const val = parseFloat(budgetInput.value);
    if (val <= 0 || isNaN(val)) {
      showAlert('form-alert', 'Please enter a valid budget amount.', 'warning');
    }
  });
}

// ─── DOMContentLoaded ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loading.init();
  initCheckboxStyles();
  initToggleStyles();
  initImageUpload();
  initBudgetInput();
});
