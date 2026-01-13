#!/usr/bin/perl
#
# backupjs.cgi - Modern JavaScript-based backup interface
# This file is part of the IPCop Firewall.
#
# Alternative to classic backup.cgi with modern, interactive UI.
#
# MENUENTRY system 085 "BackupJS" "modern backup"

use strict;
use warnings;

require '/usr/lib/ipcop/general-functions.pl';
require '/usr/lib/ipcop/lang.pl';
require '/usr/lib/ipcop/header.pl';

&Header::showhttpheaders();
&Header::openpage('Backup Management', 1, '');
&Header::openbigbox('100%', 'left');

print <<'HTML';
<style>
    .backup-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .section {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #333;
        border-bottom: 2px solid #4a90d9;
        padding-bottom: 8px;
    }
    .form-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .form-row label {
        min-width: 120px;
        font-weight: 500;
    }
    .form-row input[type="text"],
    .form-row input[type="password"] {
        flex: 1;
        max-width: 300px;
        padding: 8px 12px;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 14px;
    }
    .form-row input[type="file"] {
        flex: 1;
    }
    .btn {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    .btn-primary {
        background: #4a90d9;
        color: white;
    }
    .btn-primary:hover {
        background: #357abd;
    }
    .btn-success {
        background: #28a745;
        color: white;
    }
    .btn-success:hover {
        background: #218838;
    }
    .btn-danger {
        background: #dc3545;
        color: white;
    }
    .btn-danger:hover {
        background: #c82333;
    }
    .btn-secondary {
        background: #6c757d;
        color: white;
    }
    .btn-secondary:hover {
        background: #545b62;
    }
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .backup-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .backup-table th,
    .backup-table td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #eee;
    }
    .backup-table th {
        background: #f8f9fa;
        font-weight: 600;
        color: #333;
    }
    .backup-table tr:hover {
        background: #f5f5f5;
    }
    .backup-actions {
        display: flex;
        gap: 8px;
    }
    .backup-actions .btn {
        padding: 6px 12px;
        font-size: 12px;
    }
    .icon-btn {
        width: 32px;
        height: 32px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .alert {
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 15px;
        display: none;
    }
    .alert-success {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .alert-error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .alert-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
    }
    .no-key-warning {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeeba;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .loading {
        opacity: 0.6;
        pointer-events: none;
    }
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #4a90d9;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .size-badge {
        background: #e9ecef;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        color: #666;
    }
    .empty-state {
        text-align: center;
        padding: 40px;
        color: #666;
    }
    .modal-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        align-items: center;
        justify-content: center;
    }
    .modal {
        background: white;
        border-radius: 8px;
        padding: 24px;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .modal-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
    }
    .modal-body {
        margin-bottom: 20px;
    }
    .modal-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }
</style>

<div class="backup-container">
    <div id="alert" class="alert"></div>
    <div id="no-key-warning" class="no-key-warning" style="display: none;">
        <strong>Warning:</strong> No backup key found. You must create a backup key before you can create backups.
        <button class="btn btn-primary" style="margin-left: 15px;" onclick="generateKey()">Generate Key</button>
    </div>

    <!-- Key Export Section -->
    <div class="section">
        <div class="section-title">🔑 Backup Key</div>
        <form id="key-form" onsubmit="exportKey(event)">
            <div class="form-row">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter backup password" />
                <button type="submit" class="btn btn-secondary">Export Key</button>
            </div>
        </form>
    </div>

    <!-- Create Backup Section -->
    <div class="section">
        <div class="section-title">➕ Create New Backup</div>
        <form id="create-form" onsubmit="createBackup(event)">
            <div class="form-row">
                <label for="description">Description:</label>
                <input type="text" id="description" name="description" placeholder="Optional description" maxlength="80" />
                <button type="submit" class="btn btn-success" id="create-btn">Create Backup</button>
            </div>
        </form>
    </div>

    <!-- Upload Section -->
    <div class="section">
        <div class="section-title">📤 Upload Backup</div>
        <form id="upload-form" onsubmit="uploadBackup(event)" enctype="multipart/form-data">
            <div class="form-row">
                <label for="upload-file">Backup File:</label>
                <input type="file" id="upload-file" name="FH" accept=".dat" />
                <button type="submit" class="btn btn-primary">Upload</button>
            </div>
        </form>
    </div>

    <!-- Backup List Section -->
    <div class="section">
        <div class="section-title">📁 Backup Sets</div>
        <div id="backup-list">
            <div class="loading-state" style="text-align: center; padding: 20px;">
                <span class="spinner"></span> Loading backups...
            </div>
        </div>
    </div>
</div>

<!-- Restore Confirmation Modal -->
<div id="restore-modal" class="modal-overlay">
    <div class="modal">
        <div class="modal-title">Confirm Restore</div>
        <div class="modal-body">
            <p>Are you sure you want to restore from this backup?</p>
            <p id="restore-filename" style="font-weight: 500;"></p>
            <div style="margin-top: 15px;">
                <label>
                    <input type="checkbox" id="restore-hardware" />
                    Restore hardware settings (network interfaces)
                </label>
            </div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeRestoreModal()">Cancel</button>
            <button class="btn btn-danger" onclick="confirmRestore()">Restore</button>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div id="delete-modal" class="modal-overlay">
    <div class="modal">
        <div class="modal-title">Confirm Delete</div>
        <div class="modal-body">
            <p>Are you sure you want to delete this backup?</p>
            <p id="delete-filename" style="font-weight: 500;"></p>
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" onclick="closeDeleteModal()">Cancel</button>
            <button class="btn btn-danger" onclick="confirmDelete()">Delete</button>
        </div>
    </div>
</div>

<script>
let currentRestoreFile = null;
let currentDeleteFile = null;
let keyExists = false;

