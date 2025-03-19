// static/js/global-form-handler.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification container
    createNotificationContainer();
    
    // Find all forms with the data-ajax-form attribute
    const ajaxForms = document.querySelectorAll('form[data-ajax-form]');
    
    ajaxForms.forEach(form => {
        initializeAjaxForm(form);
    });
    
    // Function to initialize Ajax form handling
    function initializeAjaxForm(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.classList.add('show');
            }
            
            // Use fetch API for AJAX submission
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Operation failed');
                    });
                }
                
                // Check if we're expecting JSON or a file download
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json().then(data => {
                        showNotification('success', 'Success!', data.message || 'Operation completed successfully.');
                    });
                } else {
                    return response.blob();
                }
            })
            .then(result => {
                // If result is a blob, handle the file download
                if (result instanceof Blob) {
                    // Create a download link
                    const url = window.URL.createObjectURL(result);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    
                    // Try to get filename from Content-Disposition or form fields
                    let filename = 'downloaded_file';
                    
                    // Look for custom filename field
                    const customFilenameInput = form.querySelector('[name="output_filename"], [name="custom_filename"]');
                    const formatInput = form.querySelector('[name="output_format"]');
                    
                    if (customFilenameInput && customFilenameInput.value) {
                        filename = customFilenameInput.value;
                        // Add extension if format input exists
                        if (formatInput && formatInput.value) {
                            if (!filename.endsWith('.' + formatInput.value)) {
                                filename += '.' + formatInput.value;
                            }
                        }
                    }
                    
                    a.download = filename;
                    
                    // Trigger download
                    document.body.appendChild(a);
                    a.click();
                    
                    // Clean up
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // Show success notification
                    showNotification('success', 'Download Started', `Your file "${filename}" is being downloaded.`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('error', 'Operation Failed', error.message || 'An error occurred. Please try again.');
            })
            .finally(() => {
                // Hide loading overlay
                if (loadingOverlay) {
                    loadingOverlay.classList.remove('show');
                }
            });
        });
    }
    
    // Function to create notification container
    function createNotificationContainer() {
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            document.body.appendChild(container);
        }
    }
    
    // Function to show notifications
    window.showNotification = function(type, title, message) {
        const notificationContainer = document.getElementById('notificationContainer');
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Add notification content
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="bi ${type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle'}"></i>
                </div>
                <div class="notification-text">
                    <h6 class="notification-title">${title}</h6>
                    <p class="notification-message">${message}</p>
                </div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `;
        
        // Add to the DOM
        notificationContainer.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
});