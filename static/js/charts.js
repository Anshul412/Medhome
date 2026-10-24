"use strict";

(() => {
  const bloodPressureCanvas = document.getElementById("bp-chart");
  const oxygenCanvas = document.getElementById("spo2-chart");

  if (!bloodPressureCanvas || !oxygenCanvas) {
    return;
  }

  const errorMessage = document.getElementById("chart-error");
  const chartDataUrl =
    bloodPressureCanvas.dataset.chartDataUrl || "/vitals/api/chart-data/";
  const fontFamily = 'Arial, Helvetica, sans-serif';
  const fontColor = "#0f172a";
  Chart.defaults.font.family = fontFamily;
  Chart.defaults.font.size = 15;
  Chart.defaults.color = fontColor;

  const thresholdZonePlugin = {
    id: "spo2ThresholdZone",
    beforeDatasetsDraw(chart) {
      const yScale = chart.scales.y;
      const { ctx, chartArea } = chart;

      if (!yScale || !chartArea) {
        return;
      }

      const thresholdY = yScale.getPixelForValue(94);
      ctx.save();
      ctx.fillStyle = "rgba(185, 28, 28, 0.12)";
      ctx.fillRect(
        chartArea.left,
        thresholdY,
        chartArea.right - chartArea.left,
        chartArea.bottom - thresholdY,
      );
      ctx.restore();
    },
    afterDatasetsDraw(chart) {
      const yScale = chart.scales.y;
      const { ctx, chartArea } = chart;

      if (!yScale || !chartArea) {
        return;
      }

      const thresholdY = yScale.getPixelForValue(94);
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = "#b91c1c";
      ctx.lineWidth = 2;
      ctx.moveTo(chartArea.left, thresholdY);
      ctx.lineTo(chartArea.right, thresholdY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#7f1d1d";
      ctx.font = `bold 14px ${fontFamily}`;
      ctx.textAlign = "right";
      ctx.textBaseline = "bottom";
      ctx.fillText("94% threshold", chartArea.right - 6, thresholdY - 4);
      ctx.restore();
    },
  };

  const sharedOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        labels: {
          color: fontColor,
          font: { family: fontFamily, size: 16, weight: "bold" },
          padding: 18,
          usePointStyle: true,
        },
      },
      tooltip: {
        titleFont: { family: fontFamily, size: 16, weight: "bold" },
        bodyFont: { family: fontFamily, size: 15 },
      },
    },
    scales: {
      x: {
        ticks: {
          color: fontColor,
          font: { family: fontFamily, size: 14 },
        },
        grid: { color: "#cbd5e1" },
        title: {
          display: true,
          text: "Date",
          color: fontColor,
          font: { family: fontFamily, size: 15, weight: "bold" },
        },
      },
      y: {
        beginAtZero: false,
        ticks: {
          color: fontColor,
          font: { family: fontFamily, size: 14 },
        },
        grid: { color: "#cbd5e1" },
      },
    },
  };

  const reportError = (message) => {
    if (errorMessage) {
      errorMessage.textContent = message;
    }
  };

  fetch(chartDataUrl, {
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Could not load trend data. Please refresh and try again.");
      }
      return response.json();
    })
    .then((data) => {
      if (
        !Array.isArray(data.dates) ||
        !Array.isArray(data.systolic) ||
        !Array.isArray(data.diastolic) ||
        !Array.isArray(data.spo2)
      ) {
        throw new Error("Trend data is incomplete. Please contact support.");
      }

      new Chart(bloodPressureCanvas, {
        type: "line",
        data: {
          labels: data.dates,
          datasets: [
            {
              label: "Systolic (mmHg)",
              data: data.systolic,
              borderColor: "#b91c1c",
              backgroundColor: "#b91c1c",
              borderWidth: 3,
              pointRadius: 4,
              pointHoverRadius: 7,
              spanGaps: true,
              tension: 0.25,
            },
            {
              label: "Diastolic (mmHg)",
              data: data.diastolic,
              borderColor: "#1d4ed8",
              backgroundColor: "#1d4ed8",
              borderWidth: 3,
              pointRadius: 4,
              pointHoverRadius: 7,
              spanGaps: true,
              tension: 0.25,
            },
          ],
        },
        options: {
          ...sharedOptions,
          plugins: {
            ...sharedOptions.plugins,
            title: {
              display: true,
              text: "Blood pressure readings",
              color: fontColor,
              font: { family: fontFamily, size: 18, weight: "bold" },
            },
          },
          scales: {
            ...sharedOptions.scales,
            y: {
              ...sharedOptions.scales.y,
              title: {
                display: true,
                text: "Blood pressure (mmHg)",
                color: fontColor,
                font: { family: fontFamily, size: 15, weight: "bold" },
              },
            },
          },
        },
      });

      new Chart(oxygenCanvas, {
        type: "line",
        data: {
          labels: data.dates,
          datasets: [
            {
              label: "SpO2 (%)",
              data: data.spo2,
              borderColor: "#047857",
              backgroundColor: "#047857",
              borderWidth: 3,
              pointRadius: 4,
              pointHoverRadius: 7,
              pointBackgroundColor: data.spo2.map((value) =>
                value !== null && value < 94 ? "#b91c1c" : "#047857",
              ),
              spanGaps: true,
              tension: 0.25,
            },
          ],
        },
        options: {
          ...sharedOptions,
          plugins: {
            ...sharedOptions.plugins,
            title: {
              display: true,
              text: "Blood oxygen readings",
              color: fontColor,
              font: { family: fontFamily, size: 18, weight: "bold" },
            },
          },
          scales: {
            ...sharedOptions.scales,
            y: {
              ...sharedOptions.scales.y,
              min: 0,
              max: 100,
              title: {
                display: true,
                text: "SpO2 (%)",
                color: fontColor,
                font: { family: fontFamily, size: 15, weight: "bold" },
              },
            },
          },
        },
        plugins: [thresholdZonePlugin],
      });

      reportError("");
    })
    .catch((error) => {
      reportError(error.message || "Could not load trend data.");
    });
})();
