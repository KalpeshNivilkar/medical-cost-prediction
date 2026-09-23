/* ═══════════════════════════════════════════════════════════════════════
   MedCostAI — Frontend Script
   Features:
   - BMI live tag
   - Smoker hint
   - Insurance plan toggle
   - Form validation
   - Submit loader
   - Result cost animation
   - Scroll animations
   - Alcohol + doctor visit hints
   - Gemini cost-driver chart
   - Download report button loading
════════════════════════════════════════════════════════════════════════ */
'use strict';

/* ─────────────────────────────────────────────────────────────────────
   Helper: safe selector
───────────────────────────────────────────────────────────────────── */
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);


/* ─────────────────────────────────────────────────────────────────────
   BMI Live Helper
───────────────────────────────────────────────────────────────────── */
const bmiInput = document.getElementById('bmi');
const bmiTag = document.getElementById('bmiTag');

function updateBMITag() {
  if (!bmiInput || !bmiTag) return;

  const val = parseFloat(bmiInput.value);

  if (isNaN(val) || bmiInput.value === '') {
    bmiTag.textContent = '';
    bmiTag.className = 'bmi-tag';
    return;
  }

  let label;
  let cls;

  if (val < 18.5) {
    label = '⬇ Underweight (< 18.5)';
    cls = 'bmi-underweight';
  } else if (val < 25) {
    label = '✅ Normal weight (18.5–25)';
    cls = 'bmi-normal';
  } else if (val < 30) {
    label = '⚠️ Overweight (25–30)';
    cls = 'bmi-overweight';
  } else {
    label = '🔴 Obese (30+)';
    cls = 'bmi-obese';
  }

  bmiTag.textContent = label;
  bmiTag.className = `bmi-tag ${cls}`;
}

if (bmiInput) {
  bmiInput.addEventListener('input', updateBMITag);
  updateBMITag();
}


/* ─────────────────────────────────────────────────────────────────────
   Smoker Hint
───────────────────────────────────────────────────────────────────── */
const smokerSelect = document.getElementById('smoker');
const smokerHint = document.getElementById('smokerHint');

function updateSmokerHint() {
  if (!smokerSelect || !smokerHint) return;

  if (smokerSelect.value === 'Yes') {
    smokerHint.textContent = '⚠️ Smoking is one of the strongest medical cost drivers.';
    smokerHint.style.color = '#dc2626';
    smokerHint.style.fontWeight = '600';
  } else if (smokerSelect.value === 'No') {
    smokerHint.textContent = '✅ Non-smoker status usually lowers predicted cost risk.';
    smokerHint.style.color = '#16a34a';
    smokerHint.style.fontWeight = '500';
  } else {
    smokerHint.textContent = '';
  }
}

if (smokerSelect) {
  smokerSelect.addEventListener('change', updateSmokerHint);
  updateSmokerHint();
}


/* ─────────────────────────────────────────────────────────────────────
   Insurance Plan Card Toggle
───────────────────────────────────────────────────────────────────── */
const planCards = document.querySelectorAll('.plan-card');
const planRadios = document.querySelectorAll('.plan-radio');

function updateActivePlanCard() {
  planCards.forEach(card => {
    const radio = card.querySelector('.plan-radio');

    if (radio && radio.checked) {
      card.classList.add('plan-card--active');
    } else {
      card.classList.remove('plan-card--active');
    }
  });
}

planCards.forEach(card => {
  card.addEventListener('click', () => {
    const radio = card.querySelector('.plan-radio');

    if (radio) {
      radio.checked = true;
    }

    updateActivePlanCard();
  });
});

planRadios.forEach(radio => {
  radio.addEventListener('change', updateActivePlanCard);
});

updateActivePlanCard();


/* ─────────────────────────────────────────────────────────────────────
   Inline Form Error Helpers
───────────────────────────────────────────────────────────────────── */
function showInlineError(inputEl, msg) {
  if (!inputEl) return;

  inputEl.style.borderColor = '#dc2626';
  inputEl.style.boxShadow = '0 0 0 3px rgba(220,38,38,.12)';

  const parent = inputEl.parentElement;
  if (!parent) return;

  let existing = parent.querySelector('.inline-err');

  if (!existing) {
    const err = document.createElement('span');
    err.className = 'inline-err';
    err.style.cssText = `
      font-size:11.5px;
      color:#dc2626;
      margin-top:3px;
      display:block;
      line-height:1.4;
    `;
    err.textContent = msg;
    parent.appendChild(err);
  } else {
    existing.textContent = msg;
  }
}

function clearInlineError(inputEl) {
  if (!inputEl) return;

  inputEl.style.borderColor = '';
  inputEl.style.boxShadow = '';

  const parent = inputEl.parentElement;
  if (!parent) return;

  const existing = parent.querySelector('.inline-err');
  if (existing) existing.remove();
}


/* ─────────────────────────────────────────────────────────────────────
   Form Validation
───────────────────────────────────────────────────────────────────── */
const predForm = document.getElementById('predForm');
const submitBtn = document.getElementById('submitBtn');

