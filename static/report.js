/* report.js */
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('evidence');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                console.log('File selected:', this.files[0].name);
            }
        });
    }
});
