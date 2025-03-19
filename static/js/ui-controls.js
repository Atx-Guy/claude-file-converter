// static/js/ui-controls.js

document.addEventListener('DOMContentLoaded', function() {
    // Loading overlay handling
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (loadingOverlay) {
        // Hide loading overlay when page is fully loaded
        window.addEventListener('load', function() {
            loadingOverlay.classList.remove('show');
        });
        
        // Add method to show/hide loading overlay globally
        window.showLoading = function() {
            loadingOverlay.classList.add('show');
        };
        
        window.hideLoading = function() {
            loadingOverlay.classList.remove('show');
        };
    }
    
    // Tooltip initialization (if Bootstrap 5 is used)
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Toast notifications (if any)
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    });
    
    // Dropdown hover effect for desktop
    const dropdowns = document.querySelectorAll('.navbar .dropdown');
    
    if (window.matchMedia('(min-width: 992px)').matches) {
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('mouseenter', function() {
                const dropdownMenu = this.querySelector('.dropdown-menu');
                if (dropdownMenu) {
                    const openDropdown = document.querySelector('.dropdown-menu.show');
                    if (openDropdown && openDropdown !== dropdownMenu) {
                        openDropdown.classList.remove('show');
                    }
                    dropdownMenu.classList.add('show');
                }
            });
            
            dropdown.addEventListener('mouseleave', function() {
                const dropdownMenu = this.querySelector('.dropdown-menu');
                if (dropdownMenu) {
                    dropdownMenu.classList.remove('show');
                }
            });
        });
    }
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            // Skip if it's a dropdown toggle or has other functionality
            if (this.getAttribute('data-bs-toggle') || targetId === '#') {
                return;
            }
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Adjust for header
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // File input customization
    const customFileInputs = document.querySelectorAll('.custom-file-input');
    customFileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (label && this.files.length) {
                if (this.files.length > 1) {
                    label.textContent = `${this.files.length} files selected`;
                } else {
                    label.textContent = this.files[0].name;
                }
            }
        });
    });
    
    // Form validation highlighting
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Back to top button
    const backToTopBtn = document.getElementById('backToTopBtn');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
});