function validateNumberField(id, label, min, max, integerOnly = false) {
  const el = document.getElementById(id);
  if (!el) return true;

  clearInlineError(el);

  const value = integerOnly ? parseInt(el.value, 10) : parseFloat(el.value);

  if (!el.value || isNaN(value)) {
    showInlineError(el, `${label} is required.`);
    return false;
  }

  if (value < min || value > max) {
    showInlineError(el, `${label} must be between ${min} and ${max}.`);
    return false;
  }

  return true;
}

function validateRequiredSelect(id, label) {
  const el = document.getElementById(id);
  if (!el) return true;

  clearInlineError(el);

  if (!el.value) {
    showInlineError(el, `Please select ${label}.`);
    return false;
  }

  return true;
}

function validateForm() {
  let valid = true;

  valid = validateNumberField('age', 'Age', 18, 120, true) && valid;
  valid = validateNumberField('bmi', 'BMI', 10, 70, false) && valid;
  valid = validateNumberField('children', 'Children', 0, 15, true) && valid;
  valid = validateNumberField('annual_income_usd', 'Annual income', 0, 100000000, false) && valid;
  valid = validateNumberField('chronic_diseases', 'Chronic diseases', 0, 10, true) && valid;
  valid = validateNumberField('doctor_visits_per_year', 'Doctor visits per year', 0, 60, true) && valid;
  valid = validateNumberField('hospitalizations_last_year', 'Hospitalisations last year', 0, 20, true) && valid;
  valid = validateNumberField('alcohol_consumption_per_week', 'Alcohol consumption', 0, 80, true) && valid;

  valid = validateRequiredSelect('gender', 'gender') && valid;
  valid = validateRequiredSelect('region', 'region') && valid;
  valid = validateRequiredSelect('occupation', 'occupation') && valid;
  valid = validateRequiredSelect('smoker', 'smoker status') && valid;
  valid = validateRequiredSelect('exercise_level', 'exercise level') && valid;

  const anyPlan = document.querySelector('.plan-radio:checked');

  if (!anyPlan) {
    const planSection = document.querySelector('.fields-grid--plans');

    if (planSection) {
      let err = planSection.querySelector('.inline-err');

      if (!err) {
        err = document.createElement('span');
        err.className = 'inline-err';
        err.style.cssText = `
          font-size:11.5px;
          color:#dc2626;
          grid-column:1/-1;
          display:block;
        `;
        err.textContent = 'Please select an insurance plan.';
        planSection.appendChild(err);
      }
    }

    valid = false;
  }

  return valid;
}

if (predForm) {
  predForm.addEventListener('submit', function(e) {
    const valid = validateForm();

    if (!valid) {
      e.preventDefault();

      const firstErr = document.querySelector('.inline-err');
      if (firstErr) {
        firstErr.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }

      return;
    }

    if (submitBtn) {
      submitBtn.innerHTML = `
        <span class="btn-icon">⏳</span>
        <span class="btn-text">Analysing with AI...</span>
      `;
      submitBtn.disabled = true;
      submitBtn.style.opacity = '0.85';
      submitBtn.style.cursor = 'not-allowed';
    }
  });

  predForm.querySelectorAll('.field-input').forEach(el => {
    el.addEventListener('input', () => clearInlineError(el));
    el.addEventListener('change', () => clearInlineError(el));
  });
}


/* ─────────────────────────────────────────────────────────────────────
   Result Page: Animate Cost Number
───────────────────────────────────────────────────────────────────── */
const costEl = document.querySelector('.result-cost');

if (costEl) {
  const raw = costEl.textContent.replace(/[$,]/g, '');
  const target = parseFloat(raw);

  if (!isNaN(target)) {
    const duration = 1200;
    const start = performance.now();

    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);

      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;

      costEl.textContent = '$' + current.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });

      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }
}


