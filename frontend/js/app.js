/**
 * Main Application Logic
 */

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();

        // Update active nav
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');

        // Show corresponding page
        const pageName = item.dataset.page;
        showPage(pageName);
    });
});

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(`${pageName}-page`).classList.add('active');

    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'applications': 'Applications',
        'underwriting': 'Underwriting Workflow',
        'analytics': 'Analytics & Reports',
        'monitoring': 'System Monitoring',
        'admin': 'Admin Console'
    };
    document.getElementById('page-title').textContent = titles[pageName] || pageName;

    // Load page data
    loadPageData(pageName);
}

// Load Applications Table
async function loadApplications() {
    try {
        // In production, fetch from API
        // const data = await api.get('/applications');

        // Mock data for demo
        const applications = [
            {
                id: 'APP-2024-001',
                applicant: 'Budi Santoso',
                amount: 150000000,
                creditScore: 720,
                status: 'PENDING',
                submitted: '2024-01-15'
            },
            {
                id: 'APP-2024-002',
                applicant: 'Siti Aminah',
                amount: 200000000,
                creditScore: 680,
                status: 'APPROVED',
                submitted: '2024-01-14'
            },
            {
                id: 'APP-2024-003',
                applicant: 'Ahmad Hidayat',
                amount: 100000000,
                creditScore: 550,
                status: 'REJECTED',
                submitted: '2024-01-13'
            }
        ];

        const tbody = document.querySelector('#applications-table tbody');
        tbody.innerHTML = applications.map(app => `
            <tr>
                <td><strong>${app.id}</strong></td>
                <td>${app.applicant}</td>
                <td>Rp ${app.amount.toLocaleString('id-ID')}</td>
                <td><span class="badge ${getCreditScoreBadge(app.creditScore)}">${app.creditScore}</span></td>
                <td><span class="badge ${getStatusBadge(app.status)}">${app.status}</span></td>
                <td>${app.submitted}</td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="viewApplication('${app.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading applications:', error);
    }
}

function getCreditScoreBadge(score) {
    if (score >= 700) return 'badge-success';
    if (score >= 600) return 'badge-info';
    if (score >= 500) return 'badge-warning';
    return 'badge-danger';
}

function getStatusBadge(status) {
    const badges = {
        'PENDING': 'badge-warning',
        'APPROVED': 'badge-success',
        'REJECTED': 'badge-danger',
        'PROCESSING': 'badge-info'
    };
    return badges[status] || 'badge-info';
}

// Load Users (Admin Page)
async function loadUsers() {
    try {
        const users = [
            {
                name: 'System Administrator',
                email: 'admin@analyticaloan.com',
                role: 'ADMIN',
                status: 'Active'
            },
            {
                name: 'John Underwriter',
                email: 'underwriter@analyticaloan.com',
                role: 'UNDERWRITER',
                status: 'Active'
            },
            {
                name: 'Jane Risk Analyst',
                email: 'risk@analyticaloan.com',
                role: 'RISK_ANALYST',
                status: 'Active'
            }
        ];

        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td><span class="badge badge-info">${user.role}</span></td>
                <td><span class="badge badge-success">${user.status}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Initialize Charts (Analytics Page)
function initializeCharts() {
    // Approvals Chart
    const approvalsCtx = document.getElementById('approvals-chart');
    if (approvalsCtx) {
        new Chart(approvalsCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Approved',
                    data: [45, 52, 48, 67, 73, 82],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Rejected',
                    data: [12, 15, 10, 8, 13, 9],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#94a3b8' }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: '#334155' }
                    }
                }
            }
        });
    }

    // Risk Distribution Chart
    const riskCtx = document.getElementById('risk-chart');
    if (riskCtx) {
        new Chart(riskCtx, {
            type: 'doughnut',
            data: {
                labels: ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'C'],
                datasets: [{
                    data: [15, 25, 30, 18, 8, 3, 1],
                    backgroundColor: [
                        '#10b981',
                        '#34d399',
                        '#6ee7b7',
                        '#f59e0b',
                        '#fbbf24',
                        '#ef4444',
                        '#dc2626'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#94a3b8' }
                    }
                }
            }
        });
    }
}

// Page Data Loader
function loadPageData(pageName) {
    switch (pageName) {
        case 'dashboard':
        case 'applications':
            loadApplications();
            break;
        case 'admin':
            loadUsers();
            break;
        case 'analytics':
            setTimeout(initializeCharts, 100);
            break;
    }
}

// Workflow Functions
function refreshWorkflow() {
    console.log('Refreshing workflow...');
    // Implement workflow refresh
}

function viewApplication(id) {
    console.log('Viewing application:', id);
    // Navigate to application detail page
}

// Logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        api.logout();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load initial page
    loadPageData('dashboard');

    // Check authentication
    if (!localStorage.getItem('access_token')) {
        window.location.href = '/login.html';
    }
});
