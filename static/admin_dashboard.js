document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialize Filtering
    const searchInput = document.getElementById("tableSearch");
    if (searchInput) {
        searchInput.addEventListener('keyup', filterTable);
    }

    // 2. Initialize AJAX Status Updates
    const statusSelects = document.querySelectorAll('.status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', function() {
            updateComplaintStatus(this);
        });
    });

    // 3. Initialize Charts
    initCharts();

    // 4. Initialize Map
    initMap();

    // 5. Initialize Row Click Interactivity
    initRowInteractivity();

    // 6. Initialize Counter Animations
    initCounters();
});

function initCounters() {
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-target');
        if (isNaN(target)) return;
        
        const increment = target / 50;
        
        function updateCount() {
            const count = +counter.innerText;
            if (count < target) {
                counter.innerText = Math.ceil(count + increment);
                setTimeout(updateCount, 20);
            } else {
                counter.innerText = target;
            }
        }
        updateCount();
    });
}

let dashboardMap;
const markers = [];

function filterTable() {
    let input = document.getElementById("tableSearch");
    let filter = input.value.toUpperCase();
    let table = document.querySelector(".complaints-table");
    let tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let found = false;
        let tds = tr[i].getElementsByTagName("td");
        for (let j = 0; j < tds.length; j++) {
            if (tds[j].textContent.toUpperCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }
        tr[i].style.display = found ? "" : "none";
    }
}

async function updateComplaintStatus(selectElement) {
    const form = selectElement.closest('form');
    const complaintId = form.getAttribute('data-id');
    const newStatus = selectElement.value;
    const formData = new FormData(form);

    // Show loading state
    selectElement.disabled = true;
    const badge = selectElement.closest('tr').querySelector('.status-badge');
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Update badge UI
            if (badge) {
                badge.textContent = newStatus;
                badge.className = `badge status-${newStatus.toLowerCase().replace(' ', '-')}`;
            }
            showToast(result.message, 'success');
        } else {
            throw new Error(result.error || 'Update failed');
        }
    } catch (error) {
        console.error('Error updating status:', error);
        showToast(error.message, 'error');
        // Revert selection if failed
        // Note: For full robustness, we'd store the old value
    } finally {
        selectElement.disabled = false;
    }
}

function initCharts() {
    const typeDataElement = document.getElementById('typeChartData');
    const statusDataElement = document.getElementById('statusChartData');

    if (typeDataElement && statusDataElement) {
        const typeData = JSON.parse(typeDataElement.textContent);
        const statusData = JSON.parse(statusDataElement.textContent);

        const typeCtx = document.getElementById('typeChart').getContext('2d');
        new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: typeData.labels,
                datasets: [{
                    data: typeData.values,
                    backgroundColor: ['#00d2ff', '#6366f1', '#f43f5e', '#fbbf24', '#a855f7'],
                    borderWidth: 0,
                    hoverOffset: 25
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { 
                            usePointStyle: true, 
                            padding: 25,
                            color: '#94a3b8',
                            font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' }
                        }
                    }
                },
                cutout: '75%'
            }
        });
    }
}

function initMap() {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return;

    dashboardMap = L.map('map').setView([23.8103, 90.4125], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(dashboardMap);

    const mapDataElement = document.getElementById('mapMarkersData');
    if (mapDataElement) {
        const markerData = JSON.parse(mapDataElement.textContent);
        markerData.forEach(m => {
            const marker = L.marker([m.lat, m.lng])
                .addTo(dashboardMap)
                .bindPopup(`<b>${m.type}</b><br>${m.location}`);
            markers.push({ id: m.id, marker: marker });
        });
    }
}

function initRowInteractivity() {
    const rows = document.querySelectorAll('.complaints-table tbody tr');
    rows.forEach((row, index) => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on select or links
            if (e.target.tagName === 'SELECT' || e.target.tagName === 'A' || e.target.tagName === 'OPTION') {
                return;
            }
            
            if (markers[index]) {
                const marker = markers[index].marker;
                dashboardMap.setView(marker.getLatLng(), 15);
                marker.openPopup();
                
                // Visual feedback on row
                rows.forEach(r => r.classList.remove('active-row'));
                row.classList.add('active-row');
                
                // Scroll map into view if mobile
                if (window.innerWidth < 768) {
                    document.getElementById('map').scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
}

function showToast(message, type) {
    // Basic toast implementation
    const toast = document.createElement('div');
    toast.className = `flash ${type}`;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '250px';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}
