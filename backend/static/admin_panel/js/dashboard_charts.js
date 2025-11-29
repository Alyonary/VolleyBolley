document.addEventListener('DOMContentLoaded', function() {
    // Games chart
    const gamesLabels = window.gamesChartLabels || [];
    const gamesData = window.gamesChartData || [];
    const ctx = document.getElementById('gamesChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: gamesLabels,
            datasets: [{
                label: 'Games',
                data: gamesData,
                borderColor: '#0073aa',
                backgroundColor: 'rgba(0,115,170,0.1)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Players chart
    const playersLabels = window.playersChartLabels || [];
    const playersData = window.playersChartData || [];
    const ctxPlayers = document.getElementById('playersChart').getContext('2d');
    new Chart(ctxPlayers, {
        type: 'line',
        data: {
            labels: playersLabels,
            datasets: [{
                label: 'Players',
                data: playersData,
                borderColor: '#ff9800',
                backgroundColor: 'rgba(255,152,0,0.1)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            }
        }
    });
});