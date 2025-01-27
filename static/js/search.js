document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    const searchResults = document.getElementById('search-results');
    let searchTimeout;

    // Mostra/nascondi il pulsante clear
    searchInput.addEventListener('input', function() {
        searchClear.style.display = this.value ? 'block' : 'none';
        
        clearTimeout(searchTimeout);
        if (this.value.length >= 3) {
            searchTimeout = setTimeout(() => performSearch(this.value), 300);
        } else {
            searchResults.classList.remove('active');
        }
    });

    // Clear button
    searchClear.addEventListener('click', function() {
        searchInput.value = '';
        searchInput.focus();
        searchClear.style.display = 'none';
        searchResults.classList.remove('active');
    });

    // Chiudi risultati quando si clicca fuori
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });

    async function performSearch(query) {
        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                displayResults(data.results);
            } else {
                displayNoResults();
            }
        } catch (error) {
            console.error('Error performing search:', error);
            displayError();
        }
    }

    function displayResults(results) {
        searchResults.innerHTML = '';
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
                <div class="search-result-image">
                    <img src="${result.image}" alt="${result.title}" loading="lazy">
                </div>
                <div class="search-result-info">
                    <h3 class="search-result-title">${result.title}</h3>
                    ${result.meta ? `<div class="search-result-meta">${result.meta}</div>` : ''}
                </div>
            `;
            
            item.addEventListener('click', () => {
                window.location.href = result.link;
            });
            
            searchResults.appendChild(item);
        });
        searchResults.classList.add('active');
    }

    function displayNoResults() {
        searchResults.innerHTML = `
            <div class="search-result-item">
                <div class="search-result-info">
                    <h3 class="search-result-title">Nessun risultato trovato</h3>
                </div>
            </div>
        `;
        searchResults.classList.add('active');
    }

    function displayError() {
        searchResults.innerHTML = `
            <div class="search-result-item">
                <div class="search-result-info">
                    <h3 class="search-result-title">Errore durante la ricerca</h3>
                </div>
            </div>
        `;
        searchResults.classList.add('active');
    }
}); 