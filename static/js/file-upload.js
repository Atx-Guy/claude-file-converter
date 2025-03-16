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
    
    // Form submission handler
    if (convertForm) {
        convertForm.addEventListener('submit', function() {
            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.classList.add('show');
            }
        });
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