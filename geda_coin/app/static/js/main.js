let miningInterval;
let isMining = false;
let miningPower = 0.5; // Default mining power (50%)
const MAX_GADA = 1619;

// Mining Controls
async function toggleMining() {
    const button = document.getElementById('mining-toggle');
    if (!isMining) {
        // Start mining on server
        const response = await fetch('/mining/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mining_power: miningPower })
        });
        
        if (response.ok) {
            startMining();
            button.innerHTML = '<i class="fas fa-stop"></i> Stop Mining';
            button.style.backgroundColor = '#f44336';
        }
    } else {
        // Stop mining on server
        await fetch('/mining/stop', { method: 'POST' });
        stopMining();
        button.innerHTML = '<i class="fas fa-play"></i> Start Mining';
        button.style.backgroundColor = '';
    }
    isMining = !isMining;
}

function startMining() {
    miningInterval = setInterval(updateMiningStats, 1000);
}

function stopMining() {
    clearInterval(miningInterval);
}

async function updateMiningPower() {
    const powerSelect = document.getElementById('mining-power');
    const powerDisplay = document.getElementById('current-power');
    
    switch(powerSelect.value) {
        case 'low':
            miningPower = 0.25;
            break;
        case 'medium':
            miningPower = 0.5;
            break;
        case 'high':
            miningPower = 0.75;
            break;
        case 'max':
            miningPower = 1;
            break;
    }
    
    // Update mining power on server
    if (isMining) {
        await fetch('/mining/power', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mining_power: miningPower })
        });
    }
    
    powerDisplay.textContent = `${miningPower * 100}%`;
}

// Check mining state on page load
async function checkMiningState() {
    const response = await fetch('/mining/stats');
    const data = await response.json();
    
    if (data.is_mining) {
        isMining = true;
        miningPower = data.mining_power;
        const button = document.getElementById('mining-toggle');
        button.innerHTML = '<i class="fas fa-stop"></i> Stop Mining';
        button.style.backgroundColor = '#f44336';
        startMining();
        
        // Update mining power display
        const powerSelect = document.getElementById('mining-power');
        const powerDisplay = document.getElementById('current-power');
        powerSelect.value = miningPower === 0.25 ? 'low' : 
                           miningPower === 0.5 ? 'medium' :
                           miningPower === 0.75 ? 'high' : 'max';
        powerDisplay.textContent = `${miningPower * 100}%`;
    }
}

// Call checkMiningState when page loads
if (document.getElementById('dashboard')) {
    checkMiningState();
}

// QR Code
function showQRCode() {
    const modal = document.getElementById('qr-modal');
    const qrcodeDiv = document.getElementById('qrcode');
    qrcodeDiv.innerHTML = ''; // Clear previous QR code
    
    const userId = document.querySelector('.user-id').textContent.split(': ')[1];
    new QRCode(qrcodeDiv, {
        text: userId,
        width: 200,
        height: 200
    });
    
    modal.style.display = 'block';
}

// Copy User ID
function copyUserId() {
    const userId = document.querySelector('.user-id').textContent.split(': ')[1];
    navigator.clipboard.writeText(userId).then(() => {
        alert('User ID copied to clipboard!');
    });
}

// Close Modal
document.querySelector('.close')?.addEventListener('click', () => {
    document.getElementById('qr-modal').style.display = 'none';
});

// Mining Stats Update
function updateMiningStats() {
    if (!isMining) return;
    
    fetch('/mining/stats')
        .then(response => response.json())
        .then(data => {
            const currentBalance = data.current_balance;
            const oldBalance = parseFloat(document.getElementById('balance').textContent);
            
            // Show notification for mining rewards
            if (currentBalance > oldBalance) {
                const earned = (currentBalance - oldBalance).toFixed(2);
                showNotification(`Mined ${earned} GRIV`, 'success');
            }
            
            // Check if max GRIV reached
            if (currentBalance >= MAX_GADA) {
                stopMining();
                const button = document.getElementById('mining-toggle');
                button.innerHTML = '<i class="fas fa-play"></i> Start Mining';
                button.style.backgroundColor = '';
                isMining = false;
                alert('Maximum GRIV limit reached (1619 GRIV)');
                return;
            }
            
            document.getElementById('mining-rate').textContent = 
                (data.rate * miningPower).toFixed(2) + ' GRIV/min';
            document.getElementById('active-users').textContent = data.active_users;
            document.getElementById('balance').textContent = 
                currentBalance.toFixed(2) + ' GRIV';
                
            // Update progress bar
            const progressBar = document.querySelector('.progress-bar');
            const limitText = document.querySelector('.limit-text');
            const percentage = (currentBalance / MAX_GADA * 100).toFixed(2);
            progressBar.style.width = percentage + '%';
            limitText.textContent = percentage + '% of max';
        })
        .catch(console.error);
}

// Transfer Form
document.getElementById('transfer-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const submitButton = e.target.querySelector('button[type="submit"]');
    
    try {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        
        const response = await fetch('/transfer', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(data.message, 'success');
            location.reload();
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        showNotification('Transfer failed. Please try again.', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
    }
});

// Format UUID as user types
document.getElementById('receiver_id')?.addEventListener('input', (e) => {
    let value = e.target.value.replace(/[^a-f0-9]/gi, '');
    if (value.length > 32) value = value.slice(0, 32);
    
    // Format with dashes
    const parts = [
        value.slice(0, 8),
        value.slice(8, 12),
        value.slice(12, 16),
        value.slice(16, 20),
        value.slice(20, 32)
    ];
    
    e.target.value = parts.filter(part => part).join('-');
});

// Cleanup
window.addEventListener('beforeunload', () => {
    if (miningInterval) {
        clearInterval(miningInterval);
    }
});

// Notification function
function showNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = document.createElement('i');
    icon.className = `fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}`;
    
    const text = document.createElement('span');
    text.textContent = message;
    
    notification.appendChild(icon);
    notification.appendChild(text);
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
} 