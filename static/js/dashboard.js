// ETHIC-Loop Dashboard Charts
function initDashboardCharts(stageLabels, stageCounts, sevLabels, sevCounts) {
    // 1. Projects by Lifecycle Stage Bar Chart
    const stageCtx = document.getElementById('stageChart');
    if (stageCtx) {
        new Chart(stageCtx, {
            type: 'bar',
            data: {
                labels: stageLabels,
                datasets: [{
                    label: 'Projects in Stage',
                    data: stageCounts,
                    backgroundColor: [
                        '#174C3C',
                        '#236852',
                        '#3a7d65',
                        '#A7C4A0',
                        '#6f9567',
                        '#28352D'
                    ],
                    borderColor: '#174C3C',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#28352D',
                        titleColor: '#F5F3E9',
                        bodyColor: '#FFFFFF',
                        cornerRadius: 6
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#5e6f65' },
                        grid: { color: 'rgba(223, 219, 203, 0.4)' }
                    },
                    x: {
                        ticks: { color: '#28352D', font: { weight: '600' } },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // 2. Risk Severity Doughnut Chart
    const sevCtx = document.getElementById('sevChart');
    if (sevCtx) {
        new Chart(sevCtx, {
            type: 'doughnut',
            data: {
                labels: sevLabels,
                datasets: [{
                    data: sevCounts,
                    backgroundColor: [
                        '#1b6a38', // Low (Green)
                        '#995c00', // Moderate (Amber)
                        '#c2410c', // High (Orange)
                        '#b91c1c'  // Critical (Red)
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#28352D',
                            font: { weight: '600', size: 12 },
                            padding: 14
                        }
                    },
                    tooltip: {
                        backgroundColor: '#28352D',
                        cornerRadius: 6
                    }
                },
                cutout: '65%'
            }
        });
    }
}