function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.className = 'alert alert-' + type;
    alert.textContent = message;
    alert.style.display = 'block';
    setTimeout(() => { alert.style.display = 'none'; }, 5000);
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function loadBackups() {
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi?action=list');
        const data = await response.json();
        
        keyExists = data.keyExists;
        document.getElementById('no-key-warning').style.display = keyExists ? 'none' : 'block';
        document.getElementById('create-btn').disabled = !keyExists;
        
        const container = document.getElementById('backup-list');
        
        if (!data.backups || data.backups.length === 0) {
            container.innerHTML = '<div class="empty-state">No backup sets found. Create your first backup above.</div>';
            return;
        }
        
        let html = '<table class="backup-table">';
        html += '<tr><th>Date/Time</th><th>Description</th><th>Size</th><th>Actions</th></tr>';
        
        data.backups.forEach(backup => {
            html += `<tr>
                <td>${backup.datetime || 'Unknown'}</td>
                <td>${backup.description || '<em>No description</em>'}</td>
                <td><span class="size-badge">${formatSize(backup.size)}</span></td>
                <td class="backup-actions">
                    <button class="btn btn-primary icon-btn" onclick="showRestoreModal('${backup.filename}')" title="Restore">↻</button>
                    <a href="${backup.downloadUrl}" class="btn btn-success icon-btn" title="Download" download>↓</a>
                    <button class="btn btn-danger icon-btn" onclick="showDeleteModal('${backup.filename}')" title="Delete">🗑</button>
                </td>
            </tr>`;
        });
        
        html += '</table>';
        container.innerHTML = html;
    } catch (e) {
        console.error('Failed to load backups:', e);
        document.getElementById('backup-list').innerHTML = 
            '<div class="empty-state" style="color: #dc3545;">Failed to load backups. Please refresh the page.</div>';
    }
}

async function createBackup(event) {
    event.preventDefault();
    
    if (!keyExists) {
        showAlert('Cannot create backup: No backup key found', 'error');
        return;
    }
    
    const description = document.getElementById('description').value;
    const btn = document.getElementById('create-btn');
    const originalText = btn.textContent;
    
    btn.innerHTML = '<span class="spinner"></span>Creating...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `action=create&description=${encodeURIComponent(description)}`
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Backup created successfully!', 'success');
            document.getElementById('description').value = '';
            loadBackups();
        } else {
            showAlert(data.error || 'Failed to create backup', 'error');
        }
    } catch (e) {
        showAlert('Error creating backup: ' + e.message, 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = !keyExists;
    }
}

async function uploadBackup(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('upload-file');
    if (!fileInput.files[0]) {
        showAlert('Please select a backup file to upload', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'upload');
    formData.append('FH', fileInput.files[0]);
    
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Backup uploaded successfully!', 'success');
            fileInput.value = '';
            loadBackups();
        } else {
            showAlert(data.error || 'Failed to upload backup', 'error');
        }
    } catch (e) {
        showAlert('Error uploading backup: ' + e.message, 'error');
    }
}

function showRestoreModal(filename) {
    currentRestoreFile = filename;
    document.getElementById('restore-filename').textContent = filename;
    document.getElementById('restore-modal').style.display = 'flex';
}

function closeRestoreModal() {
    document.getElementById('restore-modal').style.display = 'none';
    currentRestoreFile = null;
}

async function confirmRestore() {
    if (!currentRestoreFile) return;
    
    const filename = currentRestoreFile;  // Save before closeModal nullifies it
    const restoreHardware = document.getElementById('restore-hardware').checked;
    closeRestoreModal();
    
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `action=restore&filename=${encodeURIComponent(filename)}&restoreHardware=${restoreHardware}`
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'warning');
        } else {
            showAlert(data.error || 'Restore failed', 'error');
        }
    } catch (e) {
        showAlert('Error during restore: ' + e.message, 'error');
    }
}

function showDeleteModal(filename) {
    currentDeleteFile = filename;
    document.getElementById('delete-filename').textContent = filename;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
    currentDeleteFile = null;
}

async function confirmDelete() {
    if (!currentDeleteFile) return;
    
    const filename = currentDeleteFile;  // Save before closeModal nullifies it
    closeDeleteModal();
    
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `action=delete&filename=${encodeURIComponent(filename)}`
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Backup deleted', 'success');
            loadBackups();
        } else {
            showAlert(data.error || 'Delete failed', 'error');
        }
    } catch (e) {
        showAlert('Error deleting backup: ' + e.message, 'error');
    }
}

function exportKey(event) {
    event.preventDefault();
    // For key export, we use the original backup.cgi method
    // as it requires proper binary response handling
    const password = document.getElementById('password').value;
    if (password.length < 6) {
        showAlert('Password must be at least 6 characters', 'error');
        return;
    }
    
    // Create a form and submit it to trigger the key download
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/cgi-bin/backup.cgi';
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'ACTION';
    actionInput.value = 'Export backup key';
    form.appendChild(actionInput);
    
    const passInput = document.createElement('input');
    passInput.type = 'hidden';
    passInput.name = 'PASSWORD';
    passInput.value = password;
    form.appendChild(passInput);
    
    document.body.appendChild(form);
    form.submit();
}

async function generateKey() {
    try {
        const response = await fetch('/cgi-bin/backupapi.cgi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'action=generatekey'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Backup key created successfully!', 'success');
            loadBackups();  // Reload to update UI
        } else {
            showAlert(data.error || 'Failed to create backup key', 'error');
        }
    } catch (e) {
        showAlert('Error creating backup key: ' + e.message, 'error');
    }
}

// Initial load
loadBackups();
</script>
HTML

&Header::closebigbox();
&Header::closepage();
