// dark_mode.js

const darkModeCheckbox = document.getElementById('dark-mode-checkbox');
const body = document.body;

// Function to toggle dark mode
function toggleDarkMode() {
    body.classList.toggle('dark-mode');
}

// Event listener for dark mode toggle checkbox
darkModeCheckbox.addEventListener('change', toggleDarkMode);
