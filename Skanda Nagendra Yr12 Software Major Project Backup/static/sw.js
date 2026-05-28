const CACHE_NAME = 'sen-pwa-v1';
const FILES_TO_CACHE = [
'/',
'/templates/index.html',
'/templates/login.html',
'/templates/register.html',
'/templates/signpage.html',
'/templates/preparation.html',
'/templates/testpage.html',
'/static/style.css',
'/app.py',
'/manifest.json'
];



// Install: Save files to cache
self.addEventListener('install', (event) => {
event.waitUntil(
caches.open(CACHE_NAME).then((cache) => {
console.log('Caching files');
return cache.addAll(FILES_TO_CACHE);
})
);
});
// to use the service worker in app.py, the following code should be added to the base template
// <script>
// if ('serviceWorker' in navigator) {
// navigator.serviceWorker.register('sw.js').then(function(registration))}
// .catch(function(error)) {
// }

// Fetch: Use cached files when offline

self.addEventListener('fetch', (event) => {
event.respondWith(
caches.match(event.request).then((response) => {
return response || fetch(event.request);
})
);
});