/* ─────────────────────────────────────────────────────────────────────
   Result Page: Gemini Cost Driver Chart
   Works with result.html:
   <script>
     window.costDriverData = {{ chart_data | safe }};
   </script>
───────────────────────────────────────────────────────────────────── */
function initCostDriverChart() {
  const chartCanvas = document.getElementById('costDriverChart');

  if (!chartCanvas) return;

  if (typeof Chart === 'undefined') {
    console.warn('Chart.js is not loaded.');
    return;
  }

  let chartData = [];

  if (Array.isArray(window.costDriverData)) {
    chartData = window.costDriverData;
  } else {
    try {
      const embeddedData = document.getElementById('costDriverData');
      if (embeddedData) {
        chartData = JSON.parse(embeddedData.textContent);
      }
    } catch (err) {
      console.warn('Could not parse chart data:', err);
    }
  }

  if (!Array.isArray(chartData) || chartData.length === 0) {
    chartData = [
      { driver: 'Smoking', score: 0 },
      { driver: 'BMI', score: 0 },
      { driver: 'Chronic Diseases', score: 0 },
      { driver: 'Hospitalizations', score: 0 },
      { driver: 'Doctor Visits', score: 0 },
      { driver: 'Exercise', score: 0 },
      { driver: 'Alcohol', score: 0 }
    ];
  }

  const labels = chartData.map(item => item.driver);
  const scores = chartData.map(item => Number(item.score) || 0);

  new Chart(chartCanvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Cost Driver Score',
        data: scores,
        borderWidth: 1,
        borderRadius: 10,
        maxBarThickness: 55
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 900,
        easing: 'easeOutQuart'
      },
      plugins: {
        legend: {
          display: true,
          labels: {
            boxWidth: 14,
            font: {
              size: 12,
              weight: '600'
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.raw}/100 impact score`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20
          },
          title: {
            display: true,
            text: 'Impact Score'
          }
        },
        x: {
          ticks: {
            font: {
              size: 11
            }
          }
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', initCostDriverChart);


/* ─────────────────────────────────────────────────────────────────────
   Download Report Button State
───────────────────────────────────────────────────────────────────── */
const downloadForm = document.querySelector('form[action="/download-report"]');
const downloadBtn = document.querySelector('.download-btn');

if (downloadForm && downloadBtn) {
  downloadForm.addEventListener('submit', function() {
    const oldText = downloadBtn.innerHTML;

    downloadBtn.innerHTML = `
      <span>Preparing Report...</span>
      <span>⏳</span>
    `;

    downloadBtn.disabled = true;
    downloadBtn.style.opacity = '0.85';
    downloadBtn.style.cursor = 'not-allowed';

    setTimeout(() => {
      downloadBtn.innerHTML = oldText;
      downloadBtn.disabled = false;
      downloadBtn.style.opacity = '';
      downloadBtn.style.cursor = '';
    }, 1800);
  });
}


/* ─────────────────────────────────────────────────────────────────────
   Alcohol Units Helper
───────────────────────────────────────────────────────────────────── */
const alcInput = document.getElementById('alcohol_consumption_per_week');

if (alcInput) {
  alcInput.addEventListener('input', function() {
    const v = parseInt(this.value, 10);

    let hint = this.parentElement.querySelector('.field-hint');

    if (!hint) {
      hint = document.createElement('span');
      hint.className = 'field-hint';
      this.parentElement.appendChild(hint);
    }

    if (isNaN(v)) {
      hint.textContent = '1 unit ≈ 1 standard drink';
      hint.style.color = '';
      return;
    }

    if (v === 0) {
      hint.textContent = '✅ No alcohol consumption';
      hint.style.color = '#16a34a';
    } else if (v <= 7) {
      hint.textContent = '✅ Low to moderate usage';
      hint.style.color = '#16a34a';
    } else if (v <= 14) {
      hint.textContent = '⚠️ Moderate to heavy usage';
      hint.style.color = '#d97706';
    } else {
      hint.textContent = '🔴 Heavy consumption pattern';
      hint.style.color = '#dc2626';
    }
  });
}


/* ─────────────────────────────────────────────────────────────────────
   Doctor Visits Helper
───────────────────────────────────────────────────────────────────── */
const dvInput = document.getElementById('doctor_visits_per_year');

if (dvInput) {
  dvInput.addEventListener('input', function() {
    const v = parseInt(this.value, 10);

    let hint = this.parentElement.querySelector('.field-hint');

    if (!hint) {
      hint = document.createElement('span');
      hint.className = 'field-hint';
      this.parentElement.appendChild(hint);
    }

    if (isNaN(v)) {
      hint.textContent = 'Outpatient consultations per year';
      hint.style.color = '';
      return;
    }

    if (v <= 2) {
      hint.textContent = '✅ Low healthcare utilisation';
      hint.style.color = '#16a34a';
    } else if (v <= 7) {
      hint.textContent = '📋 Moderate healthcare utilisation';
      hint.style.color = '#d97706';
    } else {
      hint.textContent = '⚠️ High healthcare utilisation';
      hint.style.color = '#dc2626';
    }
  });
}


/* ─────────────────────────────────────────────────────────────────────
   Smooth Fade-in Animations
───────────────────────────────────────────────────────────────────── */
const observerOptions = {
  threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.form-section, .result-card').forEach((el, i) => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(18px)';
  el.style.transition = `
    opacity 0.45s ease ${i * 0.06}s,
    transform 0.45s ease ${i * 0.06}s
  `;

  observer.observe(el);
});


/* ─────────────────────────────────────────────────────────────────────
   Small UX: Copy report text if button exists
───────────────────────────────────────────────────────────────────── */
const copyReportBtn = document.getElementById('copyReportBtn');

if (copyReportBtn) {
  copyReportBtn.addEventListener('click', async () => {
    const reportField = document.querySelector('textarea[name="report_text"]');

    if (!reportField) return;

    try {
      await navigator.clipboard.writeText(reportField.value);
      copyReportBtn.textContent = 'Copied ✅';

      setTimeout(() => {
        copyReportBtn.textContent = 'Copy Report';
      }, 1500);
    } catch (err) {
      console.warn('Copy failed:', err);
    }
  });
}