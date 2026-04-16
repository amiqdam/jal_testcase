/* Dynamic Charts Component */
function createDynamicChart(container, type, chartData, options) {
  const canvas = document.createElement('canvas');
  container.appendChild(canvas);
  return new Chart(canvas.getContext('2d'), {
    type: type,
    data: chartData,
    options: options || { responsive: true }
  });
}
