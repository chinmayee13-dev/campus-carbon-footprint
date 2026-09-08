/**
 * API client for Campus Carbon Management Agent.
 */

const API_BASE = '/api';

const API = {
  async getStatus() {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) throw new Error('Failed to fetch agent status');
    return await res.json();
  },

  async getDashboard() {
    const res = await fetch(`${API_BASE}/dashboard`);
    if (!res.ok) throw new Error('Failed to load dashboard data');
    return await res.json();
  },

  async getEmissionFactors() {
    const res = await fetch(`${API_BASE}/emission-factors`);
    if (!res.ok) throw new Error('Failed to load emission factors');
    return await res.json();
  },

  async sendChatMessage(message, history = []) {
    const res = await fetch(`${API_BASE}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to send message to agent');
    }
    return await res.json();
  },

  async recordCampusData(payload) {
    const res = await fetch(`${API_BASE}/campus-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to record campus data');
    }
    return await res.json();
  },

  async runSimulation(category, reduction_percentage) {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, reduction_percentage: Number(reduction_percentage) })
    });
    if (!res.ok) throw new Error('Simulation calculation failed');
    return await res.json();
  }
};

window.API = API;
