"use strict";

/**
 * Support Ticket Manager - vanilla JS front-end.
 * Talks exclusively to the same-origin REST API defined in src/routers/tickets.py.
 * No ticket data is ever hardcoded here; everything is fetched live from the API.
 */

const API_BASE = "/tickets";

const CATEGORIES = [
  "account_access",
  "technical_issue",
  "billing_question",
  "feature_request",
  "bug_report",
  "other",
];
const PRIORITIES = ["urgent", "high", "medium", "low"];
const STATUSES = ["new", "in_progress", "waiting_customer", "resolved", "closed"];
const SOURCES = ["web_form", "email", "api", "chat", "phone"];
const DEVICE_TYPES = ["desktop", "mobile", "tablet"];

function humanize(value) {
  if (!value) return "";
  return value
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function populateSelect(select, values, { includeBlank, blankLabel } = {}) {
  select.innerHTML = "";
  if (includeBlank) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = blankLabel || "Any";
    select.appendChild(opt);
  }
  for (const value of values) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = humanize(value);
    select.appendChild(opt);
  }
}

// ---------------------------------------------------------------------------
// Toasts
// ---------------------------------------------------------------------------

function showToast(message, type = "info", timeoutMs = 4500) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), timeoutMs);
}

function extractErrorMessage(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload.error === "string") {
    if (Array.isArray(payload.details) && payload.details.length) {
      const details = payload.details
        .map((d) => `${d.field || "field"}: ${d.message}`)
        .join("; ");
      return `${payload.error} - ${details}`;
    }
    return payload.error;
  }
  return fallback;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  let payload = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (e) {
      payload = null;
    }
  }
  if (!response.ok) {
    const message = extractErrorMessage(payload, `Request failed (${response.status})`);
    throw new Error(message);
  }
  return payload;
}

// ---------------------------------------------------------------------------
// Application state
// ---------------------------------------------------------------------------

const state = {
  page: 1,
  pageSize: 20,
  filters: { category: "", priority: "", status: "", customer_id: "" },
  ticketsById: new Map(),
};

// ---------------------------------------------------------------------------
// Ticket list
// ---------------------------------------------------------------------------

function buildListQuery() {
  const params = new URLSearchParams();
  params.set("page", String(state.page));
  params.set("page_size", String(state.pageSize));
  if (state.filters.category) params.set("category", state.filters.category);
  if (state.filters.priority) params.set("priority", state.filters.priority);
  if (state.filters.status) params.set("status", state.filters.status);
  if (state.filters.customer_id) params.set("customer_id", state.filters.customer_id);
  return params.toString();
}

async function loadTickets() {
  const statusEl = document.getElementById("list-status");
  statusEl.textContent = "Loading tickets...";
  try {
    const query = buildListQuery();
    const data = await apiRequest(`${API_BASE}?${query}`);
    state.ticketsById.clear();
    for (const ticket of data.items) {
      state.ticketsById.set(ticket.id, ticket);
    }
    renderTicketTable(data.items);
    renderPagination(data.total, data.page, data.page_size);
    statusEl.textContent = `Showing ${data.items.length} of ${data.total} ticket(s)`;
  } catch (err) {
    statusEl.textContent = "Failed to load tickets.";
    showToast(err.message, "error");
  }
}

function priorityBadgeClass(priority) {
  return `badge badge-priority-${priority}`;
}

