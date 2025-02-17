document.addEventListener('DOMContentLoaded', function() {
    // File input preview handlers
    function showPreview(input, previewElement) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewElement.src = e.target.result;
                previewElement.classList.remove('d-none');
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    // Clothing file input preview
    const clothingFile = document.getElementById('clothingFile');
    const clothingPreview = document.getElementById('clothingPreview');
    clothingFile.addEventListener('change', function() {
        showPreview(this, clothingPreview);
    });

    // Barcode file input preview
    const barcodeFile = document.getElementById('barcodeFile');
    const barcodePreview = document.getElementById('barcodePreview');
    barcodeFile.addEventListener('change', function() {
        showPreview(this, barcodePreview);
    });

    // Display recommendations
    function displayRecommendations(results, type) {
        const container = document.getElementById(type + 'RecommendationsContainer');
        const resultsDiv = document.getElementById(type + 'RecommendationResults');
        resultsDiv.innerHTML = '';

        results.forEach(item => {
            const col = document.createElement('div');
            col.className = 'col-6 col-sm-4';

            const img = document.createElement('img');
            img.src = item.url;
            img.className = 'img-fluid rounded';
            img.alt = 'Recommended item';

            col.appendChild(img);
            resultsDiv.appendChild(col);
        });

        container.classList.remove('d-none');
    }

    // Display matching item
    function displayMatchingItem(item) {
        const container = document.getElementById('matchingItemContainer');
        const resultDiv = document.getElementById('matchingResult');
        resultDiv.innerHTML = '';

        const img = document.createElement('img');
        img.src = item.url;
        img.className = 'img-fluid rounded';
        img.alt = 'Matching item';

        resultDiv.appendChild(img);
        container.classList.remove('d-none');
    }

    // Clothing form submission
    document.getElementById('clothingForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData();
        formData.append('file', clothingFile.files[0]);

        fetch('/upload_clothing', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRecommendations(data.recommendations, 'clothing');
            } else {
                alert(data.error || 'An error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            error.text().then(errorText => {
                try {
                    const errorData = JSON.parse(errorText);
                    alert(errorData.error || 'An error occurred');
                } catch(e) {
                    alert(errorText || 'An error occurred');
                }
            }).catch(e => {
                alert('An error occurred while processing your request');
            });
        });
    });

    // Barcode form submission
    document.getElementById('barcodeForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData();
        formData.append('file', barcodeFile.files[0]);

        fetch('/upload_barcode', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.recommendations) {
                displayRecommendations(data.recommendations, 'barcode');
            } else {
                alert(data.error || 'An error occurred processing the barcode');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            error.text().then(errorText => {
                try {
                    const errorData = JSON.parse(errorText);
                    alert(errorData.error || 'An error occurred');
                } catch(e) {
                    alert(errorText || 'An error occurred');
                }
            }).catch(e => {
                alert('An error occurred while processing your request');
            });
        });
    });
});