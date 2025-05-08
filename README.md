# Anime Scraper

A modern web scraper that aggregates content from AnimeWorld and LiveChart, built with Python/Flask and a minimalistic Swift/XCode-inspired UI.

## 🚀 Technical Characteristics

### Backend (Python/Flask)
- Advanced web scraping with `cloudscraper` to bypass anti-bot protections
- Caching system to optimize requests
- Error handling and detailed logging
- RESTful API for anime data management

### Frontend (HTML/CSS/JavaScript)
- Responsive design optimized for mobile and desktop
- Minimalist Swift/XCode style UI
- Smooth horizontal scrolling with snap points
- Lazy loading of images for optimized performance

### Main Sections
1. **Most Popular**: Scraped from `animeworld.so/filter?sort=6`
2. **Latest Releases**: Scraped from `animeworld.so/newest`
3. **Daily Calendar**: Integration with `livechart.me/schedule`
4. **Latest Episodes**: Scraped from `animeworld.so/updated`

## 🛠 Technologies Use

- **Backend**:
  - Python 3.x
  - Flask
  - BeautifulSoup4
  - Cloudscraper
  - Logging

- **Frontend**:
  - HTML5
  - CSS3 (CSS Variables, Flexbox, Grid)
  - JavaScript (ES6+)
  - Font Awesome
  - SF Pro Display Font

## 📱 Responsive Design

- Fluid layout that adapts to different screen sizes
- Optimized breakpoints for:
- Desktop (> 768px)
- Tablet (≤ 768px)
- Mobile (≤ 480px)
- Touch-friendly controls on mobile devices

## 🔍 Search Features

- Real-time anime search
- Results formatted in responsive cards
- Error handling and loading states

## 🎨 UI/UX Features

- Modern dark theme
- Smooth animations
- Horizontal scroll with intuitive controls
- Cards with hover effects
- Loading states and error handling

## 📦 Project Structure
The project structure is organized as follows:
- `static/`: Contains static files
- `css/`: CSS styles
- `js/`: JavaScript scripts
- `templates/`: Contains HTML templates
- `app.py`: Main file of the Flask application

## 🚀 Performance

- Lazy image loading
- Data caching
- API request optimization
- Efficient scroll management
