/**
 * Dashboard visualization & metrics manager.
 * Initializes Chart.js charts, KPI cards, and What-If sandbox.
 */

let trendChartInstance = null;
let breakdownChartInstance = null;

async function initDashboard() {
  try {
    const data = await window.API.getDashboard();
    updateStatusBadge(data.agent_status);
    updateKPIs(data);
    renderTrendChart(data.records || []);
    renderBreakdownChart(data.breakdown || {});
    renderRecommendedActions(data.recommendations || []);
    initWhatIfSandbox();
    
    // Refresh icons
    if (window.lucide) {
      window.lucide.createIcons();
    }
  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
}

function updateStatusBadge(status) {
  const badge = document.getElementById('agent-status-badge');
  const text = document.getElementById('agent-status-text');
  const subtext = document.getElementById('agent-subtext');
  const banner = document.getElementById('system-banner');
  const bannerTitle = document.getElementById('banner-title');
  const bannerDesc = document.getElementById('banner-desc');

  if (!status) return;

  if (status.is_fallback) {
    badge.className = 'status-badge fallback-badge';
    text.textContent = 'Fallback Mode (Rule-Based)';
    badge.title = 'AI API key not provided. Operating via deterministic rule-based agent and real backend tools.';
    if (subtext) subtext.textContent = 'Deterministic Rule-Based Tool Engine';
    
    if (banner) {
      banner.className = 'system-banner warning';
      bannerTitle.textContent = 'Operating in Fallback Mode:';
      bannerDesc.textContent = 'AI API key not configured in .env. Full deterministic tool calling, calculators, and rule-based sustainability recommendations remain 100% functional.';
    }
  } else {
    badge.className = 'status-badge';
    text.textContent = `${status.provider_name} Active`;
    badge.title = `Autonomous tool-calling enabled via ${status.provider_name} (${status.model})`;
    if (subtext) subtext.textContent = `Powered by ${status.provider_name} with Tool Calling`;

    if (banner) {
      banner.className = 'system-banner';
      bannerTitle.textContent = `${status.provider_name} AI Agent Active:`;
      bannerDesc.textContent = `Autonomous reasoning connected to 7 deterministic campus carbon tools and SQLite memory.`;
    }
  }
}

function updateKPIs(data) {
  if (!data.has_data || !data.latest) return;

  const latest = data.latest;
  const prev = data.previous;
  const mom = data.mom_metrics;
  const breakdown = data.breakdown;

  // KPI 1: Current Monthly Footprint
  document.getElementById('kpi-current-co2e').textContent = Number(latest.total_emissions).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  document.getElementById('kpi-current-month').textContent = latest.month;

  // KPI 2: Previous Month
  if (prev) {
    document.getElementById('kpi-previous-co2e').textContent = Number(prev.total_emissions).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    document.getElementById('kpi-previous-month').textContent = prev.month;
  } else {
    document.getElementById('kpi-previous-co2e').textContent = 'N/A';
    document.getElementById('kpi-previous-month').textContent = 'None';
  }

  // KPI 3: Net MoM Delta
  if (mom && prev) {
    const diffSign = mom.absolute_change_kg_co2e > 0 ? '+' : '';
    document.getElementById('kpi-diff-co2e').textContent = `${diffSign}${mom.absolute_change_kg_co2e.toLocaleString()}`;
    
    const momBadge = document.getElementById('kpi-mom-badge');
    const pctBadge = document.getElementById('kpi-pct-change');

    const pctText = `${diffSign}${mom.percentage_change}%`;
    pctBadge.textContent = pctText;

    if (mom.trend === 'increased') {
      momBadge.className = 'badge-trend increased';
      momBadge.textContent = `▲ ${pctText} MoM`;
      pctBadge.className = 'badge-trend increased';
    } else if (mom.trend === 'decreased') {
      momBadge.className = 'badge-trend decreased';
      momBadge.textContent = `▼ ${Math.abs(mom.percentage_change)}% MoM`;
      pctBadge.className = 'badge-trend decreased';
    } else {
      momBadge.className = 'badge-trend neutral';
      momBadge.textContent = `Steady`;
      pctBadge.className = 'badge-trend neutral';
    }
  }

  // KPI 4: Largest Contributor
  if (breakdown) {
    const largest = breakdown.largest_emission_source;
    const share = breakdown.percentage_contributions ? breakdown.percentage_contributions[largest.toLowerCase()] : 0;
    document.getElementById('kpi-largest-source').textContent = largest;
    document.getElementById('kpi-largest-share').textContent = `${share}% of total footprint`;

    // Category progress bars
    const pcts = breakdown.percentage_contributions || {};
    document.getElementById('cat-elec-val').textContent = `${Number(latest.electricity_emissions).toLocaleString()} kg`;
    document.getElementById('cat-elec-bar').style.width = `${pcts.electricity || 0}%`;
    document.getElementById('cat-elec-pct').textContent = `${pcts.electricity || 0}% share`;

    document.getElementById('cat-trans-val').textContent = `${Number(latest.transportation_emissions).toLocaleString()} kg`;
    document.getElementById('cat-trans-bar').style.width = `${pcts.transportation || 0}%`;
    document.getElementById('cat-trans-pct').textContent = `${pcts.transportation || 0}% share`;

    document.getElementById('cat-waste-val').textContent = `${Number(latest.waste_emissions).toLocaleString()} kg`;
    document.getElementById('cat-waste-bar').style.width = `${pcts.waste || 0}%`;
    document.getElementById('cat-waste-pct').textContent = `${pcts.waste || 0}% share`;
  }
}

function renderTrendChart(records) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;

  const labels = records.map(r => r.month);
  const electricityData = records.map(r => r.electricity_emissions);
  const transportationData = records.map(r => r.transportation_emissions);
  const wasteData = records.map(r => r.waste_emissions);

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Electricity (Scope 2)',
          data: electricityData,
          backgroundColor: 'rgba(245, 158, 11, 0.85)',
          borderRadius: 4,
          stack: 'emissions'
        },
        {
          label: 'Transportation (Scope 1 & 3)',
          data: transportationData,
          backgroundColor: 'rgba(56, 189, 248, 0.85)',
          borderRadius: 4,
          stack: 'emissions'
        },
        {
          label: 'Waste (Scope 3)',
          data: wasteData,
          backgroundColor: 'rgba(16, 185, 129, 0.85)',
          borderRadius: 6,
          stack: 'emissions'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11, weight: '500' },
            boxWidth: 12,
            boxHeight: 12
          }
        },
        tooltip: {
          backgroundColor: '#0f191d',
          titleColor: '#ffffff',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(16, 185, 129, 0.3)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(ctx) {
              return `${ctx.dataset.label}: ${Number(ctx.parsed.y).toLocaleString()} kg CO2e`;
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
        },
        y: {
          stacked: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11 },
            callback: value => `${(value / 1000).toFixed(0)}k kg`
          }
        }
      }
    }
  });
}

