/**
 * API Configuration and HTTP Client
 */

const API_CONFIG = {
    baseURL: 'http://localhost:8000/api/v1',
    wsURL: 'ws://localhost:8006/ws',
    timeout: 30000
};

class APIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
    }

    async request(endpoint, options = {}) {
        const url = `${API_CONFIG.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                timeout: API_CONFIG.timeout
            });

            if (response.status === 401) {
                // Token expired, redirect to login
                this.logout();
                return null;
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'API request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    }
}

const api = new APIClient();

/**
 * WebSocket Manager
 */
class WebSocketManager {
    constructor() {
        this.connections = {};
    }

    connect(type, id, onMessage) {
        const wsURL = `${API_CONFIG.wsURL}/${type}/${id}`;
        const ws = new WebSocket(wsURL);

        ws.onopen = () => {
            console.log(`WebSocket connected: ${type}/${id}`);
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (onMessage) onMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log(`WebSocket closed: ${type}/${id}`);
            delete this.connections[id];
        };

        this.connections[id] = ws;
        return ws;
    }

    disconnect(id) {
        if (this.connections[id]) {
            this.connections[id].close();
            delete this.connections[id];
        }
    }

    disconnectAll() {
        Object.keys(this.connections).forEach(id => this.disconnect(id));
    }
}

const wsManager = new WebSocketManager();
