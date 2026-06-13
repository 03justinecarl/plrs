// Dashboard Charts via Chart.js
async function loadCharts() {
  const res = await fetch('/api/progress');
  const data = await res.json();

  // Line Chart – Weekly Progress
  const lineCtx = document.getElementById('progressChart');
  if (lineCtx && data.weeks.length) {
    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: data.weeks,
        datasets: [{
          label: 'Avg Score (%)',
          data: data.scores,
          borderColor: '#7b1113',
          backgroundColor: 'rgba(123,17,19,0.08)',
          borderWidth: 2.5,
          pointBackgroundColor: '#7b1113',
          pointRadius: 5,
          tension: 0.4,
          fill: true,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#f0f0f0' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Bar Chart – Subject Performance
  const barCtx = document.getElementById('subjectChart');
  if (barCtx && data.subjects.length) {
    const colors = data.subject_scores.map(s =>
      s >= 75 ? '#28a745' : s >= 60 ? '#f0ad4e' : '#d9534f'
    );
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: data.subjects,
        datasets: [{
          label: 'Score (%)',
          data: data.subject_scores,
          backgroundColor: colors,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#f0f0f0' } },
          x: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', loadCharts);
