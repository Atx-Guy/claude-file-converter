// static/js/theme-toggle.js

document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('themeToggle');
    const body = document.body;
    const themeIcon = themeToggleBtn.querySelector('i');
    const themeText = themeToggleBtn.querySelector('.theme-text');
    
    // Check for saved theme preference or use system preference
    const getCurrentTheme = () => {
        const savedTheme = document.cookie
            .split('; ')
            .find(row => row.startsWith('theme='));
        
        if (savedTheme) {
            return savedTheme.split('=')[1];
        }
        
        // If no saved preference, check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    };
    
    // Apply theme based on current preference
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            themeIcon.classList.remove('bi-moon-stars');
            themeIcon.classList.add('bi-sun');
            themeText.textContent = 'Light Mode';
        } else {
            body.classList.remove('dark-theme');
            themeIcon.classList.remove('bi-sun');
            themeIcon.classList.add('bi-moon-stars');
            themeText.textContent = 'Dark Mode';
        }
    };
    
    // Set theme on initial load
    const currentTheme = getCurrentTheme();
    applyTheme(currentTheme);
    
    // Toggle theme when button is clicked
    themeToggleBtn.addEventListener('click', () => {
        const newTheme = body.classList.contains('dark-theme') ? 'light' : 'dark';
        
        // Save preference to cookie (expires in 365 days)
        const expiryDate = new Date();
        expiryDate.setTime(expiryDate.getTime() + (365 * 24 * 60 * 60 * 1000));
        document.cookie = `theme=${newTheme}; expires=${expiryDate.toUTCString()}; path=/`;
        
        // Apply the new theme
        applyTheme(newTheme);
    });
});