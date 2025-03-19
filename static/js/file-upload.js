// static/js/file-upload.js

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const outputFormat = document.getElementById('outputFormat');
    const convertForm = document.getElementById('convertForm');
    
    // Only proceed if we're on a page with the file upload elements
    if (!fileInput || !dropZone) return;
    
    // File upload format options based on file type
    const formatOptions = {
        image: ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff'],
        audio: ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
        document: ['pdf', 'docx', 'txt', 'md', 'html']
    };
    
    // Drag and drop functionality
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            updateFileInfo();
        }
    });
    
    // File input change handler
    fileInput.addEventListener('change', updateFileInfo);
    
    // Update file info and show conversion options
    function updateFileInfo() {
        if (fileInput.files && fileInput.files[0]) {
            const file = fileInput.files[0];
            
            // Display file info
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            
            // Show file info section
            if (fileInfo) {
                fileInfo.classList.remove('d-none');
            }
            
            // Update output format options based on file type
            updateOutputFormats(file);
        }
    }
    
    // Update output format dropdown based on input file type
    function updateOutputFormats(file) {
        if (!outputFormat) return;
        
        // Clear existing options
        outputFormat.innerHTML = '<option value="">Select output format...</option>';
        
        // Determine file type
        const extension = getFileExtension(file.name).toLowerCase();
        let fileType = '';
        
        if (formatOptions.image.includes(extension)) {
            fileType = 'image';
        } else if (formatOptions.audio.includes(extension)) {
            fileType = 'audio';
        } else if (formatOptions.document.includes(extension)) {
            fileType = 'document';
        }
        
        // Add appropriate conversion options
        if (fileType) {
            formatOptions[fileType].forEach(format => {
                if (format !== extension) { // Don't allow converting to the same format
                    const option = document.createElement('option');
                    option.value = format;
                    option.textContent = format.toUpperCase();
                    outputFormat.appendChild(option);
                }
            });
            
            // Select first option as default
            if (outputFormat.options.length > 1) {
                outputFormat.selectedIndex = 1;
            }
        }
    }
    
   // In file-upload.js, replace the form submission handler

// Enhanced form submission with elegant notifications
document.getElementById('convertForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Show loading overlay
    document.getElementById('loadingOverlay').classList.add('show');
    
    // Use fetch API for AJAX submission
    fetch(this.action, {
        method: 'POST',
        body: new FormData(this)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Conversion failed');
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Create a download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Get filename from form if available or use default
        const customFilename = document.getElementById('customFilename');
        const outputFormat = document.getElementById('outputFormat');
        let filename = 'converted_file';
        
        if (customFilename && customFilename.value) {
            filename = `${customFilename.value}.${outputFormat.value}`;
        } else if (fileName && fileName.textContent) {
            const originalName = fileName.textContent.split('.')[0];
            filename = `${originalName}.${outputFormat.value}`;
        }
        
        a.download = filename;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        // Show success notification
        showNotification('success', 'Conversion successful!', `Your file "${filename}" has been downloaded.`);
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', 'Conversion failed', error.message || 'An error occurred during conversion. Please try again.');
    })
    .finally(() => {
        // Hide loading overlay
        document.getElementById('loadingOverlay').classList.remove('show');
    });
});

// Elegant notification system
function showNotification(type, title, message) {
    // Create notification container if it doesn't exist
    let notificationContainer = document.getElementById('notificationContainer');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notificationContainer';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        notificationContainer.style.maxWidth = '350px';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.backgroundColor = type === 'success' ? '#4F46E5' : '#EF4444';
    notification.style.color = 'white';
    notification.style.padding = '16px';
    notification.style.borderRadius = '6px';
    notification.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
    notification.style.marginBottom = '10px';
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(40px)';
    notification.style.transition = 'all 0.3s ease-in-out';
    
    // Add notification content
    notification.innerHTML = `
        <div style="display: flex; align-items: flex-start;">
            <div style="margin-right: 12px; font-size: 20px;">
                <i class="bi ${type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle'}"></i>
            </div>
            <div>
                <h6 style="margin: 0 0 5px 0; font-weight: 600;">${title}</h6>
                <p style="margin: 0; font-size: 14px;">${message}</p>
            </div>
            <button style="background: none; border: none; color: white; margin-left: auto; cursor: pointer; font-size: 16px;" 
                    onclick="this.parentElement.parentElement.remove()">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `;
    
    // Add to the DOM
    notificationContainer.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(40px)';
        
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}
    
    // Helper function to get file extension
    function getFileExtension(filename) {
        return filename.split('.').pop();
    }
    
    // Helper function to format file size
    function formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }
});