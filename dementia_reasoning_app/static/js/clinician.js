const socket = io();
const averageScoreEl = document.getElementById("average-score");
const latestScoreEl = document.getElementById("latest-score");
const averageMetricsEl = document.getElementById("average-metrics");
const historyTableEl = document.getElementById("history-table");
const chartCanvas = document.getElementById("score-chart");

let chartInstance;

function ensureChart() {
  if (chartInstance) {
    return chartInstance;
  }

  chartInstance = new Chart(chartCanvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Reasoning Score",
          data: [],
          tension: 0.35,
          borderColor: "#4338ca",
          backgroundColor: "rgba(67, 56, 202, 0.2)",
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          min: 0,
          max: 100,
        },
      },
    },
  });

  return chartInstance;
}

function renderMetrics(metrics = {}) {
  averageMetricsEl.innerHTML = "";
  Object.entries(metrics).forEach(([metric, value]) => {
    if (metric === "score" || metric === "overall") {
      return;
    }
    const element = document.createElement("div");
    element.className = "metric";
    element.innerHTML = `
      <span class="metric-title">${metric.replace(/_/g, " ")}</span>
      <span class="metric-value">${value}</span>
    `;
    averageMetricsEl.appendChild(element);
  });
}

function renderHistory(history = []) {
  historyTableEl.innerHTML = "";
  history
    .slice()
    .reverse()
    .forEach((entry) => {
      const row = document.createElement("tr");
      const timeCell = document.createElement("td");
      const transcriptCell = document.createElement("td");
      const scoreCell = document.createElement("td");
      const insightsCell = document.createElement("td");

      const date = new Date(entry.timestamp);
      timeCell.textContent = date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      transcriptCell.textContent = entry.transcript;
      scoreCell.textContent = entry.score ?? "–";
      insightsCell.textContent = entry.insights || "";

      row.appendChild(timeCell);
      row.appendChild(transcriptCell);
      row.appendChild(scoreCell);
      row.appendChild(insightsCell);
      historyTableEl.appendChild(row);
    });
}

function updateChart(history = []) {
  const chart = ensureChart();
  chart.data.labels = history.map((entry) => new Date(entry.timestamp));
  chart.data.datasets[0].data = history.map((entry) => entry.score ?? null);
  chart.options.scales.x = {
    type: "time",
    time: { unit: "minute" },
  };
  chart.update();
}

function applySnapshot(snapshot) {
  if (!snapshot) return;

  const { averages = {}, latest = null, history = [] } = snapshot;

  const meanScore = averages?.overall || averages?.score;
  averageScoreEl.textContent = meanScore ? Math.round(meanScore) : "–";
  latestScoreEl.textContent = latest?.score ?? "–";

  renderMetrics(averages);
  renderHistory(history);
  updateChart(history);
}

fetch("/api/scoreboard")
  .then((response) => response.json())
  .then((snapshot) => applySnapshot(snapshot))
  .catch((error) => console.error("Failed to fetch scoreboard", error));

socket.on("clinician_update", applySnapshot);
