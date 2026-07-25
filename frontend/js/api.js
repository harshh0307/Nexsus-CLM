class NexusAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  getToken() {
    return localStorage.getItem('nexus_token');
  }

  setToken(token) {
    if (token) {
      localStorage.setItem('nexus_token', token);
    } else {
      localStorage.removeItem('nexus_token');
    }
  }

  getUser() {
    const data = localStorage.getItem('nexus_user');
    return data ? JSON.parse(data) : null;
  }

  setUser(user) {
    if (user) {
      localStorage.setItem('nexus_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('nexus_user');
    }
  }

  showSpinner() {
    document.getElementById('global-spinner').style.display = 'flex';
  }

  hideSpinner() {
    document.getElementById('global-spinner').style.display = 'none';
  }

  async _fetch(method, path, body, isFile) {
    this.showSpinner();
    const headers = {};
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    let fetchBody;
    if (isFile) {
      fetchBody = body;
    } else if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      fetchBody = JSON.stringify(body);
    }
    try {
      const res = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers,
        body: fetchBody,
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { detail: text || 'Request failed' };
      }
      if (!res.ok) {
        const msg = data.detail || `Error ${res.status}`;
        throw new Error(msg);
      }
      return data;
    } finally {
      this.hideSpinner();
    }
  }

  register(email, password, name) {
    return this._fetch('POST', '/auth/register', { email, password, name });
  }

  login(email, password) {
    return this._fetch('POST', '/auth/login', { email, password });
  }

  listContracts() {
    return this._fetch('GET', '/api/contracts');
  }

  uploadContract(file, party) {
    const form = new FormData();
    form.append('file', file);
    return this._fetch('POST', `/api/contracts/upload?party=${party}`, form, true);
  }

  analyzeContract(contractId) {
    return this._fetch('POST', `/api/contracts/${contractId}/analyze`, { extraction_queries: [] });
  }

  compareContracts(companyId, clientId) {
    return this._fetch('POST', '/api/contracts/compare', { company_contract_id: companyId, client_contract_id: clientId, extraction_queries: [] });
  }

  listGuidelines() {
    return this._fetch('GET', '/api/guidelines');
  }

  uploadCompanyGuidelines(guidelines) {
    return this._fetch('POST', '/api/guidelines/company', guidelines);
  }

  uploadClientGuidelines(guidelines) {
    return this._fetch('POST', '/api/guidelines/user', guidelines);
  }

  deleteGuideline(id) {
    return this._fetch('DELETE', `/api/guidelines/${id}`);
  }

  getDashboard() {
    return this._fetch('GET', '/api/analytics/dashboard');
  }
}

const api = new NexusAPI('');