function renderBreakdownChart(breakdown) {
  const ctx = document.getElementById('breakdownChart');
  if (!ctx) return;

  const elec = breakdown.electricity_emissions_kg_co2e || 0;
  const trans = breakdown.transportation_emissions_kg_co2e || 0;
  const waste = breakdown.waste_emissions_kg_co2e || 0;
  const total = breakdown.total_emissions_kg_co2e || (elec + trans + waste);

  document.getElementById('doughnut-total-val').textContent = (total / 1000).toFixed(1) + 'k';

  if (breakdownChartInstance) {
    breakdownChartInstance.destroy();
  }

  breakdownChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Electricity', 'Transportation', 'Waste'],
      datasets: [{
        data: [elec, trans, waste],
        backgroundColor: [
          '#f59e0b',
          '#38bdf8',
          '#10b981'
        ],
        borderWidth: 2,
        borderColor: '#0f191d',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11 },
            boxWidth: 10,
            padding: 12
          }
        },
        tooltip: {
          backgroundColor: '#0f191d',
          titleColor: '#ffffff',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(16, 185, 129, 0.3)',
          borderWidth: 1,
          callbacks: {
            label: function(ctx) {
              const val = Number(ctx.parsed).toLocaleString();
              const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return `${ctx.label}: ${val} kg CO2e (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

function renderRecommendedActions(actions) {
  const container = document.getElementById('actions-list');
  if (!container) return;

  if (!actions || actions.length === 0) {
    container.innerHTML = '<p class="text-dim text-sm">No actions generated yet.</p>';
    return;
  }

  container.innerHTML = actions.map(act => {
    const priorityClass = (act.priority || '').toLowerCase();
    return `
      <div class="action-item">
        <div class="action-top-row">
          <span class="action-title">${act.title}</span>
          <span class="action-priority-badge ${priorityClass}">${act.priority.toUpperCase()} PRIORITY</span>
        </div>
        <p class="action-desc">${act.description}</p>
        <div class="action-meta-row">
          <span>🎯 ${act.impact_estimate}</span>
          <span>⏱️ ${act.timeframe}</span>
        </div>
      </div>
    `;
  }).join('');
}

function initWhatIfSandbox() {
  const categorySelect = document.getElementById('sim-category');
  const pctSlider = document.getElementById('sim-pct');
  const pctDisplay = document.getElementById('sim-pct-display');
  const btnAskAgent = document.getElementById('btn-ask-agent-sim');

  async function updateSimulation() {
    const cat = categorySelect.value;
    const pct = pctSlider.value;
    pctDisplay.textContent = `${pct}%`;

    try {
      const res = await window.API.runSimulation(cat, pct);
      const red = res.simulation.estimated_monthly_reduction_kg_co2e;
      const newTot = res.simulation.estimated_new_footprint_kg_co2e;
      const pctTot = res.simulation.total_footprint_percentage_reduction;

      document.getElementById('sim-reduction-val').textContent = `-${red.toLocaleString()} kg CO₂e (-${pctTot}%)`;
      document.getElementById('sim-new-total-val').textContent = `${newTot.toLocaleString()} kg CO₂e`;
    } catch (e) {
      console.error('Simulation error:', e);
    }
  }

  categorySelect.addEventListener('change', updateSimulation);
  pctSlider.addEventListener('input', updateSimulation);
  updateSimulation();

  btnAskAgent.addEventListener('click', () => {
    const catName = categorySelect.options[categorySelect.selectedIndex].text.split(' ')[1] || categorySelect.value;
    const pct = pctSlider.value;
    const prompt = `What if ${catName.toLowerCase()} consumption decreases by ${pct}%?`;
    if (window.triggerAgentChat) {
      window.triggerAgentChat(prompt);
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

window.refreshDashboard = initDashboard;
