from flask import Flask, render_template, jsonify, request, redirect, url_for, abort, session
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import logging
import re
import time
import pytz
from datetime import datetime
from urllib.parse import quote
from pymongo import MongoClient
import os

app = Flask(__name__)

# Configurazione logging più dettagliata
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Variabile globale per memorizzare i dati degli anime
anime_data = {
    'popular': [],
    'newest': [],
    'updated': [],
    'search': []
}

def extract_anime_data(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        anime_items = soup.select('.film-list .item')
        
        extracted_data = []
        for index, item in enumerate(anime_items, 1):
            try:
                # Otteniamo il link completo
                base_url = 'https://www.animeworld.so'
                link_element = item.select_one('a.poster')
                original_link = base_url + link_element['href'] if link_element else ''
                
                anime = {
                    'title': item.select_one('.name').text.strip() if item.select_one('.name') else 'N/A',
                    'image': item.select_one('img')['src'] if item.select_one('img') else '',
                    'episode': item.select_one('.ep').text.strip() if item.select_one('.ep') else '',
                    'anime_id': str(index),
                    'original_link': original_link  # Salviamo il link completo
                }
                extracted_data.append(anime)
                
            except Exception as e:
                logger.error(f"Error extracting single anime: {str(e)}")
                continue
            
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error in extract_anime_data: {str(e)}")
        return []

def get_anime_data(url):
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        logger.debug(f"Requesting URL: {url}")
        response = scraper.get(url)
        
        if response.status_code == 200 or response.status_code == 202:
            # Gestione del redirect se necessario
            if response.status_code == 202:
                # Estrai il cookie SecurityAW-gl
                security_cookie_match = re.search(r'SecurityAW-gl=([^;]+)', response.text)
                if security_cookie_match:
                    security_cookie = security_cookie_match.group(1)
                    logger.debug(f"Found SecurityAW-gl cookie: {security_cookie}")
                    
                    # Aggiungi il cookie
                    scraper.cookies.set('SecurityAW-gl', security_cookie, domain='www.animeworld.so')
                    
                    # Estrai l'URL di redirect
                    redirect_match = re.search(r'location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', response.text)
                    if redirect_match:
                        redirect_url = redirect_match.group(1)
                        if not redirect_url.startswith('http'):
                            redirect_url = f"https://www.animeworld.so{redirect_url.lstrip('/')}"
                        
                        logger.debug(f"Following redirect to: {redirect_url}")
                        
                        # Fai la seconda richiesta
                        time.sleep(1)  # Piccola pausa
                        response = scraper.get(redirect_url)
                        logger.debug(f"Redirect response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            anime_items = soup.select('.film-list .item')
                            logger.debug(f"Found {len(anime_items)} anime items")
                            
                            extracted_data = []
                            for item in anime_items:
                                try:
                                    # Ottieni il link corretto dall'elemento poster
                                    poster_link = item.select_one('a.poster')
                                    original_link = f"https://www.animeworld.so{poster_link['href']}" if poster_link else None
                                    
                                    anime = {
                                        'title': item.select_one('.name').text.strip() if item.select_one('.name') else 'N/A',
                                        'image': item.select_one('img')['src'] if item.select_one('img') else '',
                                        'episode': item.select_one('.ep').text.strip() if item.select_one('.ep') else '',
                                        'original_link': original_link  # Salviamo il link completo
                                    }
                                    extracted_data.append(anime)
                                    logger.debug(f"Extracted anime: {anime}")
                                except Exception as e:
                                    logger.error(f"Error extracting anime data: {e}")
                                    continue
                            
                            return extracted_data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            anime_items = soup.select('.film-list .item')
            logger.debug(f"Found {len(anime_items)} anime items")
            
            extracted_data = []
            for item in anime_items:
                try:
                    # Ottieni il link corretto dall'elemento poster
                    poster_link = item.select_one('a.poster')
                    original_link = f"https://www.animeworld.so{poster_link['href']}" if poster_link else None
                    
                    anime = {
                        'title': item.select_one('.name').text.strip() if item.select_one('.name') else 'N/A',
                        'image': item.select_one('img')['src'] if item.select_one('img') else '',
                        'episode': item.select_one('.ep').text.strip() if item.select_one('.ep') else '',
                        'original_link': original_link  # Salviamo il link completo
                    }
                    extracted_data.append(anime)
                    logger.debug(f"Extracted anime: {anime}")
                except Exception as e:
                    logger.error(f"Error extracting anime data: {e}")
                    continue
            
            return extracted_data
            
    except Exception as e:
        logger.error(f"Error in get_anime_data: {str(e)}", exc_info=True)
        return []

def get_anime_details(anime_id):
    url = f"https://www.animeworld.so/api/tooltip/{anime_id}"
    response = requests.get(url)
    return response.json()

def get_schedule_data(url):
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        logger.debug(f"Requesting schedule from: {url}")
        response = scraper.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trova il contenitore del giorno corrente
            today_container = soup.select_one('.lc-timetable-day.lc-today')
            if not today_container:
                logger.error("Today's schedule container not found")
                return []
                
            # Estrai la data
            date_container = today_container.select_one('.lc-timetable-day__heading .text-2xl')
            date_detail = today_container.select_one('.text-xl')
            today_date = f"{date_container.text} {date_detail.text}" if date_container and date_detail else "Today"
            
            schedule_items = []
            timeslots = today_container.select('.lc-timetable-timeslot')
            
            for slot in timeslots:
                try:
                    time_element = slot.select_one('.lc-timetable-timeslot__time .lc-time span')
                    anime_block = slot.select_one('.lc-timetable-anime-block')
                    
                    if time_element and anime_block:
                        time = time_element.text.strip()
                        title = anime_block.select_one('.lc-tt-anime-title').text.strip()
                        
                        # Modifica qui: ottieni l'URL dell'immagine in qualità migliore
                        image_element = anime_block.select_one('img')
                        image = image_element['src'] if image_element else ''
                        # Sostituisci 'small' con 'large' nell'URL dell'immagine
                        image = image.replace('small', 'large')
                        
                        episode_info = anime_block.select_one('.lc-tt-release-label').text.strip()
                        
                        schedule_items.append({
                            'time': time,
                            'title': title,
                            'image': image,
                            'episode_info': episode_info
                        })
                except Exception as e:
                    logger.error(f"Error parsing schedule item: {str(e)}")
                    continue
            
            return {
                'date': today_date,
                'items': schedule_items
            }
            
        else:
            logger.error(f"Error status code from LiveChart: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}", exc_info=True)
        return []

def get_anime_details_from_url(url):
    try:
        logger.debug(f"Fetching details from URL: {url}")
        scraper = cloudscraper.create_scraper()
        
        # Prima richiesta
        response = scraper.get(url)
        max_redirects = 5  # Preveniamo loop infiniti
        current_redirect = 0
        
        while response.status_code == 202 and current_redirect < max_redirects:
            # Estrai e imposta il cookie
            security_cookie_match = re.search(r'SecurityAW-gl=([^;]+)', response.text)
            if security_cookie_match:
                security_cookie = security_cookie_match.group(1)
                logger.debug(f"Setting cookie: SecurityAW-gl={security_cookie}")
                scraper.cookies.set('SecurityAW-gl', security_cookie, domain='www.animeworld.so')
                
                # Estrai l'URL di redirect
                redirect_match = re.search(r'location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', response.text)
                if redirect_match:
                    redirect_url = redirect_match.group(1)
                    if not redirect_url.startswith('https'):
                        redirect_url = f"https://www.animeworld.so{redirect_url.split('.so')[-1]}"
                    
                    logger.debug(f"Following redirect #{current_redirect + 1} to: {redirect_url}")
                    
                    # Richiesta con cookie
                    headers = {
                        'Cookie': f'SecurityAW-gl={security_cookie}',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    response = scraper.get(redirect_url, headers=headers)
                    current_redirect += 1
                    logger.debug(f"Response {current_redirect}: status={response.status_code}")
            else:
                break
        
        if response.status_code != 200:
            logger.error(f"Failed after {current_redirect} redirects with status code: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.debug(f"Final page title: {soup.title.string if soup.title else 'No title'}")
        
        # Contenitore principale delle info
        info_widget = soup.select_one('.widget.info')
        if not info_widget:
            logger.error("Info widget non trovato")
            return None
            
        details = {}
        
        # Estrazione dati principali
        info_widget = soup.select_one('.widget.info')
        if not info_widget:
            logger.error("Info widget non trovato")
            return None
            
        # Immagine di copertina
        thumb = info_widget.select_one('.thumb img')
        if thumb:
            details['image'] = thumb.get('src', '')
            
        # Titolo principale
        title = info_widget.select_one('.title')
        if title:
            details['title'] = title.text.strip()
            
        # Titolo alternativo
        alt_title = info_widget.select_one('.alt-title')
        if alt_title:
            details['alt_title'] = alt_title.text.strip()
            
        # Rating
        rating_div = info_widget.select_one('.rating')
        if rating_div:
            details['rating'] = rating_div.get('data-value', 'N/A')
            
        # Descrizione completa
        desc = info_widget.select_one('.desc')
        if desc:
            details['description'] = desc.text.strip()
            
        # Meta info dalla prima colonna
        meta_cols = info_widget.select('.meta')
        if len(meta_cols) >= 2:
            col1, col2 = meta_cols[:2]
            
            # Prima colonna
            details['category'] = col1.select_one('dt:contains("Categoria:") + dd').text.strip() if col1.select_one('dt:contains("Categoria:") + dd') else None
            details['audio'] = col1.select_one('dt:contains("Audio:") + dd').text.strip() if col1.select_one('dt:contains("Audio:") + dd') else None
            details['release_date'] = col1.select_one('dt:contains("Data di Uscita:") + dd').text.strip() if col1.select_one('dt:contains("Data di Uscita:") + dd') else None
            details['season'] = col1.select_one('dt:contains("Stagione:") + dd').text.strip() if col1.select_one('dt:contains("Stagione:") + dd') else None
            details['studio'] = col1.select_one('dt:contains("Studio:") + dd').text.strip() if col1.select_one('dt:contains("Studio:") + dd') else None
            
            # Generi
            genres_dd = col1.select_one('dt:contains("Genere:") + dd')
            if genres_dd:
                details['genres'] = [a.text.strip() for a in genres_dd.select('a')]
            
            # Seconda colonna
            details['duration'] = col2.select_one('dt:contains("Durata:") + dd').text.strip() if col2.select_one('dt:contains("Durata:") + dd') else None
            details['episodes_count'] = col2.select_one('dt:contains("Episodi:") + dd').text.strip() if col2.select_one('dt:contains("Episodi:") + dd') else None
            details['status'] = col2.select_one('dt:contains("Stato:") + dd').text.strip() if col2.select_one('dt:contains("Stato:") + dd') else None
            details['views'] = col2.select_one('dt:contains("Visualizzazioni:") + dd').text.strip() if col2.select_one('dt:contains("Visualizzazioni:") + dd') else None
            
            # Voto medio e numero voti
            vote_info = info_widget.select_one('.rating-info')
            if vote_info:
                details['vote_average'] = vote_info.select_one('.average').text.strip() if vote_info.select_one('.average') else None
                details['vote_count'] = vote_info.select_one('.count').text.strip() if vote_info.select_one('.count') else None
        
        # Estrazione stagioni ed episodi
        widget_body = soup.select_one('#main')
        if widget_body:
            logger.debug("Found main container")
            
            # Inizializza episodes e ranges
            details['episodes'] = {}
            details['ranges'] = []
            
            # Prima controlla se ci sono range titles
            range_titles = widget_body.select('span.rangetitle')
            logger.debug(f"Found {len(range_titles)} range titles")
            
            # Se non ci sono range titles, è una singola stagione
            if not range_titles:
                logger.debug("No range titles found - Single season detected")
                
                # Usa un set per tenere traccia degli episodi unici
                seen_episodes = set()
                episodes = []
                
                all_episodes = widget_body.select('li.episode a')
                for episode in all_episodes:
                    episode_num = episode.get('data-episode-num')
                    # Controlla se abbiamo già visto questo numero di episodio
                    if episode_num not in seen_episodes:
                        seen_episodes.add(episode_num)
                        episode_data = {
                            'id': episode.get('data-episode-id'),
                            'number': episode_num,
                            'url': f"https://www.animeworld.so{episode.get('href')}",
                            'title': f"Episodio {episode_num}",
                            'active': 'active' in episode.get('class', [])
                        }
                        episodes.append(episode_data)
                
                details['episodes']['0'] = episodes
                details['ranges'] = [{
                    'id': '0',
                    'title': 'Episodi',
                    'active': True
                }]
                logger.debug(f"Added single season with {len(episodes)} unique episodes")
            else:
                # Gestione multiple ranges
                ranges_dict = {}
                for range_span in range_titles:
                    range_id = range_span.get('data-range-id')
                    if range_id and range_id not in ranges_dict:
                        ranges_dict[range_id] = {
                            'id': range_id,
                            'title': range_span.text.strip(),
                            'active': 'active' in range_span.get('class', [])
                        }
                
                # Cerca gli episodi per ogni range
                for range_id in ranges_dict:
                    episode_list = widget_body.select_one(f'ul.episodes.range[data-range-id="{range_id}"]')
                    if episode_list:
                        seen_episodes = set()  # Set per episodi unici in questo range
                        episodes = []
                        
                        episode_items = episode_list.select('li.episode a')
                        for episode in episode_items:
                            episode_num = episode.get('data-episode-num')
                            # Controlla se abbiamo già visto questo numero di episodio
                            if episode_num not in seen_episodes:
                                seen_episodes.add(episode_num)
                                episode_data = {
                                    'id': episode.get('data-episode-id'),
                                    'number': episode_num,
                                    'url': f"https://www.animeworld.so{episode.get('href')}",
                                    'title': f"Episodio {episode_num}",
                                    'active': 'active' in episode.get('class', [])
                                }
                                episodes.append(episode_data)
                        
                        details['episodes'][range_id] = episodes
                        details['ranges'].append(ranges_dict[range_id])
                        logger.debug(f"Added range {ranges_dict[range_id]['title']} with {len(episodes)} unique episodes")

            logger.debug(f"Final ranges structure: {details['ranges']}")
            logger.debug(f"Final episodes count per range: {dict((k, len(v)) for k, v in details['episodes'].items())}")
            
        return details
        
    except Exception as e:
        logger.error(f"Errore nell'estrazione dei dettagli: {str(e)}", exc_info=True)
        return None

@app.route('/')
def home():
    try:
        # Ottieni i dati per ogni sezione
        popular = get_anime_data('https://www.animeworld.so/filter?sort=6')
        newest = get_anime_data('https://www.animeworld.so/newest')
        updated = get_anime_data('https://www.animeworld.so/updated')
        
        # Assegna ID univoci a ogni anime
        def assign_ids(anime_list, prefix):
            for i, anime in enumerate(anime_list, 1):
                anime['anime_id'] = f"{prefix}{i}"
            return anime_list
        
        # Assegna ID e salva i dati
        global anime_data
        anime_data['popular'] = assign_ids(popular, 'p')
        anime_data['newest'] = assign_ids(newest, 'n')
        anime_data['updated'] = assign_ids(updated, 'u')
        
        # Salva i dati anche nella sessione
        session['anime_data'] = anime_data
        
        # Debug log
        logger.debug(f"Popular anime count: {len(popular)}")
        logger.debug(f"Newest anime count: {len(newest)}")
        logger.debug(f"Updated anime count: {len(updated)}")
        logger.debug("Sample popular anime:", popular[0] if popular else "No popular anime")
        
        # Ottieni il calendario
        schedule = get_schedule_data('https://www.livechart.me/schedule')
        
        return render_template('index.html',
                             popular_data=json.dumps(anime_data['popular']),
                             newest_data=json.dumps(anime_data['newest']),
                             updated_data=json.dumps(anime_data['updated']),
                             schedule_data=json.dumps(schedule))
                             
    except Exception as e:
        logger.error(f"Error in route /: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/search')
def search():
    query = request.args.get('keyword', '').strip()
    if not query:
        return redirect(url_for('home'))
        
    try:
        url = f"https://www.animeworld.so/search?keyword={quote(query)}"
        results = get_anime_data(url)  # Usa la stessa funzione di scraping
        
        # Debug log per verificare i risultati
        logger.debug(f"Search results for '{query}': {results}")
        
        # Assegna ID univoci ai risultati della ricerca
        search_results = []
        for i, item in enumerate(results, 1):
            item['anime_id'] = f"s{i}"  # 's' per search
            search_results.append(item)
            
        # Aggiorna i dati globali
        anime_data['search'] = search_results
        
        return render_template('search_results.html', 
                             query=query,
                             results=json.dumps(search_results))
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return render_template('search_results.html', 
                             query=query,
                             results=json.dumps([]),
                             error="Si è verificato un errore durante la ricerca")

@app.route('/anime/<anime_id>')
def anime_detail(anime_id):
    try:
        logger.debug(f"Richiesta dettagli per anime_id: {anime_id}")
        
        # Recupera i dati dalla sessione se anime_data è vuoto
        global anime_data
        if not any(anime_data.values()):
            stored_data = session.get('anime_data')
            if stored_data:
                anime_data = stored_data
                logger.debug("Dati recuperati dalla sessione")
            else:
                logger.error("Nessun dato trovato nella sessione")
                return redirect(url_for('home'))
        
        # Cerca l'anime nelle sezioni
        prefix = anime_id[0]
        section = {
            'p': 'popular',
            'n': 'newest',
            'u': 'updated',
            's': 'search'
        }.get(prefix)
        
        if not section:
            logger.error(f"Prefisso ID non valido: {prefix}")
            return render_template('404.html'), 404
        
        # Trova l'anime nella sezione appropriata
        anime_base = next(
            (anime for anime in anime_data[section] if anime['anime_id'] == anime_id),
            None
        )
        
        if not anime_base:
            logger.error(f"Nessun anime trovato per id: {anime_id}")
            logger.debug(f"Dati disponibili: {anime_data}")
            return redirect(url_for('home'))
            
        # Ottieni l'URL originale e scarica i dettagli completi
        original_link = anime_base.get('original_link')
        if not original_link:
            logger.error("Link originale non trovato")
            return render_template('error.html', message="Link non disponibile"), 500
            
        logger.debug(f"Scaricando dettagli da: {original_link}")
        detailed_info = get_anime_details_from_url(original_link)
        
        if not detailed_info:
            logger.error("Impossibile ottenere dettagli aggiuntivi")
            return render_template('error.html', message="Impossibile caricare i dettagli"), 500
            
        # Mantieni l'ID originale mentre unisci i dettagli
        detailed_info['anime_id'] = anime_id
        anime_details = {**anime_base, **detailed_info}
        
        logger.debug(f"Dettagli completi ottenuti: {anime_details}")
        return render_template('anime_detail.html', anime=anime_details)
        
    except Exception as e:
        logger.error(f"Error in anime detail page: {str(e)}", exc_info=True)
        return render_template('error.html', message="Si è verificato un errore"), 500

@app.route('/get-video-url', methods=['POST'])
def get_video_url():
    try:
        data = request.get_json()
        episode_url = data.get('url')
        
        if not episode_url:
            return jsonify({'error': 'URL non fornito'}), 400
            
        logger.debug(f"Richiesta URL video per: {episode_url}")
        
        # Estrai l'ID dell'episodio dall'URL
        episode_id = episode_url.split('/')[-1]
        
        # Costruisci l'URL dell'API
        api_url = f"https://www.animeworld.so/api/episode/serverPlayerAnimeWorld?id={episode_id}"
        logger.debug(f"Richiesta API: {api_url}")
        
        scraper = cloudscraper.create_scraper()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': episode_url
        }
        
        # Prima richiesta per ottenere il cookie
        response = scraper.get(api_url, headers=headers)
        
        if response.status_code == 202:
            # Estrai il cookie di sicurezza
            security_cookie_match = re.search(r'SecurityAW-gl=([^;]+)', response.text)
            if security_cookie_match:
                security_cookie = security_cookie_match.group(1)
                
                # Aggiungi il cookie alla richiesta successiva
                headers['Cookie'] = f'SecurityAW-gl={security_cookie}'
                
                # Fai la seconda richiesta con il parametro d=1
                api_url_with_d = f"{api_url}&d=1"
                logger.debug(f"Seconda richiesta API con cookie: {api_url_with_d}")
                
                response = scraper.get(api_url_with_d, headers=headers)
        
        if response.status_code == 200:
            # Analizza l'HTML per trovare il tag video
            soup = BeautifulSoup(response.text, 'html.parser')
            video_source = soup.select_one('video source')
            
            if video_source and video_source.get('src'):
                video_url = video_source['src']
                logger.debug(f"URL video trovato: {video_url}")
                return jsonify({'videoUrl': video_url})
            else:
                logger.error("Tag video source non trovato nell'HTML")
                logger.debug(f"HTML ricevuto: {response.text[:500]}...")
        
        logger.error(f"Risposta API: {response.status_code}")
        return jsonify({'error': 'URL del video non trovato'}), 404
        
    except Exception as e:
        logger.error(f"Errore nell'estrazione dell'URL del video: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Aggiungi una chiave segreta per la sessione
app.secret_key = 'la_tua_chiave_segreta_qui'  # Cambia questa con una chiave sicura

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))