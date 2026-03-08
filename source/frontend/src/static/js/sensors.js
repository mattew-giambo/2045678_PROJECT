document.addEventListener("DOMContentLoaded", () => {
    
    // --- 1. GLOBAL STATE & WEB SOCKET ---
    const socket = new WebSocket('ws://localhost:8005/ws/data_stream');
    
    // Telemetry state (from previous implementation)
    const telemetryStreams = {}; 
    let activeTelemetryId = null;
    let focusedChart = null;
    
    // Sensors state
    const sensorCharts = {};
    const sensorStats = {}; // Stores min/max for each sensor

    // --- 2. INITIALIZE TELEMETRY CHART (from previous setup) ---
    const telemetryCanvas = document.getElementById('focused-canvas');
    if (telemetryCanvas) {
        focusedChart = new Chart(telemetryCanvas.getContext('2d'), {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Telemetry Value',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.2,
                    fill: true,
                    data: []
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                        x: { 
                            type: 'realtime', 
                            realtime: { duration: 20000, refresh: 1000, delay: 1000 },
                            grid: {
                                display: true,
                                color: 'rgba(255, 255, 255, 0.05)', // Griglia verticale sottilissima
                                drawBorder: false
                            },
                            ticks: { 
                                display: true,
                                color: '#64748b', // Colore grigetto per i numeri
                                font: { size: 9 }, // Numeri piccoli
                                maxTicksLimit: 4 // Non più di 4 numeri sull'asse Y
                            }
                        },
                        y: { 
                            display: true,
                            grid: {
                                display: true,
                                color: 'rgba(255, 255, 255, 0.05)', // Griglia orizzontale
                                drawBorder: false
                            },
                            ticks: { 
                                display: true,
                                color: '#64748b', // Colore grigetto per i numeri
                                font: { size: 9 }, // Numeri piccoli
                                maxTicksLimit: 4 // Non più di 4 numeri sull'asse Y
                            }
                        }
                },
                plugins: { legend: { display: false }, streaming: { frameRate: 30 } }
            }
        });

        // Setup Telemetry Rows clicking
        const rows = document.querySelectorAll('.telem-row');
        rows.forEach(row => {
            const id = row.querySelector('.telem-name').innerText.trim();
            telemetryStreams[id] = { value: '--', peak: '--', status: '--', min:'--', history: [] };
            
            row.addEventListener('click', () => {
                rows.forEach(r => r.style.backgroundColor = 'transparent');
                row.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                activeTelemetryId = id;
                updateFocusedTelemetryCard(id);
            });
        });
        if (rows.length > 0) rows[0].click();
    }

    // --- 3. INITIALIZE SENSOR SPARKLINES ---
    // Find all sensor cards and create a mini-chart for each
    const sensorCards = document.querySelectorAll('.sensor-card');
    
    sensorCards.forEach(card => {
        const sensorId = card.id.replace('sensor-card-', ''); // e.g., 'greenhouse_temperature'
        const canvasId = `chart-${sensorId}`;
        const canvasElement = document.getElementById(canvasId);
        
        if (canvasElement) {
            // Initialize min/max tracking for this sensor
            sensorStats[sensorId] = { min: Infinity, max: -Infinity };
            
            sensorCharts[sensorId] = new Chart(canvasElement.getContext('2d'), {
                type: 'line',
                data: {
                    datasets: [{
                        borderColor: '#3b82f6',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3, // Smooth curves
                        data: []
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: { padding: 5 },
                    scales: {
                        x: { 
                            type: 'realtime', 
                            realtime: { duration: 20000, refresh: 1000, delay: 1000 },
                            grid: {
                                display: true,
                                color: 'rgba(255, 255, 255, 0.05)', // Griglia verticale sottilissima
                                drawBorder: false
                            },
                            ticks: { display: false } // Nasconde i numeri per risparmiare spazio
                        },
                        y: { 
                            display: true,
                            grid: {
                                display: true,
                                color: 'rgba(255, 255, 255, 0.05)', // Griglia orizzontale
                                drawBorder: false
                            },
                            ticks: { 
                                display: true,
                                color: '#64748b', // Colore grigetto per i numeri
                                font: { size: 9 }, // Numeri piccoli
                                maxTicksLimit: 4 // Non più di 4 numeri sull'asse Y
                }
        }
    },
    plugins: { legend: { display: false }, tooltip: { enabled: false }, streaming: { frameRate: 30 } }
}
            });
        }
    });


    // --- 4. WEBSOCKET MESSAGE HANDLER ---
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Route data based on the 'type' field
        if (data.type === 'telemetry') {
            handleTelemetryData(data);
        } else if (data.type === 'sensor') {
            handleSensorData(data);
        } else {
            console.warn("Received data with unknown type:", data.type);
        }
    };

    socket.onopen = () => console.log("WebSocket connected.");
    socket.onerror = (e) => console.error("WebSocket error:", e);


    // --- 5. DATA PROCESSING FUNCTIONS ---

    function handleTelemetryData(data) {
        const id = data.device_id;
        const value = parseFloat(data.value);
        const unit = data.unit || '';
        const point = { x: Date.now(), y: value };

        if (!telemetryStreams[id]) {
            telemetryStreams[id] = { history: [], peak: '--', min: '--', status: data.status };
        }

        telemetryStreams[id].value = `${value} ${unit}`;
        telemetryStreams[id].status = data.status || telemetryStreams[id].status;
        
        const currentPeak = parseFloat(telemetryStreams[id].peak) || 0;
        if (value > currentPeak) {
            telemetryStreams[id].peak = `${value} ${unit}`;
        }

        const currentMin = parseFloat(telemetryStreams[id].min) || 10000
        if (value < currentMin) {
            telemetryStreams[id].min = `${value} ${unit}`;
        }

        telemetryStreams[id].history.push(point);
        if (telemetryStreams[id].history.length > 60) telemetryStreams[id].history.shift();

        // Update row UI
        const rows = document.querySelectorAll('.telem-row');
        for (let row of rows) {
            if (row.querySelector('.telem-name').innerText.trim() === id) {
                row.querySelector('.telem-value').innerText = telemetryStreams[id].value;
                break;
            }
        }

        // Update focused chart if this is the active stream
        if (activeTelemetryId === id && focusedChart) {
            document.getElementById('focused-value').innerText = telemetryStreams[id].value;
            document.getElementById('focused-peak').innerText = telemetryStreams[id].peak;
            document.getElementById('focused-status').innerText = telemetryStreams[id].status;
            document.getElementById('focused-min').innerText = telemetryStreams[id].min;
            
            focusedChart.data.datasets[0].data.push(point);
            focusedChart.update('quiet');
        }
    }

    function handleSensorData(data) {
        const id = data.device_id;
        const value = parseFloat(data.value);
        const formattedValue = `${value} ${data.unit}`;
        
        // 1. Update text elements in the DOM
        const valueElement = document.getElementById(`sensor-value-${id}`);
        const badgeElement = document.getElementById(`sensor-badge-${id}`);
        
        if (valueElement) valueElement.innerText = formattedValue;
        if (badgeElement) {
            badgeElement.innerText = formattedValue;
            
            // Optional: Change badge color based on status (if your CSS classes support it)
            if (data.status === 'warning') {
                badgeElement.className = "sensor-badge badge-yellow";
            } else {
                badgeElement.className = "sensor-badge badge-green";
            }
        }

        // 2. Update Min/Max tracking
        if (sensorStats[id]) {
            if (value < sensorStats[id].min) sensorStats[id].min = value;
            if (value > sensorStats[id].max) sensorStats[id].max = value;
            
            const minmaxElement = document.getElementById(`sensor-minmax-${id}`);
            if (minmaxElement) {
                minmaxElement.innerText = `Min ${sensorStats[id].min} / Max ${sensorStats[id].max} this session`;
            }
        }

        // 3. Push data to the specific sparkline chart
        if (sensorCharts[id]) {
            sensorCharts[id].data.datasets[0].data.push({
                x: Date.now(),
                y: value
            });
            sensorCharts[id].update('quiet');
        }
    }

    // Helper function for telemetry updates
    function updateFocusedTelemetryCard(id) {
        const stream = telemetryStreams[id];
        if (!stream || !focusedChart) return;
        document.getElementById('focused-topic').innerText = id;
        document.getElementById('focused-value').innerText = stream.value;
        document.getElementById('focused-peak').innerText = stream.peak;
        document.getElementById('focused-min').innerText = stream.min;
        document.getElementById('focused-status').innerText = stream.status;
        focusedChart.data.datasets[0].data = [...stream.history];
        focusedChart.update();
    }
});