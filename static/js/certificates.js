/**
 * Certificate Management JavaScript
 * Handles TLS certificate generation, download and management
 */

class CertificateManager {
    constructor() {
        this.progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
        this.initializeEventListeners();
        this.loadCertificates();
    }

    initializeEventListeners() {
        // Generate server certificates form
        document.getElementById('generateCertForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateServerCertificates();
        });

        // Generate client certificate form
        document.getElementById('generateClientCertForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateClientCertificate();
        });
    }

    async generateServerCertificates() {
        const formData = {
            server_name: document.getElementById('serverName').value,
            server_ip: document.getElementById('serverIp').value || null,
            organization: document.getElementById('organization').value,
            validity_days: parseInt(document.getElementById('validityDays').value)
        };

        this.showProgress('Generazione certificati server in corso...');

        try {
            const response = await fetch('/api/certificates/generate-server', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                this.hideProgress();
                this.showSuccess('Certificati server generati con successo!');
                this.loadCertificates();
                
                // Update server name display
                document.getElementById('serverNameDisplay').textContent = formData.server_name;
                
                // Show download options
                this.showDownloadOptions(result);
            } else {
                this.hideProgress();
                this.showError(result.error || 'Errore durante la generazione');
            }
        } catch (error) {
            this.hideProgress();
            this.showError('Errore di connessione: ' + error.message);
        }
    }

    async generateClientCertificate() {
        const formData = {
            client_name: document.getElementById('clientName').value,
            extension: document.getElementById('extension').value,
            validity_days: parseInt(document.getElementById('clientValidityDays').value)
        };

        this.showProgress('Generazione certificato client in corso...');

        try {
            const response = await fetch('/api/certificates/generate-client', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                this.hideProgress();
                this.showSuccess(`Certificato per ${formData.client_name}-${formData.extension} generato!`);
                this.loadCertificates();
                this.showClientDownloadOptions(result);
            } else {
                this.hideProgress();
                this.showError(result.error || 'Errore durante la generazione');
            }
        } catch (error) {
            this.hideProgress();
            this.showError('Errore di connessione: ' + error.message);
        }
    }

    async loadCertificates() {
        try {
            const response = await fetch('/api/certificates/list');
            const certificates = await response.json();

            this.updateCertificatesTable(certificates);
            this.updateCertificateCount(certificates.length);
        } catch (error) {
            console.error('Error loading certificates:', error);
        }
    }

    updateCertificatesTable(certificates) {
        const tbody = document.getElementById('certificatesTableBody');
        
        if (certificates.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nessun certificato trovato</td></tr>';
            return;
        }

        tbody.innerHTML = certificates.map(cert => {
            const isExpired = cert.is_expired;
            const daysUntilExpiry = cert.days_until_expiry;
            const statusClass = isExpired ? 'danger' : (daysUntilExpiry < 30 ? 'warning' : 'success');
            const statusText = isExpired ? 'Scaduto' : (daysUntilExpiry < 30 ? 'In scadenza' : 'Valido');
            
            const certType = this.getCertificateType(cert.filename);
            const subject = this.parseSubject(cert.subject);
            
            return `
                <tr>
                    <td><code>${cert.filename}</code></td>
                    <td><span class="badge bg-secondary">${certType}</span></td>
                    <td class="small">${subject}</td>
                    <td class="small">${this.formatDate(cert.not_valid_before)} - ${this.formatDate(cert.not_valid_after)}</td>
                    <td class="small">${daysUntilExpiry} giorni</td>
                    <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="certificateManager.downloadCertificate('${cert.filename}')">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-outline-info" onclick="certificateManager.viewCertificate('${cert.filename}')">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="certificateManager.deleteCertificate('${cert.filename}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    getCertificateType(filename) {
        if (filename.includes('ca-cert')) return 'CA';
        if (filename.includes('bundle')) return 'Bundle';
        if (filename.includes('client')) return 'Client';
        if (filename.includes('server') || filename.includes('sip-server')) return 'Server';
        return 'Unknown';
    }

    parseSubject(subject) {
        // Extract common name from subject string
        const cnMatch = subject.match(/CN=([^,]+)/);
        return cnMatch ? cnMatch[1] : subject.substring(0, 30) + '...';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('it-IT');
    }

    updateCertificateCount(count) {
        document.getElementById('activeCerts').textContent = count;
        
        const statusElement = document.getElementById('tlsStatus');
        if (count > 0) {
            statusElement.textContent = 'TLS: Configurato';
            statusElement.className = 'badge bg-success';
        } else {
            statusElement.textContent = 'TLS: Configurazione Richiesta';
            statusElement.className = 'badge bg-info';
        }
    }

    showDownloadOptions(result) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show mt-3" role="alert">
                <h6><i class="fas fa-check-circle me-2"></i>Certificati generati con successo!</h6>
                <p class="mb-3">Scarica i file necessari per configurare i tuoi client SIP:</p>
                <div class="d-flex flex-wrap gap-2">
                    <a href="/api/certificates/download/${result.server_cert_file}" class="btn btn-sm btn-primary">
                        <i class="fas fa-download me-1"></i>Certificato Server
                    </a>
                    <a href="/api/certificates/download/${result.server_bundle_file}" class="btn btn-sm btn-success">
                        <i class="fas fa-download me-1"></i>Bundle (per client)
                    </a>
                    <a href="/api/certificates/download/ca-cert.pem" class="btn btn-sm btn-secondary">
                        <i class="fas fa-download me-1"></i>Certificato CA
                    </a>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.querySelector('.card-body').insertAdjacentHTML('afterbegin', alertHtml);
    }

    showClientDownloadOptions(result) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show mt-3" role="alert">
                <h6><i class="fas fa-check-circle me-2"></i>Certificato client generato!</h6>
                <p class="mb-3">Scarica i file per configurare il client SIP:</p>
                <div class="d-flex flex-wrap gap-2">
                    <a href="/api/certificates/download/${result.client_cert_file}" class="btn btn-sm btn-primary">
                        <i class="fas fa-download me-1"></i>Certificato Client
                    </a>
                    ${result.client_p12_file ? `
                        <a href="/api/certificates/download/${result.client_p12_file}" class="btn btn-sm btn-success">
                            <i class="fas fa-download me-1"></i>PKCS12 (facile installazione)
                        </a>
                    ` : ''}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.querySelector('.card-body').insertAdjacentHTML('afterbegin', alertHtml);
    }

    async downloadCertificate(filename) {
        window.open(`/api/certificates/download/${filename}`, '_blank');
    }

    async viewCertificate(filename) {
        try {
            const response = await fetch(`/api/certificates/info/${filename}`);
            const certInfo = await response.json();
            
            this.showCertificateInfo(certInfo);
        } catch (error) {
            this.showError('Errore nel caricamento informazioni certificato');
        }
    }

    showCertificateInfo(certInfo) {
        const modalHtml = `
            <div class="modal fade" id="certInfoModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Informazioni Certificato</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <dl class="row">
                                <dt class="col-sm-3">Soggetto:</dt>
                                <dd class="col-sm-9"><code>${certInfo.subject}</code></dd>
                                
                                <dt class="col-sm-3">Emittente:</dt>
                                <dd class="col-sm-9"><code>${certInfo.issuer}</code></dd>
                                
                                <dt class="col-sm-3">Numero Seriale:</dt>
                                <dd class="col-sm-9"><code>${certInfo.serial_number}</code></dd>
                                
                                <dt class="col-sm-3">Valido da:</dt>
                                <dd class="col-sm-9">${this.formatDate(certInfo.not_valid_before)}</dd>
                                
                                <dt class="col-sm-3">Valido fino:</dt>
                                <dd class="col-sm-9">${this.formatDate(certInfo.not_valid_after)}</dd>
                                
                                <dt class="col-sm-3">Stato:</dt>
                                <dd class="col-sm-9">
                                    <span class="badge bg-${certInfo.is_expired ? 'danger' : 'success'}">
                                        ${certInfo.is_expired ? 'Scaduto' : 'Valido'}
                                    </span>
                                </dd>
                            </dl>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Chiudi</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('certInfoModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('certInfoModal'));
        modal.show();
    }

    async deleteCertificate(filename) {
        if (!confirm(`Sei sicuro di voler eliminare il certificato ${filename}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/certificates/delete/${filename}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Certificato eliminato con successo');
                this.loadCertificates();
            } else {
                this.showError(result.error || 'Errore durante l\'eliminazione');
            }
        } catch (error) {
            this.showError('Errore di connessione: ' + error.message);
        }
    }

    showProgress(text) {
        document.getElementById('progressText').textContent = text;
        this.progressModal.show();
    }

    hideProgress() {
        this.progressModal.hide();
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

// Global functions for button clicks
function refreshCertificates() {
    certificateManager.loadCertificates();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.certificateManager = new CertificateManager();
});