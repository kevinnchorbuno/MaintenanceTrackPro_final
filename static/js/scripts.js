document.addEventListener('DOMContentLoaded', function() {
    // Existing delete confirmation logic
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Existing theme switching logic
    const themeSwitcher = document.getElementById('theme-switcher');
    if (themeSwitcher) {
        themeSwitcher.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            this.textContent = document.body.classList.contains('dark-mode') ? 'Light Mode' : 'Dark Mode';
            document.querySelector('.navbar').classList.toggle('navbar-dark');
            document.querySelector('.navbar').classList.toggle('bg-dark');
        });
    }

    // New chart initialization and update logic
    const equipmentSelect = document.getElementById('equipmentSelect');
    const healthChartCanvas = document.getElementById('healthChart');
    if (equipmentSelect && healthChartCanvas) {
        const ctx = healthChartCanvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [], // Will be populated with timestamps or other x-axis data
                datasets: [{
                    label: 'Temperature (°C)',
                    data: [], // Will be populated with temperature values
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuad'
                }
            }
        });

        // Function to update the chart with data for a given equipment ID
        function updateChart(equipmentId) {
            fetch('/get_health_data/' + equipmentId)
                .then(response => response.json())
                .then(data => {
                    chart.data.labels = data.labels; // e.g., ["10:00", "10:05", ...]
                    chart.data.datasets[0].data = data.temperature; // e.g., [22, 23, ...]
                    chart.update();
                })
                .catch(error => console.error('Error fetching health data:', error));
        }

        // Event listener for equipment selection
        equipmentSelect.addEventListener('change', function() {
            updateChart(this.value);
        });

        // Initialize chart with the first equipment (if any)
        if (equipmentSelect.options.length > 0) {
            updateChart(equipmentSelect.value);
        }
    }
});