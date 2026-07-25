const Screens = {
  currentPage: null,
  contracts: [],

  init() {
    document.querySelectorAll('.sidebar-btn[data-page]').forEach(btn => {
      btn.addEventListener('click', () => this.navigate(btn.dataset.page));
    });

    document.getElementById('logout-btn').addEventListener('click', () => Auth.logout());

    this.setupUpload('company');
    this.setupUpload('client');

    document.getElementById('upload-guideline-company').addEventListener('click', () => this.uploadGuideline('company'));
    document.getElementById('upload-guideline-client').addEventListener('click', () => this.uploadGuideline('client'));

    document.getElementById('analyze-contract').addEventListener('change', () => {
      document.getElementById('analyze-btn').disabled = !document.getElementById('analyze-contract').value;
    });
    document.getElementById('analyze-btn').addEventListener('click', () => this.runAnalysis());

    document.getElementById('compare-company').addEventListener('change', () => this.updateCompareBtn());
    document.getElementById('compare-client').addEventListener('change', () => this.updateCompareBtn());
    document.getElementById('compare-btn').addEventListener('click', () => this.runComparison());
  },

  navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sidebar-btn[data-page]').forEach(b => b.classList.remove('active'));

    const pageEl = document.getElementById(`page-${page}`);
    if (pageEl) pageEl.classList.add('active');

    const btn = document.querySelector(`.sidebar-btn[data-page="${page}"]`);
    if (btn) btn.classList.add('active');

    this.currentPage = page;

    switch (page) {
      case 'dashboard': this.loadDashboard(); break;
      case 'contracts': this.loadContracts(); break;
      case 'guidelines': this.loadGuidelines(); break;
      case 'analyze': this.populateAnalyzeContracts(); break;
      case 'compare': this.populateCompareContracts(); break;
    }
  },

  async loadDashboard() {
    try {
      const [dashboardData, contractsData, guidelinesData] = await Promise.all([
        api.getDashboard(),
        api.listContracts(),
        api.listGuidelines(),
      ]);

      const contracts = Array.isArray(contractsData) ? contractsData : [];
      const guidelines = Array.isArray(guidelinesData) ? guidelinesData : [];
      const riskOverview = dashboardData.risk_overview || [];
      const clauseCompliance = dashboardData.clause_compliance || [];
      const contractSummary = dashboardData.contract_summary || [];

      this.animateNumber('stat-contracts', contracts.length);
      this.animateNumber('stat-guidelines', guidelines.length);

      const avgRiskEl = document.getElementById('stat-risk');
      if (riskOverview.length > 0) {
        const scores = riskOverview.map(r => r.overall_risk_score).filter(s => s !== null);
        const avg = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
        avgRiskEl.textContent = avg.toFixed(1);
        avgRiskEl.className = `stat-number ${avg > 0.7 ? 'risk-high' : avg > 0.4 ? 'risk-mid' : 'risk-low'}`;
      } else {
        avgRiskEl.textContent = '—';
        avgRiskEl.className = 'stat-number';
      }

      const compliantCount = clauseCompliance
        .filter(c => c.compliance_status === 'compliant')
        .reduce((sum, c) => sum + (c.match_count || 0), 0);
      this.animateNumber('stat-compliant', compliantCount);

      const container = document.getElementById('recent-analyses');
      if (riskOverview.length === 0) {
        container.innerHTML = '<p class="empty-state">No analyses yet. Upload a contract to get started.</p>';
        return;
      }

      let html = `<table><thead><tr>
        <th>Contract</th><th>Risk Score</th><th>Party</th><th>Date</th>
      </tr></thead><tbody>`;
      for (const a of riskOverview) {
        const name = a.file_name || 'Unknown';
        const risk = a.overall_risk_score !== null ? parseFloat(a.overall_risk_score).toFixed(2) : '—';
        const party = a.party || '—';
        const date = a.analysis_date ? new Date(a.analysis_date).toLocaleDateString() : '—';
        html += `<tr>
          <td>${this.esc(name)}</td>
          <td class="${risk > 0.7 ? 'risk-high' : risk > 0.4 ? 'risk-mid' : 'risk-low'}">${risk}</td>
          <td><span class="badge badge-${party === 'company' ? 'compliant' : 'na'}">${this.esc(party)}</span></td>
          <td>${date}</td>
        </tr>`;
      }
      html += '</tbody></table>';
      container.innerHTML = html;
    } catch (err) {
      document.getElementById('recent-analyses').innerHTML =
        `<p class="empty-state">Error loading dashboard: ${this.esc(err.message)}</p>`;
    }
  },

  animateNumber(elId, target) {
    const el = document.getElementById(elId);
    if (!el) return;
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    el.textContent = '0';
    const step = Math.max(1, Math.ceil(target / 25));
    let count = 0;
    const timer = setInterval(() => {
      count += step;
      if (count >= target) {
        count = target;
        clearInterval(timer);
      }
      el.textContent = count;
    }, 20);
  },

  setupUpload(party) {
    const zone = document.getElementById(`upload-${party}`);
    const input = document.getElementById(`file-${party}`);
    const statusEl = document.getElementById(`upload-${party}-status`);

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
      zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      if (e.dataTransfer.files.length > 0) {
        this.uploadFile(e.dataTransfer.files[0], party, statusEl);
      }
    });

    input.addEventListener('change', () => {
      if (input.files.length > 0) {
        this.uploadFile(input.files[0], party, statusEl);
        input.value = '';
      }
    });
  },

  async uploadFile(file, party, statusEl) {
    const ext = file.name.toLowerCase().split('.').pop();
    if (!['pdf', 'doc', 'docx'].includes(ext)) {
      statusEl.innerHTML = `<div class="upload-status error">Only PDF and DOC files are supported.</div>`;
      return;
    }
    statusEl.innerHTML = `<div class="upload-status" style="color:var(--text-secondary)">Uploading ${this.esc(file.name)}...</div>`;
    try {
      const result = await api.uploadContract(file, party);
      statusEl.innerHTML = `<div class="upload-status success">Uploaded: ${this.esc(result.file_name || file.name)}</div>`;
      Toast.show('Contract uploaded successfully', 'success');
      if (this.currentPage === 'contracts') this.loadContracts();
    } catch (err) {
      statusEl.innerHTML = `<div class="upload-status error">${this.esc(err.message)}</div>`;
    }
  },

  async loadContracts() {
    try {
      const data = await api.listContracts();
      this.contracts = Array.isArray(data) ? data : [];
      const container = document.getElementById('contracts-table');
      if (this.contracts.length === 0) {
        container.innerHTML = '<p class="empty-state">No contracts uploaded yet.</p>';
        return;
      }
      let html = `<table><thead><tr>
        <th>ID</th><th>Filename</th><th>Party</th><th>Status</th><th>Uploaded</th>
      </tr></thead><tbody>`;
      for (const c of this.contracts) {
        const id = c.id || '';
        const name = c.file_name || 'Unknown';
        const party = c.party || '—';
        const status = c.status || '—';
        const date = c.created_at ? new Date(c.created_at).toLocaleDateString() : '—';
        html += `<tr>
          <td style="color:var(--text-muted);font-size:0.8rem">${this.esc(String(id).slice(0, 8))}…</td>
          <td>${this.esc(name)}</td>
          <td><span class="badge badge-${party === 'company' ? 'compliant' : 'na'}">${this.esc(party)}</span></td>
          <td>${this.esc(status)}</td>
          <td>${date}</td>
        </tr>`;
      }
      html += '</tbody></table>';
      container.innerHTML = html;
    } catch (err) {
      document.getElementById('contracts-table').innerHTML =
        `<p class="empty-state">Error: ${this.esc(err.message)}</p>`;
    }
  },

  async loadGuidelines() {
    try {
      const data = await api.listGuidelines();
      const guidelines = Array.isArray(data) ? data : [];
      const container = document.getElementById('guidelines-table');
      if (guidelines.length === 0) {
        container.innerHTML = '<p class="empty-state">No guidelines defined yet.</p>';
        return;
      }
      let html = `<table><thead><tr>
        <th>Text</th><th>Type</th><th>Risk</th><th>Scope</th><th>Action</th>
      </tr></thead><tbody>`;
      for (const g of guidelines) {
        const id = g.id;
        const text = g.text || '—';
        const type = g.type || 'general';
        const risk = g.risk_level || 'medium';
        const scope = g.scope || '—';
        html += `<tr>
          <td>${this.esc(String(text).substring(0, 60))}${String(text).length > 60 ? '…' : ''}</td>
          <td><span class="badge badge-na">${this.esc(type)}</span></td>
          <td class="risk-${risk}">${this.esc(risk)}</td>
          <td><span class="badge badge-${scope === 'company' ? 'compliant' : 'na'}">${this.esc(scope)}</span></td>
          <td><button class="delete-btn" data-guideline-id="${id}" title="Delete">✕</button></td>
        </tr>`;
      }
      html += '</tbody></table>';
      container.innerHTML = html;

      container.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (confirm('Delete this guideline?')) {
            try {
              await api.deleteGuideline(btn.dataset.guidelineId);
              Toast.show('Guideline deleted', 'success');
              this.loadGuidelines();
            } catch (err) {
              Toast.show(err.message, 'error');
            }
          }
        });
      });
    } catch (err) {
      document.getElementById('guidelines-table').innerHTML =
        `<p class="empty-state">Error: ${this.esc(err.message)}</p>`;
    }
  },

  async uploadGuideline(type) {
    const textareaId = type === 'company' ? 'guideline-company' : 'guideline-client';
    const textarea = document.getElementById(textareaId);
    const raw = textarea.value.trim();
    if (!raw) {
      Toast.show('Please enter guideline JSON', 'error');
      return;
    }
    let guidelines;
    try {
      guidelines = JSON.parse(raw);
      if (!Array.isArray(guidelines)) guidelines = [guidelines];
    } catch {
      Toast.show('Invalid JSON format', 'error');
      return;
    }
    try {
      if (type === 'company') {
        await api.uploadCompanyGuidelines(guidelines);
      } else {
        await api.uploadClientGuidelines(guidelines);
      }
      Toast.show('Guidelines uploaded', 'success');
      textarea.value = '';
      this.loadGuidelines();
    } catch (err) {
      Toast.show(err.message, 'error');
    }
  },

  async populateAnalyzeContracts() {
    try {
      const data = await api.listContracts();
      this.contracts = Array.isArray(data) ? data : [];
      const select = document.getElementById('analyze-contract');
      select.innerHTML = '<option value="">— Select a contract —</option>';
      for (const c of this.contracts) {
        const name = c.file_name || c.id;
        select.innerHTML += `<option value="${c.id}">${this.esc(name)}</option>`;
      }
      document.getElementById('analyze-btn').disabled = true;
      document.getElementById('analyze-results').innerHTML = '';
    } catch (err) {
      document.getElementById('analyze-results').innerHTML =
        `<p class="empty-state">Error loading contracts: ${this.esc(err.message)}</p>`;
    }
  },

  async runAnalysis() {
    const contractId = document.getElementById('analyze-contract').value;
    if (!contractId) return;
    const resultsEl = document.getElementById('analyze-results');
    resultsEl.innerHTML = '<p class="empty-state">Analyzing contract…</p>';
    try {
      const result = await api.analyzeContract(contractId);
      this.renderAnalysisResults(result, resultsEl);
    } catch (err) {
      resultsEl.innerHTML = `<div class="result-card"><p style="color:var(--danger)">${this.esc(err.message)}</p></div>`;
    }
  },

  renderAnalysisResults(result, container) {
    const risk = result.overall_risk_score !== null ? parseFloat(result.overall_risk_score).toFixed(2) : '—';
    const riskSummary = result.risk_summary || '';
    const clauses = result.clauses || [];
    const missing = result.missing_clauses || [];
    const mismatches = result.mismatches || [];
    const partyConflicts = result.party_conflicts || [];

    let html = `<div class="result-card">
      <h3>Analysis Results</h3>
      ${riskSummary ? `<p style="color:var(--text-secondary);margin-bottom:16px;font-size:0.9rem">${this.esc(riskSummary)}</p>` : ''}
      <div class="analysis-summary">
        <div class="summary-item">
          <span class="label">Risk Score</span>
          <span class="value ${risk > 0.7 ? 'risk-high' : risk > 0.4 ? 'risk-mid' : 'risk-low'}">${risk}</span>
        </div>
        <div class="summary-item">
          <span class="label">Clauses Found</span>
          <span class="value">${clauses.length}</span>
        </div>
        <div class="summary-item">
          <span class="label">Missing</span>
          <span class="value" style="color:${missing.length > 0 ? 'var(--danger)' : 'var(--success)'}">${missing.length}</span>
        </div>
        <div class="summary-item">
          <span class="label">Mismatches</span>
          <span class="value" style="color:${mismatches.length > 0 ? 'var(--warning)' : 'var(--success)'}">${mismatches.length}</span>
        </div>
        <div class="summary-item">
          <span class="label">Conflicts</span>
          <span class="value" style="color:${partyConflicts.length > 0 ? 'var(--warning)' : 'var(--success)'}">${partyConflicts.length}</span>
        </div>
      </div>`;

    if (clauses.length > 0) {
      html += `<div class="section-title">Extracted Clauses</div>`;
      for (const clause of clauses) {
        const text = clause.text_content || clause.summary || '';
        html += `<div class="clause-item">
          <div class="clause-header">
            <span class="clause-type">${this.esc(clause.clause_type || 'Clause')}</span>
            ${clause.company_guideline_matches && clause.company_guideline_matches.length > 0
              ? `<span class="badge ${clause.company_guideline_matches.some(m => m.compliance_status === 'compliant') ? 'badge-compliant' : 'badge-noncompliant'}">Analyzed</span>`
              : '<span class="badge badge-na">No match</span>'}
          </div>
          <div class="clause-text">${this.esc(text.substring(0, 200))}${text.length > 200 ? '…' : ''}</div>
        </div>`;
      }
    }

    if (missing.length > 0) {
      html += `<div class="section-title" style="color:var(--danger)">Missing Clauses</div>`;
      for (const m of missing) {
        html += `<div class="clause-item">
          <div class="clause-header">
            <span class="clause-type">${this.esc(m.clause_type || 'Clause')}</span>
            <span class="badge badge-${m.severity === 'high' ? 'noncompliant' : 'partial'}">${this.esc(m.severity || 'medium')}</span>
          </div>
          <div class="clause-text">${this.esc(m.reason || m.recommendation || '')}</div>
        </div>`;
      }
    }

    if (mismatches.length > 0) {
      html += `<div class="section-title" style="color:var(--warning)">Mismatches with Guidelines</div>`;
      for (const mm of mismatches) {
        html += `<div class="gap-item">
          <div class="gap-header">
            <span class="gap-party">${this.esc(mm.issue || 'Issue')}</span>
            <span class="badge badge-${mm.severity === 'high' ? 'noncompliant' : 'partial'}">${this.esc(mm.severity || 'medium')}</span>
          </div>
          <div class="gap-detail">Contract: ${this.esc(mm.contract_says || '')}</div>
          ${mm.company_requirement ? `<div class="gap-detail">Company: ${this.esc(mm.company_requirement)}</div>` : ''}
          ${mm.user_requirement ? `<div class="gap-detail">Client: ${this.esc(mm.user_requirement)}</div>` : ''}
          ${mm.recommendation ? `<div class="gap-detail" style="color:var(--accent);margin-top:4px">${this.esc(mm.recommendation)}</div>` : ''}
        </div>`;
      }
    }

    if (partyConflicts.length > 0) {
      html += `<div class="section-title" style="color:var(--warning)">Party Conflicts</div>`;
      for (const pc of partyConflicts) {
        html += `<div class="gap-item">
          <div class="gap-header">
            <span class="gap-party">${this.esc(pc.topic || 'Topic')}</span>
            <span class="badge badge-partial">${this.esc(pc.conflict_type || 'conflict')}</span>
          </div>
          <div class="gap-detail">Company: ${this.esc(pc.company_requires || '')}</div>
          <div class="gap-detail">Client: ${this.esc(pc.user_requires || '')}</div>
          ${pc.resolution_suggestion ? `<div class="gap-detail" style="color:var(--accent);margin-top:4px">${this.esc(pc.resolution_suggestion)}</div>` : ''}
        </div>`;
      }
    }

    html += '</div>';
    container.innerHTML = html;
  },

  async populateCompareContracts() {
    try {
      const data = await api.listContracts();
      this.contracts = Array.isArray(data) ? data : [];
      const companySelect = document.getElementById('compare-company');
      const clientSelect = document.getElementById('compare-client');
      companySelect.innerHTML = '<option value="">— Select company contract —</option>';
      clientSelect.innerHTML = '<option value="">— Select client contract —</option>';
      for (const c of this.contracts) {
        const name = c.file_name || c.id;
        const opt = `<option value="${c.id}">${this.esc(name)}</option>`;
        companySelect.innerHTML += opt;
        clientSelect.innerHTML += opt;
      }
      this.updateCompareBtn();
      document.getElementById('compare-results').innerHTML = '';
    } catch (err) {
      document.getElementById('compare-results').innerHTML =
        `<p class="empty-state">Error loading contracts: ${this.esc(err.message)}</p>`;
    }
  },

  updateCompareBtn() {
    const company = document.getElementById('compare-company').value;
    const client = document.getElementById('compare-client').value;
    document.getElementById('compare-btn').disabled = !company || !client;
  },

  async runComparison() {
    const companyId = document.getElementById('compare-company').value;
    const clientId = document.getElementById('compare-client').value;
    if (!companyId || !clientId) return;
    const resultsEl = document.getElementById('compare-results');
    resultsEl.innerHTML = '<p class="empty-state">Comparing contracts…</p>';
    try {
      const result = await api.compareContracts(companyId, clientId);
      this.renderComparisonResults(result, resultsEl);
    } catch (err) {
      resultsEl.innerHTML = `<div class="result-card"><p style="color:var(--danger)">${this.esc(err.message)}</p></div>`;
    }
  },

  renderComparisonResults(result, container) {
    const crossGaps = result.cross_gaps || [];
    const termConflicts = result.term_conflicts || [];
    const risk = result.overall_risk_score !== null ? parseFloat(result.overall_risk_score).toFixed(2) : '—';
    const riskSummary = result.risk_summary || '';

    let html = `<div class="result-card">
      <h3>Comparison Results</h3>
      ${riskSummary ? `<p style="color:var(--text-secondary);margin-bottom:16px;font-size:0.9rem">${this.esc(riskSummary)}</p>` : ''}
      <div class="analysis-summary">
        <div class="summary-item">
          <span class="label">Risk Score</span>
          <span class="value ${risk > 0.7 ? 'risk-high' : risk > 0.4 ? 'risk-mid' : 'risk-low'}">${risk}</span>
        </div>
        <div class="summary-item">
          <span class="label">Cross-Party Gaps</span>
          <span class="value" style="color:${crossGaps.length > 0 ? 'var(--danger)' : 'var(--success)'}">${crossGaps.length}</span>
        </div>
        <div class="summary-item">
          <span class="label">Term Conflicts</span>
          <span class="value" style="color:${termConflicts.length > 0 ? 'var(--warning)' : 'var(--success)'}">${termConflicts.length}</span>
        </div>
      </div>`;

    if (crossGaps.length > 0) {
      html += `<div class="section-title" style="color:var(--danger)">Cross-Party Gaps</div>`;
      for (const gap of crossGaps) {
        html += `<div class="gap-item">
          <div class="gap-header">
            <span class="gap-party">${this.esc(gap.clause_type || 'Clause')}</span>
            <span class="badge badge-noncompliant">Missing from ${this.esc(gap.missing_from || '?')}</span>
          </div>
          <div class="gap-detail">Present in ${this.esc(gap.present_in || '?')}</div>
          ${gap.company_text ? `<div class="gap-detail">Company text: ${this.esc(gap.company_text.substring(0, 200))}</div>` : ''}
          ${gap.client_text ? `<div class="gap-detail">Client text: ${this.esc(gap.client_text.substring(0, 200))}</div>` : ''}
          ${gap.recommendation ? `<div class="gap-detail" style="color:var(--accent);margin-top:4px">${this.esc(gap.recommendation)}</div>` : ''}
        </div>`;
      }
    }

    if (termConflicts.length > 0) {
      html += `<div class="section-title" style="color:var(--warning)">Term Conflicts</div>`;
      for (const tc of termConflicts) {
        html += `<div class="gap-item">
          <div class="gap-header">
            <span class="gap-party">${this.esc(tc.clause_type || 'Term')}</span>
            <span class="badge badge-partial">${this.esc(tc.severity || 'conflict')}</span>
          </div>
          <div class="gap-detail">Company: ${this.esc((tc.company_term || '').substring(0, 200))}</div>
          <div class="gap-detail">Client: ${this.esc((tc.client_term || '').substring(0, 200))}</div>
          ${tc.conflict_description ? `<div class="gap-detail" style="color:var(--warning);margin-top:4px">${this.esc(tc.conflict_description)}</div>` : ''}
          ${tc.resolution_suggestion ? `<div class="gap-detail" style="color:var(--accent);margin-top:4px">${this.esc(tc.resolution_suggestion)}</div>` : ''}
        </div>`;
      }
    }

    if (crossGaps.length === 0 && termConflicts.length === 0) {
      html += `<div style="text-align:center;padding:24px;color:var(--success)">
        <p style="font-size:1.2rem;font-weight:600">✓ No Gaps or Conflicts Found</p>
        <p style="color:var(--text-secondary);margin-top:4px">The company and client contracts are well-aligned.</p>
      </div>`;
    }

    html += '</div>';
    container.innerHTML = html;
  },

  esc(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  },
};

const Toast = {
  show(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.classList.add('toast-out');
      setTimeout(() => el.remove(), 300);
    }, 2800);
  },
};

document.addEventListener('DOMContentLoaded', () => Auth.init());