function renderTicketTable(tickets) {
  const tbody = document.getElementById("ticket-table-body");
  tbody.innerHTML = "";

  if (!tickets.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="7"><div class="empty-state">No tickets match the current filters.</div></td>`;
    tbody.appendChild(tr);
    return;
  }

  for (const ticket of tickets) {
    const tr = document.createElement("tr");
    tr.dataset.ticketId = ticket.id;

    const created = new Date(ticket.created_at).toLocaleString();

    tr.innerHTML = `
      <td data-label="Subject" class="subject-cell">${escapeHtml(ticket.subject)}</td>
      <td data-label="Customer">${escapeHtml(ticket.customer_name)}</td>
      <td data-label="Category"><span class="badge badge-category">${humanize(ticket.category)}</span></td>
      <td data-label="Priority"><span class="${priorityBadgeClass(ticket.priority)}">${humanize(ticket.priority)}</span></td>
      <td data-label="Status"><span class="badge badge-status">${humanize(ticket.status)}</span></td>
      <td data-label="Created">${created}</td>
      <td data-label="Actions">
        <div class="row-actions">
          <button class="btn btn-ghost btn-small" data-action="view">View</button>
          <button class="btn btn-secondary btn-small" data-action="classify">Classify</button>
          <button class="btn btn-danger btn-small" data-action="delete">Delete</button>
        </div>
      </td>
    `;

    tr.addEventListener("click", (event) => {
      const action = event.target.closest("[data-action]");
      if (!action) {
        openDetailModal(ticket.id);
        return;
      }
      event.stopPropagation();
      const kind = action.dataset.action;
      if (kind === "view") openDetailModal(ticket.id);
      if (kind === "classify") runAutoClassify(ticket.id);
      if (kind === "delete") confirmDeleteTicket(ticket.id);
    });

    tbody.appendChild(tr);
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

function renderPagination(total, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  document.getElementById("pagination-info").textContent = `Page ${page} of ${totalPages}`;
  document.getElementById("btn-prev-page").disabled = page <= 1;
  document.getElementById("btn-next-page").disabled = page >= totalPages;
}

// ---------------------------------------------------------------------------
// Ticket detail modal
// ---------------------------------------------------------------------------

function classificationHtml(ticket) {
  const c = ticket.classification;
  if (!c) {
    return `<p class="detail-section-title">Classification</p><p>No classification recorded yet. Use "Auto-Classify" to run it.</p>`;
  }
  const keywords = (c.keywords_found || [])
    .map((k) => `<span class="keyword-chip">${escapeHtml(k)}</span>`)
    .join("") || "<em>none</em>";
  return `
    <p class="detail-section-title">Classification</p>
    <div class="classification-box">
      <div class="detail-grid">
        <div class="detail-item"><dt>Category</dt><dd>${humanize(c.category)}</dd></div>
        <div class="detail-item"><dt>Priority</dt><dd>${humanize(c.priority)}</dd></div>
        <div class="detail-item"><dt>Confidence</dt><dd>${(c.confidence * 100).toFixed(0)}%</dd></div>
        <div class="detail-item"><dt>Manually Overridden</dt><dd>${c.manually_overridden ? "Yes" : "No"}</dd></div>
      </div>
      <p><strong>Reasoning:</strong> ${escapeHtml(c.reasoning)}</p>
      <p><strong>Keywords found:</strong> ${keywords}</p>
    </div>
  `;
}

function detailHtml(ticket) {
  const meta = ticket.metadata || {};
  const tags = (ticket.tags || []).map((t) => `<span class="keyword-chip">${escapeHtml(t)}</span>`).join("") || "<em>none</em>";
  return `
    <div class="detail-grid">
      <div class="detail-item"><dt>Subject</dt><dd>${escapeHtml(ticket.subject)}</dd></div>
      <div class="detail-item"><dt>Status</dt><dd>${humanize(ticket.status)}</dd></div>
      <div class="detail-item"><dt>Customer</dt><dd>${escapeHtml(ticket.customer_name)} (${escapeHtml(ticket.customer_id)})</dd></div>
      <div class="detail-item"><dt>Email</dt><dd>${escapeHtml(ticket.customer_email)}</dd></div>
      <div class="detail-item"><dt>Assigned To</dt><dd>${escapeHtml(ticket.assigned_to) || "<em>unassigned</em>"}</dd></div>
      <div class="detail-item"><dt>Created</dt><dd>${new Date(ticket.created_at).toLocaleString()}</dd></div>
      <div class="detail-item"><dt>Updated</dt><dd>${new Date(ticket.updated_at).toLocaleString()}</dd></div>
      <div class="detail-item"><dt>Resolved</dt><dd>${ticket.resolved_at ? new Date(ticket.resolved_at).toLocaleString() : "<em>not resolved</em>"}</dd></div>
    </div>
    <p class="detail-section-title">Description</p>
    <p>${escapeHtml(ticket.description)}</p>
    <p class="detail-section-title">Tags</p>
    <p>${tags}</p>
    ${classificationHtml(ticket)}
    <p class="detail-section-title">Metadata</p>
    <div class="detail-grid">
      <div class="detail-item"><dt>Source</dt><dd>${humanize(meta.source)}</dd></div>
      <div class="detail-item"><dt>Device Type</dt><dd>${meta.device_type ? humanize(meta.device_type) : "<em>unset</em>"}</dd></div>
      <div class="detail-item"><dt>Browser</dt><dd>${meta.browser ? escapeHtml(meta.browser) : "<em>unset</em>"}</dd></div>
    </div>
  `;
}

let activeDetailTicketId = null;

async function openDetailModal(ticketId) {
  try {
    const ticket = await apiRequest(`${API_BASE}/${ticketId}`);
    state.ticketsById.set(ticket.id, ticket);
    activeDetailTicketId = ticket.id;
    document.getElementById("ticket-detail-title").textContent = ticket.subject;
    document.getElementById("ticket-detail-body").innerHTML = detailHtml(ticket);
    openModal("ticket-detail-modal");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function runAutoClassify(ticketId) {
  try {
    const ticket = await apiRequest(`${API_BASE}/${ticketId}/auto-classify`, { method: "POST" });
    state.ticketsById.set(ticket.id, ticket);
    showToast(
      `Classified as ${humanize(ticket.classification.category)} / ${humanize(ticket.classification.priority)} (${Math.round(ticket.classification.confidence * 100)}% confidence)`,
      "success"
    );
    if (activeDetailTicketId === ticketId) {
      document.getElementById("ticket-detail-body").innerHTML = detailHtml(ticket);
    }
    await loadTickets();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function confirmDeleteTicket(ticketId) {
  const ticket = state.ticketsById.get(ticketId);
  const label = ticket ? ticket.subject : ticketId;
  if (!window.confirm(`Delete ticket "${label}"? This cannot be undone.`)) return;
  try {
    await apiRequest(`${API_BASE}/${ticketId}`, { method: "DELETE" });
    showToast("Ticket deleted.", "success");
    closeModal("ticket-detail-modal");
    await loadTickets();
  } catch (err) {
    showToast(err.message || "Failed to delete ticket.", "error");
  }
}

// ---------------------------------------------------------------------------
// Create / Edit form
// ---------------------------------------------------------------------------

const form = document.getElementById("ticket-form");
const fieldErrorEls = {};
document.querySelectorAll(".field-error").forEach((el) => {
  fieldErrorEls[el.dataset.errorFor] = el;
});

function clearFieldErrors() {
  Object.values(fieldErrorEls).forEach((el) => (el.textContent = ""));
}

function setFieldError(field, message) {
  if (fieldErrorEls[field]) fieldErrorEls[field].textContent = message;
}

function updateCharCounts() {
  const subject = document.getElementById("field-subject").value;
  const description = document.getElementById("field-description").value;
  document.getElementById("subject-count").textContent = `${subject.length}/200`;
  document.getElementById("description-count").textContent = `${description.length}/2000`;
}

document.getElementById("field-subject").addEventListener("input", updateCharCounts);
document.getElementById("field-description").addEventListener("input", updateCharCounts);

function resetTicketForm() {
  form.reset();
  clearFieldErrors();
  document.getElementById("ticket-form-id").value = "";
  updateCharCounts();
}

function openCreateModal() {
  resetTicketForm();
  document.getElementById("ticket-form-title").textContent = "New Ticket";
  document.getElementById("field-status-wrapper").style.display = "none";
  document.getElementById("auto-classify-field").style.display = "";
  document.getElementById("field-auto-classify").checked = false;
  openModal("ticket-form-modal");
}

function openEditModal(ticketId) {
  const ticket = state.ticketsById.get(ticketId);
  if (!ticket) return;
  resetTicketForm();
  document.getElementById("ticket-form-title").textContent = `Edit Ticket`;
  document.getElementById("ticket-form-id").value = ticket.id;
  document.getElementById("field-customer-id").value = ticket.customer_id;
  document.getElementById("field-customer-email").value = ticket.customer_email;
  document.getElementById("field-customer-name").value = ticket.customer_name;
  document.getElementById("field-assigned-to").value = ticket.assigned_to || "";
  document.getElementById("field-subject").value = ticket.subject;
  document.getElementById("field-description").value = ticket.description;
  document.getElementById("field-category").value = ticket.category || "";
  document.getElementById("field-priority").value = ticket.priority || "";
  document.getElementById("field-status").value = ticket.status;
  document.getElementById("field-tags").value = (ticket.tags || []).join(", ");
  const meta = ticket.metadata || {};
  document.getElementById("field-meta-source").value = meta.source || "api";
  document.getElementById("field-meta-device").value = meta.device_type || "";
  document.getElementById("field-meta-browser").value = meta.browser || "";
  document.getElementById("field-status-wrapper").style.display = "";
  document.getElementById("auto-classify-field").style.display = "none";
  updateCharCounts();
  openModal("ticket-form-modal");
}

function validateForm(values) {
  let valid = true;
  clearFieldErrors();

  if (!values.customer_id || values.customer_id.length > 100) {
    setFieldError("customer_id", "Required, max 100 characters.");
    valid = false;
  }
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(values.customer_email)) {
    setFieldError("customer_email", "Enter a valid email address.");
    valid = false;
  }
  if (!values.customer_name || values.customer_name.length > 200) {
    setFieldError("customer_name", "Required, max 200 characters.");
    valid = false;
  }
  if (!values.subject || values.subject.length > 200) {
    setFieldError("subject", "Required, 1-200 characters.");
    valid = false;
  }
  if (!values.description || values.description.length < 10 || values.description.length > 2000) {
    setFieldError("description", "Required, 10-2000 characters.");
    valid = false;
  }
  return valid;
}

function buildPayloadFromForm() {
  const tagsRaw = document.getElementById("field-tags").value;
  const tags = tagsRaw
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const values = {
    customer_id: document.getElementById("field-customer-id").value.trim(),
    customer_email: document.getElementById("field-customer-email").value.trim(),
    customer_name: document.getElementById("field-customer-name").value.trim(),
    subject: document.getElementById("field-subject").value.trim(),
    description: document.getElementById("field-description").value.trim(),
    assigned_to: document.getElementById("field-assigned-to").value.trim() || null,
    tags,
  };

  const category = document.getElementById("field-category").value;
  const priority = document.getElementById("field-priority").value;
  const deviceType = document.getElementById("field-meta-device").value;
  const browser = document.getElementById("field-meta-browser").value.trim();

  const payload = {
    ...values,
    category: category || null,
    priority: priority || null,
    metadata: {
      source: document.getElementById("field-meta-source").value,
      device_type: deviceType || null,
      browser: browser || null,
    },
  };
  return { payload, values };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const { payload, values } = buildPayloadFromForm();
  if (!validateForm(values)) {
    showToast("Please fix the highlighted fields.", "error");
    return;
  }

  const ticketId = document.getElementById("ticket-form-id").value;
  const submitBtn = document.getElementById("btn-submit-ticket-form");
  submitBtn.disabled = true;
  try {
    if (ticketId) {
      const status = document.getElementById("field-status").value;
      await apiRequest(`${API_BASE}/${ticketId}`, {
        method: "PUT",
        body: JSON.stringify({ ...payload, status }),
      });
      showToast("Ticket updated.", "success");
    } else {
      const autoClassify = document.getElementById("field-auto-classify").checked;
      await apiRequest(`${API_BASE}?auto_classify=${autoClassify}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      showToast("Ticket created.", "success");
    }
    closeModal("ticket-form-modal");
    await loadTickets();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    submitBtn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// Bulk import
// ---------------------------------------------------------------------------

document.getElementById("btn-submit-import").addEventListener("click", async () => {
  const fileInput = document.getElementById("import-file");
  const summaryEl = document.getElementById("import-summary");
  if (!fileInput.files.length) {
    showToast("Choose a file to import first.", "error");
    return;
  }
  const autoClassify = document.getElementById("import-auto-classify").checked;
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const btn = document.getElementById("btn-submit-import");
  btn.disabled = true;
  summaryEl.classList.add("hidden");
  try {
    const response = await fetch(`${API_BASE}/import?auto_classify=${autoClassify}`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(extractErrorMessage(data, "Import failed."));
    }
    renderImportSummary(data);
    showToast(`Imported ${data.successful}/${data.total} ticket(s).`, data.failed ? "info" : "success");
    await loadTickets();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
});

function renderImportSummary(summary) {
  const el = document.getElementById("import-summary");
  el.classList.remove("hidden");
  let html = `<p><strong>Total:</strong> ${summary.total} &nbsp; <strong>Successful:</strong> ${summary.successful} &nbsp; <strong>Failed:</strong> ${summary.failed}</p>`;
  if (summary.errors && summary.errors.length) {
    html += `<table><thead><tr><th>Index</th><th>Field</th><th>Message</th></tr></thead><tbody>`;
    for (const e of summary.errors) {
      html += `<tr><td>${e.index ?? ""}</td><td>${escapeHtml(e.field || "")}</td><td>${escapeHtml(e.message || "")}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  el.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Modal helpers
// ---------------------------------------------------------------------------

function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

document.querySelectorAll("[data-close-modal]").forEach((btn) => {
  btn.addEventListener("click", () => closeModal(btn.dataset.closeModal));
});

document.querySelectorAll(".modal-overlay").forEach((overlay) => {
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) overlay.classList.add("hidden");
  });
});

// ---------------------------------------------------------------------------
// Wiring: header buttons, filters, pagination, detail modal actions
// ---------------------------------------------------------------------------

document.getElementById("btn-new-ticket").addEventListener("click", openCreateModal);
document.getElementById("btn-import").addEventListener("click", () => {
  document.getElementById("import-file").value = "";
  document.getElementById("import-auto-classify").checked = false;
  document.getElementById("import-summary").classList.add("hidden");
  openModal("import-modal");
});

document.getElementById("btn-apply-filters").addEventListener("click", () => {
  state.filters.category = document.getElementById("filter-category").value;
  state.filters.priority = document.getElementById("filter-priority").value;
  state.filters.status = document.getElementById("filter-status").value;
  state.filters.customer_id = document.getElementById("filter-customer").value.trim();
  state.page = 1;
  loadTickets();
});

document.getElementById("btn-clear-filters").addEventListener("click", () => {
  document.getElementById("filter-category").value = "";
  document.getElementById("filter-priority").value = "";
  document.getElementById("filter-status").value = "";
  document.getElementById("filter-customer").value = "";
  state.filters = { category: "", priority: "", status: "", customer_id: "" };
  state.page = 1;
  loadTickets();
});

document.getElementById("btn-prev-page").addEventListener("click", () => {
  if (state.page > 1) {
    state.page -= 1;
    loadTickets();
  }
});

document.getElementById("btn-next-page").addEventListener("click", () => {
  state.page += 1;
  loadTickets();
});

document.getElementById("page-size-select").addEventListener("change", (event) => {
  state.pageSize = Number(event.target.value);
  state.page = 1;
  loadTickets();
});

document.getElementById("btn-detail-classify").addEventListener("click", () => {
  if (activeDetailTicketId) runAutoClassify(activeDetailTicketId);
});

document.getElementById("btn-detail-edit").addEventListener("click", () => {
  if (!activeDetailTicketId) return;
  closeModal("ticket-detail-modal");
  openEditModal(activeDetailTicketId);
});

document.getElementById("btn-detail-delete").addEventListener("click", () => {
  if (activeDetailTicketId) confirmDeleteTicket(activeDetailTicketId);
});

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

function initSelects() {
  populateSelect(document.getElementById("filter-category"), CATEGORIES, { includeBlank: true, blankLabel: "All categories" });
  populateSelect(document.getElementById("filter-priority"), PRIORITIES, { includeBlank: true, blankLabel: "All priorities" });
  populateSelect(document.getElementById("filter-status"), STATUSES, { includeBlank: true, blankLabel: "All statuses" });

  populateSelect(document.getElementById("field-category"), CATEGORIES, { includeBlank: true, blankLabel: "Auto / unset" });
  populateSelect(document.getElementById("field-priority"), PRIORITIES, { includeBlank: true, blankLabel: "Auto / unset" });
  populateSelect(document.getElementById("field-status"), STATUSES);
  populateSelect(document.getElementById("field-meta-source"), SOURCES);
  populateSelect(document.getElementById("field-meta-device"), DEVICE_TYPES, { includeBlank: true, blankLabel: "Unset" });
}

initSelects();
loadTickets();
