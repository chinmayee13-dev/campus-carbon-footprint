/**
 * Campus Data Entry Modal & Emission Factors Reference Viewer.
 */

// Factors cache for instant client preview
let factorsMap = {
  electricity: 0.385,
  car: 0.171,
  motorcycle: 0.103,
  bus_fuel: 2.680,
  organic_waste: 0.450,
  plastic_waste: 2.100,
  paper_waste: 0.950
};

function initDataEntry() {
  const modalDataEntry = document.getElementById('modal-data-entry');
  const btnOpenModal = document.getElementById('btn-open-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelModal = document.getElementById('btn-cancel-modal');
  const formCampusData = document.getElementById('form-campus-data');

  // Emission Factors Modal elements
  const modalFactors = document.getElementById('modal-factors');
  const btnOpenFactors = document.getElementById('btn-open-factors');
  const btnCloseFactors = document.getElementById('btn-close-factors');

  // Set default month to current or next month
  const inputMonth = document.getElementById('input-month');
  if (inputMonth) {
    const d = new Date();
    const curYear = d.getFullYear();
    const curMonth = String(d.getMonth() + 1).padStart(2, '0');
    inputMonth.value = `${curYear}-${curMonth}`;
  }

  // Open / Close Data Entry Modal
  btnOpenModal.addEventListener('click', () => {
    modalDataEntry.classList.add('active');
    updatePreview();
  });

  const closeModal = () => modalDataEntry.classList.remove('active');
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);

  // Close on outside click
  modalDataEntry.addEventListener('click', (e) => {
    if (e.target === modalDataEntry) closeModal();
  });

  // Attach live calculation listener to all input fields
  const liveInputs = [
    'input-kwh', 'input-cars', 'input-car-dist', 'input-motos',
    'input-moto-dist', 'input-bus-fuel', 'input-waste-organic',
    'input-waste-plastic', 'input-waste-paper'
  ];

  liveInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', updatePreview);
    }
  });

  // Form Submission
  formCampusData.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('btn-save-data');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Saving to SQLite...</span>';

    try {
      const payload = {
        month: document.getElementById('input-month').value.trim(),
        electricity_kwh: parseFloat(document.getElementById('input-kwh').value) || 0,
        cars: parseInt(document.getElementById('input-cars').value, 10) || 0,
        car_distance: parseFloat(document.getElementById('input-car-dist').value) || 0,
        motorcycles: parseInt(document.getElementById('input-motos').value, 10) || 0,
        motorcycle_distance: parseFloat(document.getElementById('input-moto-dist').value) || 0,
        bus_fuel: parseFloat(document.getElementById('input-bus-fuel').value) || 0,
        organic_waste: parseFloat(document.getElementById('input-waste-organic').value) || 0,
        plastic_waste: parseFloat(document.getElementById('input-waste-plastic').value) || 0,
        paper_waste: parseFloat(document.getElementById('input-waste-paper').value) || 0
      };

      const res = await window.API.recordCampusData(payload);
      closeModal();
      formCampusData.reset();

      // Refresh dashboard
      if (window.refreshDashboard) {
        await window.refreshDashboard();
      }

      // Trigger chat notification
      if (window.triggerAgentChat) {
        window.triggerAgentChat(`We just recorded new campus data for ${payload.month}. Can you analyze our new carbon footprint?`);
      }
    } catch (err) {
      alert(`Error saving campus data: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i data-lucide="save"></i><span>Calculate & Save to SQLite</span>';
      if (window.lucide) window.lucide.createIcons();
    }
  });

  // Open / Close Factors Modal
  btnOpenFactors.addEventListener('click', async () => {
    modalFactors.classList.add('active');
    await loadFactorsTable();
  });

  const closeFactors = () => modalFactors.classList.remove('active');
  btnCloseFactors.addEventListener('click', closeFactors);
  modalFactors.addEventListener('click', (e) => {
    if (e.target === modalFactors) closeFactors();
  });
}

function updatePreview() {
  const kwh = parseFloat(document.getElementById('input-kwh')?.value) || 0;
  const cars = parseInt(document.getElementById('input-cars')?.value, 10) || 0;
  const carDist = parseFloat(document.getElementById('input-car-dist')?.value) || 0;
  const motos = parseInt(document.getElementById('input-motos')?.value, 10) || 0;
  const motoDist = parseFloat(document.getElementById('input-moto-dist')?.value) || 0;
  const busFuel = parseFloat(document.getElementById('input-bus-fuel')?.value) || 0;
  const orgWaste = parseFloat(document.getElementById('input-waste-organic')?.value) || 0;
  const plasWaste = parseFloat(document.getElementById('input-waste-plastic')?.value) || 0;
  const papWaste = parseFloat(document.getElementById('input-waste-paper')?.value) || 0;

  const elecCo2 = kwh * factorsMap.electricity;
  const transCo2 = (cars * carDist * factorsMap.car) + (motos * motoDist * factorsMap.motorcycle) + (busFuel * factorsMap.bus_fuel);
  const wasteCo2 = (orgWaste * factorsMap.organic_waste) + (plasWaste * factorsMap.plastic_waste) + (papWaste * factorsMap.paper_waste);
  const totalCo2 = elecCo2 + transCo2 + wasteCo2;

  document.getElementById('preview-elec').textContent = elecCo2.toLocaleString(undefined, { maximumFractionDigits: 1 });
  document.getElementById('preview-trans').textContent = transCo2.toLocaleString(undefined, { maximumFractionDigits: 1 });
  document.getElementById('preview-waste').textContent = wasteCo2.toLocaleString(undefined, { maximumFractionDigits: 1 });
  document.getElementById('preview-total').textContent = `${totalCo2.toLocaleString(undefined, { maximumFractionDigits: 1 })} kg CO₂e`;
}

async function loadFactorsTable() {
  const tbody = document.getElementById('factors-table-body');
  if (!tbody) return;

  try {
    const data = await window.API.getEmissionFactors();
    const factors = data.factors || {};

    const rows = [
      {
        cat: 'Electricity (Grid)',
        scope: 'Scope 2',
        factor: factors.electricity?.kwh_factor || 0.385,
        unit: 'kg CO2e / kWh',
        src: factors.electricity?.source || 'US EPA eGRID'
      },
      {
        cat: 'Passenger Cars',
        scope: 'Scope 3 (Commuting)',
        factor: factors.transportation?.car_km_factor || 0.171,
        unit: 'kg CO2e / km',
        src: factors.transportation?.source || 'UK DEFRA / EPA GHGRP'
      },
      {
        cat: 'Motorcycles / Scooters',
        scope: 'Scope 3 (Commuting)',
        factor: factors.transportation_motorcycle?.motorcycle_km_factor || 0.103,
        unit: 'kg CO2e / km',
        src: factors.transportation_motorcycle?.source || 'UK DEFRA'
      },
      {
        cat: 'Campus Diesel Buses',
        scope: 'Scope 1 (Fleet)',
        factor: factors.transportation_bus?.bus_fuel_liter_factor || 2.680,
        unit: 'kg CO2e / liter',
        src: factors.transportation_bus?.source || 'GHG Protocol Diesel'
      },
      {
        cat: 'Organic / Food Waste',
        scope: 'Scope 3 (Landfill)',
        factor: factors.waste_organic?.kg_factor || 0.450,
        unit: 'kg CO2e / kg',
        src: factors.waste_organic?.source || 'US EPA WARM v15'
      },
      {
        cat: 'Plastic Waste',
        scope: 'Scope 3 (Disposal)',
        factor: factors.waste_plastic?.kg_factor || 2.100,
        unit: 'kg CO2e / kg',
        src: factors.waste_plastic?.source || 'US EPA WARM v15'
      },
      {
        cat: 'Paper & Cardboard',
        scope: 'Scope 3 (Disposal)',
        factor: factors.waste_paper?.kg_factor || 0.950,
        unit: 'kg CO2e / kg',
        src: factors.waste_paper?.source || 'US EPA WARM v15'
      }
    ];

    tbody.innerHTML = rows.map(r => `
      <tr>
        <td><strong>${r.cat}</strong></td>
        <td><span class="badge-month">${r.scope}</span></td>
        <td><code>${r.factor}</code></td>
        <td>${r.unit}</td>
        <td><small class="text-dim">${r.src}</small></td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#f43f5e;">Failed to load emission factors: ${err.message}</td></tr>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initDataEntry();
});
