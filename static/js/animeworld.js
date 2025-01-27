function parseAndDisplayAnime(html, container) {
    console.debug('Inizio parsing HTML:', html.substring(0, 200) + '...'); // Debug primi 200 caratteri
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const animeItems = doc.querySelectorAll('.film-list .item');
    
    console.debug(`Trovati ${animeItems.length} elementi anime`);
    
    container.innerHTML = '';
    
    if (animeItems.length === 0) {
        console.warn('Nessun anime trovato nel documento');
        container.innerHTML = '<p>Nessun risultato trovato</p>';
        return;
    }
    
    animeItems.forEach((item, index) => {
        try {
            const title = item.querySelector('.name')?.textContent.trim() || 'Titolo non disponibile';
            const link = item.querySelector('a')?.href || '#';
            const image = item.querySelector('img')?.src || '/static/img/placeholder.jpg';
            const episodeInfo = item.querySelector('.ep')?.textContent.trim() || '';
            const rating = item.querySelector('.rating')?.textContent.trim() || '';
            
            console.debug(`Parsing anime ${index + 1}:`, { title, link, image, episodeInfo, rating });
            
            const animeCard = document.createElement('div');
            animeCard.className = 'anime-card';
            animeCard.innerHTML = `
                <div class="anime-image">
                    <img src="${image}" alt="${title}" loading="lazy">
                    ${episodeInfo ? `<div class="episode-badge">${episodeInfo}</div>` : ''}
                </div>
                <div class="anime-info">
                    <h3 class="anime-title">${title}</h3>
                    ${rating ? `<div class="anime-rating">${rating}</div>` : ''}
                </div>
            `;
            
            animeCard.addEventListener('click', () => {
                window.location.href = link;
            });
            
            container.appendChild(animeCard);
        } catch (error) {
            console.error(`Errore nel parsing dell'anime ${index + 1}:`, error);
        }
    });
}

function parseSchedule(html, container) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const scheduleItems = doc.querySelectorAll('.schedule-item');
    
    container.innerHTML = ''; // Pulisce il contenitore
    
    if (scheduleItems.length === 0) {
        // Fallback a LiveChart.me
        const days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'];
        const today = new Date().getDay();
        
        const scheduleContainer = document.createElement('div');
        scheduleContainer.className = 'schedule-container';
        
        days.forEach((day, index) => {
            const dayCard = document.createElement('div');
            dayCard.className = `schedule-day ${(index + 1) === today ? 'today' : ''}`;
            dayCard.innerHTML = `
                <h3>${day}</h3>
                <div class="schedule-anime-list" id="schedule-${index}">
                    <p>Caricamento...</p>
                </div>
            `;
            scheduleContainer.appendChild(dayCard);
        });
        
        container.appendChild(scheduleContainer);
        
        // Qui potresti aggiungere una chiamata API a LiveChart.me
        fetchLiveChartSchedule();
    } else {
        scheduleItems.forEach(item => {
            const animeCard = createScheduleCard(item);
            container.appendChild(animeCard);
        });
    }
}

function createScheduleCard(item) {
    const title = item.querySelector('.title')?.textContent.trim() || 'Titolo non disponibile';
    const time = item.querySelector('.time')?.textContent.trim() || '';
    const image = item.querySelector('img')?.src || '/static/img/placeholder.jpg';
    
    const card = document.createElement('div');
    card.className = 'schedule-card';
    card.innerHTML = `
        <div class="schedule-image">
            <img src="${image}" alt="${title}" loading="lazy">
        </div>
        <div class="schedule-info">
            <h4>${title}</h4>
            ${time ? `<div class="schedule-time">${time}</div>` : ''}
        </div>
    `;
    
    return card;
}

async function fetchLiveChartSchedule() {
    try {
        const response = await fetch('/get_livechart_schedule');
        const data = await response.json();
        updateScheduleDisplay(data);
    } catch (error) {
        console.error('Errore nel caricamento del calendario:', error);
    }
}

function updateScheduleDisplay(scheduleData) {
    Object.entries(scheduleData).forEach(([day, animes]) => {
        const container = document.getElementById(`schedule-${day}`);
        if (container) {
            container.innerHTML = '';
            animes.forEach(anime => {
                const card = document.createElement('div');
                card.className = 'schedule-anime';
                card.innerHTML = `
                    <img src="${anime.image}" alt="${anime.title}">
                    <div class="schedule-anime-info">
                        <h4>${anime.title}</h4>
                        <span>${anime.time}</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    });
}