document.addEventListener('DOMContentLoaded', function() {
    // Funzione per gestire lo scroll di tutte le sezioni
    function initializeScroll(container) {
        const list = container.querySelector('.anime-list, .schedule-list');
        const leftBtn = container.querySelector('.scroll-btn.left');
        const rightBtn = container.querySelector('.scroll-btn.right');
        
        // Calcola quante card sono completamente visibili nella viewport
        function getVisibleCards() {
            const containerWidth = list.clientWidth;
            const cardWidth = list.classList.contains('schedule-list') ? 300 : 200;
            const gap = 20;
            return Math.floor(containerWidth / (cardWidth + gap));
        }
        
        // Calcola lo scroll amount per mostrare una nuova "pagina" completa
        function getScrollAmount() {
            const cardWidth = list.classList.contains('schedule-list') ? 300 : 200;
            const gap = 20;
            const visibleCards = getVisibleCards();
            // Moltiplichiamo per il numero di card visibili per scorrere un'intera "pagina"
            return (cardWidth + gap) * visibleCards;
        }
        
        function updateButtonVisibility() {
            const isAtStart = list.scrollLeft <= 0;
            const isAtEnd = list.scrollLeft >= list.scrollWidth - list.clientWidth - 10;
            
            leftBtn.style.opacity = isAtStart ? '0' : '1';
            leftBtn.style.pointerEvents = isAtStart ? 'none' : 'auto';
            
            rightBtn.style.opacity = isAtEnd ? '0' : '1';
            rightBtn.style.pointerEvents = isAtEnd ? 'none' : 'auto';
        }
        
        leftBtn.addEventListener('click', () => {
            const scrollAmount = getScrollAmount();
            list.scrollBy({
                left: -scrollAmount,
                behavior: 'smooth'
            });
        });
        
        rightBtn.addEventListener('click', () => {
            const scrollAmount = getScrollAmount();
            list.scrollBy({
                left: scrollAmount,
                behavior: 'smooth'
            });
        });
        
        // Gestione touch scroll per mobile
        let touchStart = 0;
        let touchEnd = 0;
        
        list.addEventListener('touchstart', (e) => {
            touchStart = e.changedTouches[0].screenX;
        });
        
        list.addEventListener('touchend', (e) => {
            touchEnd = e.changedTouches[0].screenX;
            const scrollAmount = getScrollAmount();
            if (touchStart - touchEnd > 50) {  // Swipe left
                list.scrollBy({
                    left: scrollAmount,
                    behavior: 'smooth'
                });
            } else if (touchEnd - touchStart > 50) {  // Swipe right
                list.scrollBy({
                    left: -scrollAmount,
                    behavior: 'smooth'
                });
            }
        });
        
        // Aggiorna visibilità pulsanti
        updateButtonVisibility();
        list.addEventListener('scroll', updateButtonVisibility);
        window.addEventListener('resize', updateButtonVisibility);
    }
    
    // Inizializza lo scroll per tutte le sezioni
    document.querySelectorAll('.scroll-container').forEach(container => {
        initializeScroll(container);
    });
    
    // Popola le sezioni con i dati
    function createAnimeCards(data, containerId) {
        const container = document.getElementById(containerId);
        if (!container || !data) return;
        
        container.innerHTML = '';
        data.forEach(anime => {
            const card = document.createElement('div');
            card.className = 'anime-card';
            
            // Usa il nostro ID personalizzato
            const animeId = anime.anime_id;
            
            console.log('Anime data:', {
                title: anime.title,
                id: animeId
            });
            
            card.innerHTML = `
                <a href="/anime/${animeId}" class="anime-card-link">
                    <div class="anime-image">
                        <img src="${anime.image}" alt="${anime.title}" loading="lazy">
                        ${anime.episode ? `<div class="episode-badge">${anime.episode}</div>` : ''}
                    </div>
                    <div class="anime-info">
                        <h3 class="anime-title">${anime.title}</h3>
                    </div>
                </a>
            `;
            
            container.appendChild(card);
        });
    }
    
    // Popola le sezioni
    createAnimeCards(popularData, 'popular-list');
    createAnimeCards(newestData, 'newest-list');
    createAnimeCards(updatedData, 'updated-list');
}); 

function createAnimeCard(anime) {
    return `
        <div class="anime-card">
            <a href="/anime/${anime.anime_id}">
                <img src="${anime.image}" alt="${anime.title}" class="anime-poster">
            </a>
            <div class="anime-info">
                <h3>${anime.title}</h3>
                <p>${anime.episode}</p>
            </div>
        </div>
    `;
} 