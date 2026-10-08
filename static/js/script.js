// ================================
// STATE
// ================================
let map, markerCluster, currentLocationMarker, currentRouteLayer;
let userLocation = null;
let searchLocation = null;
let locationConfirmed = false;
let mapMode = "jobs";       // "jobs" | "trades"
let currentSearchRadius = 50000;    // default 50 km
let seenOSMIds = new Set();
let searchDebounceTimer = null;
let mapMoveTimer = null;

// ================================
// PUNE MIDC ZONES (focus area)
// ================================
const PUNE_MIDC_ZONES = [
  { name: "Chakan MIDC", lat: 18.7580, lng: 73.8600, sector: "Manufacturing" },
  { name: "Bhosari MIDC", lat: 18.6400, lng: 73.8500, sector: "Manufacturing" },
  { name: "Ranjangaon MIDC", lat: 18.7220, lng: 74.1580, sector: "Engineering" },
  { name: "Hinjewadi MIDC", lat: 18.5910, lng: 73.7380, sector: "IT / Tech" },
  { name: "Pirangut MIDC", lat: 18.5100, lng: 73.6900, sector: "Chemical" },
  { name: "Talawade MIDC", lat: 18.6560, lng: 73.7980, sector: "IT / Tech" },
  { name: "Shirwal MIDC", lat: 18.1560, lng: 74.0700, sector: "Manufacturing" },
  { name: "Pimpri MIDC", lat: 18.6280, lng: 73.8000, sector: "Engineering" },
  { name: "Hadapsar MIDC", lat: 18.5020, lng: 73.9360, sector: "Manufacturing" },
  { name: "Sanaswadi MIDC", lat: 18.6800, lng: 74.0600, sector: "Engineering" },
];

// ================================
// FILTERS
// ================================
const JOB_FILTERS = [
  { label: "Full-time", icon: "red", ragQuery: "full time permanent job regular employment 8 hours fixed salary monthly" },
  { label: "Part-time", icon: "green", ragQuery: "part time job flexible hours weekend work few hours per day" },
  { label: "Contract", icon: "blue", ragQuery: "contract basis project work temporary fixed term freelance assignment" },
  { label: "Internship", icon: "yellow", ragQuery: "internship training program fresher 6 months stipend apprenticeship entry level learning opportunity" },
  { label: "Manufacturing", icon: "purple", ragQuery: "manufacturing production factory assembly line operator cnc machine operator" },
  { label: "Textile", icon: "orange", ragQuery: "textile garments fabric sewing weaving" },
  { label: "Engineering", icon: "blue", ragQuery: "engineering mechanical design civil electrical maintenance" },
  { label: "Logistics", icon: "gold", ragQuery: "logistics warehouse supply chain driver delivery packaging" },
  { label: "IT / Tech", icon: "green", ragQuery: "software it technology developer data networking computer" },
  { label: "Management", icon: "red", ragQuery: "management supervisor manager admin operations hr" },
];
const TRADE_FILTERS = [
  { label: "Raw Material", icon: "red" },
  { label: "Machinery", icon: "blue" },
  { label: "Packaging", icon: "green" },
  { label: "Chemicals", icon: "yellow" },
  { label: "Electronics", icon: "purple" },
  { label: "Food Products", icon: "orange" },
  { label: "Automotive", icon: "gold" },
  { label: "Construction", icon: "blue" },
  { label: "Textiles", icon: "purple" },
  { label: "Metals", icon: "red" },
];
const SHIFT_FILTERS = [
  { label: "Day Shift", icon: "gold", value: "Day" },
  { label: "Night Shift", icon: "purple", value: "Night" },
  { label: "General Shift", icon: "blue", value: "General" },
  { label: "Part Time", icon: "green", value: "Part Time" },
];

// ================================
// ICON URLS
// ================================
const ICON_URLS = {
  blue: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
  red: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  green: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
  gold: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png",
  orange: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png",
  yellow: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png",
  purple: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png",
  shadow: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
};

function makeIcon(color) {
  return L.icon({
    iconUrl: ICON_URLS[color] || ICON_URLS.blue,
    shadowUrl: ICON_URLS.shadow,
    iconSize: [25, 41], iconAnchor: [12, 41],
    popupAnchor: [1, -34], shadowSize: [41, 41],
  });
}

// Pulsing blue dot for user location
function makeUserIcon() {
  return L.divIcon({
    className: "",
    html: `<div style="width:18px;height:18px;border-radius:50%;background:#1a73e8;border:3px solid #fff;box-shadow:0 0 0 3px rgba(26,115,232,0.3);animation:pulse 1.5s infinite;"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

// Small MIDC zone badge marker
function makeMidcZoneIcon(sector) {
  const colors = {
    "Manufacturing": "#185FA5",
    "Engineering": "#0F6E56",
    "IT / Tech": "#534AB7",
    "Chemical": "#993C1D",
  };
  const c = colors[sector] || "#888";
  return L.divIcon({
    className: "",
    html: `<div style="background:${c};color:#fff;font-size:10px;font-weight:600;padding:3px 7px;border-radius:4px;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.25);">${sector}</div>`,
    iconSize: [null, null],
    iconAnchor: [0, 0],
  });
}

// ================================
// POPUP BUILDERS (Google Maps style)
// ================================
function buildJobPopup(job, sourceLabel = "") {
  // sourceLabel: "Local DB" | "Naukri" | "Jobhai" | "External" | "RAG"
  const isLocal = sourceLabel === "Local DB" || job.source === "local";
  const isNaukri = sourceLabel === "Naukri" || job.source === "naukri";
  const isJobhai = sourceLabel === "Jobhai" || job.source === "jobhai";
  const isRAG = sourceLabel === "RAG" || job.source === "rag";

  const SOURCE_STYLES = {
    "Local DB": { bg: "#e8f5e9", color: "#2e7d32", icon: "fa-database", label: "Local DB" },
    "Naukri": { bg: "#fff3e0", color: "#e65100", icon: "fa-n", label: "Naukri" },
    "Jobhai": { bg: "#ede7f6", color: "#4527a0", icon: "fa-briefcase", label: "Jobhai" },
    "Adzuna": { bg: "#e3f2fd", color: "#0277bd", icon: "fa-globe", label: "Adzuna" },
    "External": { bg: "#e3f2fd", color: "#1565c0", icon: "fa-globe", label: "External" },
    "RAG": { bg: "", color: "", icon: "fa-wand-magic-sparkles", label: "AI Match" },
  };
  const style = SOURCE_STYLES[sourceLabel] || SOURCE_STYLES["External"];

  const sal = job.salary && job.salary !== "Not disclosed"
    ? `<span class="gm-chip salary"><i class="fa-solid fa-indian-rupee-sign"></i> ${escapeHtml(job.salary)}</span>`
    : `<span class="gm-chip salary"><i class="fa-solid fa-indian-rupee-sign"></i> Not disclosed</span>`;
  const shiftChip = job.shift
    ? `<span class="gm-chip shift"><i class="fa-solid fa-clock"></i> ${escapeHtml(job.shift)}</span>` : "";
  const typeChip = job.type
    ? `<span class="gm-chip type"><i class="fa-solid fa-briefcase"></i> ${escapeHtml(job.type)}</span>` : "";
  const desc = job.description
    ? `<div class="gm-popup-desc">${escapeHtml(job.description.substring(0, 120))}...</div>` : "";
  const sourceBadge = isRAG 
    ? `<span class="gm-chip source-badge rag" title="Matched by AI context, not just keywords"><i class="fa-solid ${style.icon}"></i> ${style.label}</span>`
    : `<span class="gm-chip osm" style="background:${style.bg};color:${style.color};"><i class="fa-solid ${style.icon}"></i> ${style.label}</span>`;
  const midcBadge = job.city && job.city.toLowerCase().includes("midc")
    ? `<span class="gm-chip" style="background:#e3f2fd;color:#1565c0;"><i class="fa-solid fa-industry"></i> MIDC</span>` : "";
  const viewBtn = !isLocal && job.url
    ? `<a class="gm-btn gm-btn-primary-blue" href="${job.url}" target="_blank"><i class="fa-solid fa-arrow-up-right-from-square"></i> Apply Now</a>`
    : `<a class="gm-btn gm-btn-primary-blue" href="/job/${job.id}"><i class="fa-solid fa-arrow-up-right-from-square"></i> View Job</a>`;

  return `
    <div class="gm-popup-header jobs-header"></div>
    <div class="gm-popup-body">
      <div class="gm-popup-title-row">
        <div class="gm-popup-icon jobs-icon"><i class="fa-solid fa-briefcase"></i></div>
        <div class="gm-popup-text">
          <p class="gm-popup-title" title="${escapeHtml(job.title)}">${escapeHtml(job.title)}</p>
          <p class="gm-popup-subtitle"><i class="fa-solid fa-building"></i> ${escapeHtml(job.company)}</p>
        </div>
      </div>
      <div class="gm-popup-location"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(job.city)}</div>
      <div class="gm-popup-chips">${sal}${typeChip}${shiftChip}${sourceBadge}${midcBadge}</div>
      <div class="gm-popup-divider"></div>
      ${desc}
      <div class="gm-verified"><i class="fa-solid fa-circle-check"></i> IndusTech Verified</div>
    </div>
    <div class="gm-popup-actions">
      <button class="gm-btn gm-btn-directions" onclick="getDirectionsTo(${job.lat},${job.lng})">
        <i class="fa-solid fa-diamond-turn-right"></i> Directions
      </button>
      ${viewBtn}
    </div>`;
}

function buildTradePopup(trade) {
  return `
    <div class="gm-popup-header trades-header"></div>
    <div class="gm-popup-body">
      <div class="gm-popup-title-row">
        <div class="gm-popup-icon trades-icon"><i class="fa-solid fa-box"></i></div>
        <div class="gm-popup-text">
          <p class="gm-popup-title" title="${escapeHtml(trade.name)}">${escapeHtml(trade.name)}</p>
          <p class="gm-popup-subtitle"><i class="fa-solid fa-building"></i> ${escapeHtml(trade.company)}</p>
        </div>
      </div>
      <div class="gm-popup-location"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(trade.city)}</div>
      <div class="gm-popup-chips">
        <span class="gm-chip price"><i class="fa-solid fa-indian-rupee-sign"></i> ${escapeHtml(String(trade.price))}</span>
        <span class="gm-chip qty"><i class="fa-solid fa-cubes"></i> Qty: ${escapeHtml(String(trade.quantity))}</span>
        <span class="gm-chip cat"><i class="fa-solid fa-tag"></i> ${escapeHtml(trade.category)}</span>
      </div>
      <div class="gm-popup-divider"></div>
      <div class="gm-popup-desc">${escapeHtml((trade.description || "").substring(0, 120))}</div>
      <div class="gm-verified"><i class="fa-solid fa-circle-check"></i> IndusTech Verified</div>
    </div>
    <div class="gm-popup-actions">
      <button class="gm-btn gm-btn-directions" onclick="getDirectionsTo(${trade.lat},${trade.lng})">
        <i class="fa-solid fa-diamond-turn-right"></i> Directions
      </button>
      <a class="gm-btn gm-btn-primary-green" href="/trade/${trade.id}">
        <i class="fa-solid fa-arrow-up-right-from-square"></i> View Trade
      </a>
    </div>`;
}

function buildOSMPopup(name, type, el, elLat, elLon) {
  const addrParts = [el.tags?.["addr:street"], el.tags?.["addr:city"]].filter(Boolean);
  const addr = addrParts.length ? `<div class="gm-popup-location"><i class="fa-solid fa-location-dot"></i> ${addrParts.join(", ")}</div>` : "";
  const phone = el.tags?.phone ? `<div class="gm-popup-location"><i class="fa-solid fa-phone"></i> ${el.tags.phone}</div>` : "";
  const web = el.tags?.website ? `<div class="gm-popup-location"><i class="fa-solid fa-globe"></i> <a href="${el.tags.website}" target="_blank" style="color:#1a73e8;text-decoration:none;">Visit Website</a></div>` : "";
  return `
    <div class="gm-popup-header osm-header"></div>
    <div class="gm-popup-body">
      <div class="gm-popup-title-row">
        <div class="gm-popup-icon osm-icon"><i class="fa-solid fa-industry"></i></div>
        <div class="gm-popup-text">
          <p class="gm-popup-title" title="${name}">${name}</p>
          <p class="gm-popup-subtitle"><i class="fa-solid fa-map"></i> OpenStreetMap</p>
        </div>
      </div>
      <div class="gm-popup-chips"><span class="gm-chip osm"><i class="fa-solid fa-industry"></i> ${type}</span></div>
      ${addr}${phone}${web}
    </div>
    <div class="gm-popup-actions">
      <button class="gm-btn gm-btn-directions" style="flex:1" onclick="getDirectionsTo(${elLat},${elLon})">
        <i class="fa-solid fa-diamond-turn-right"></i> Get Directions
      </button>
    </div>`;
}

function buildMidcZonePopup(zone) {
  return `
    <div class="gm-popup-header" style="background:linear-gradient(135deg,#1a237e,#1565c0);height:6px;border-radius:12px 12px 0 0;"></div>
    <div class="gm-popup-body">
      <div class="gm-popup-title-row">
        <div class="gm-popup-icon" style="background:#e3f2fd;color:#1565c0;"><i class="fa-solid fa-industry"></i></div>
        <div class="gm-popup-text">
          <p class="gm-popup-title">${zone.name}</p>
          <p class="gm-popup-subtitle"><i class="fa-solid fa-map-location-dot"></i> Pune District, Maharashtra</p>
        </div>
      </div>
      <div class="gm-popup-chips">
        <span class="gm-chip" style="background:#e3f2fd;color:#1565c0;"><i class="fa-solid fa-gears"></i> ${zone.sector}</span>
        <span class="gm-chip" style="background:#e8f5e9;color:#2e7d32;"><i class="fa-solid fa-location-dot"></i> MIDC Zone</span>
      </div>
      <div class="gm-popup-divider"></div>
      <div class="gm-popup-desc">Click to search jobs in this MIDC zone.</div>
    </div>
    <div class="gm-popup-actions">
      <button class="gm-btn gm-btn-directions" onclick="getDirectionsTo(${zone.lat},${zone.lng})">
        <i class="fa-solid fa-diamond-turn-right"></i> Directions
      </button>
      <button class="gm-btn gm-btn-primary-blue" onclick="searchJobsInZone('${zone.name}')">
        <i class="fa-solid fa-magnifying-glass"></i> Search Jobs
      </button>
      <button class="gm-btn" style="background:linear-gradient(135deg, #1a73e8, #0a438b); color:white; border: 1px solid rgba(255,255,255,0.4);" onclick="askAITellMeAbout('${zone.name}')">
        <i class="fa-solid fa-wand-magic-sparkles"></i> AI Insights
      </button>
    </div>`;
}

function buildUserPopup() {
  return `
    <div class="gm-popup-header user-header"></div>
    <div class="gm-popup-body">
      <div class="gm-popup-title-row">
        <div class="gm-popup-icon user-icon"><i class="fa-solid fa-location-crosshairs"></i></div>
        <div class="gm-popup-text">
          <p class="gm-popup-title">Your Location</p>
          <p class="gm-popup-subtitle"><i class="fa-solid fa-satellite-dish"></i> GPS detected</p>
        </div>
      </div>
      <div class="gm-popup-desc">This is your current location used as the origin for directions and nearby searches.</div>
    </div>`;
}

// ================================
// ZONE SEARCH HELPER
// ================================
function searchJobsInZone(zoneName) {
  map.closePopup();
  const sb = document.getElementById("search-box");
  if (sb) sb.value = zoneName;
  loadDataForMode();
}

// ================================
// TOAST
// ================================
function showToast(msg, duration = 3000) {
  const t = document.getElementById("map-toast");
  if (!t) return;
  t.textContent = msg;
  t.style.display = "block";
  setTimeout(() => { t.style.display = "none"; }, duration);
}

// ================================
// LOADING STATES
// ================================
function showLoading(message = "Searching...") {
  const list = document.getElementById("dynamic-industry-list");
  const cnt = document.getElementById("results-count");
  if (list) {
    list.innerHTML = `
      <div class="loading-state" style="text-align:center;margin-top:50px;">
        <div class="search-spinner"></div>
        <p style="color:#64748b;margin-top:14px;font-size:14px;">${message}</p>
      </div>`;
  }
  if (cnt) cnt.textContent = message;
}

function showNoResults(query) {
  const list = document.getElementById("dynamic-industry-list");
  const cnt = document.getElementById("results-count");
  if (list) {
    list.innerHTML = `
      <div class="empty-state" style="text-align:center;margin-top:40px;padding:0 16px;">
        <i class="fa-solid fa-magnifying-glass" style="font-size:2.5rem;margin-bottom:14px;color:#cbd5e1;"></i>
        <p style="color:#475569;font-weight:600;font-size:15px;margin-bottom:8px;">No results found${query ? ` for "${query}"` : ""}</p>
        <p style="color:#94a3b8;font-size:13px;line-height:1.5;">Try different keywords, change the location, or increase the search radius.</p>
      </div>`;
  }
  if (cnt) cnt.textContent = "0 Results";
}

function updateResultCount() {
  const list = document.getElementById("dynamic-industry-list");
  const cnt = document.getElementById("results-count");
  if (!list || !cnt) return;
  const count = list.querySelectorAll(".industry-card").length;
  cnt.textContent = `${count} Result${count !== 1 ? "s" : ""} found`;
}

// ================================
// UTILITY
// ================================
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ================================
// INIT
// ================================
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("map")) {
    initMap();
    initSidebar();
  }
});

function initMap() {
  // Default center: Pune district
  map = L.map("map", {
    zoomControl: false,
  }).setView([18.6200, 73.8800], 11);

  // Google Maps-style tile layer via CartoDB
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    attribution: '© <a href="https://carto.com/">CARTO</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Zoom control bottom-right (like Google Maps)
  L.control.zoom({ position: "bottomright" }).addTo(map);

  markerCluster = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 40,      // smaller = less aggressive clustering
    disableClusteringAtZoom: 14, // at zoom 14+ show individual markers
    spiderfyOnMaxZoom: true,
  });
  map.addLayer(markerCluster);

  // Draw Pune MIDC zone boundary markers
  drawPuneMidcZones();

  initAutocomplete();
  detectLocation();

  map.on("dragend zoomend", () => {
    if (!locationConfirmed) return;
    clearTimeout(mapMoveTimer);
    // Debounce 800ms — only reloads local DB jobs + re-filters cached Adzuna
    // No new Adzuna API call on map move
    mapMoveTimer = setTimeout(() => {
      applyRadiusFromZoom();
      loadDataForMode();
    }, 800);
  });

  // Add pulsing animation style
  const style = document.createElement("style");
  style.textContent = `
    @keyframes pulse {
      0%   { box-shadow: 0 0 0 0   rgba(26,115,232,0.4); }
      70%  { box-shadow: 0 0 0 10px rgba(26,115,232,0);   }
      100% { box-shadow: 0 0 0 0   rgba(26,115,232,0);    }
    }
    .gm-leaflet-popup .leaflet-popup-content-wrapper {
      border-radius: 12px !important;
      box-shadow: 0 4px 20px rgba(0,0,0,0.18) !important;
      padding: 0 !important;
      overflow: hidden;
    }
    .gm-leaflet-popup .leaflet-popup-content { margin: 0 !important; width: 300px !important; }
    .gm-leaflet-popup .leaflet-popup-tip-container { display: none; }
    .midc-zone-label {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
    }
  `;
  document.head.appendChild(style);
}

// ================================
// PUNE MIDC ZONE OVERLAY
// ================================
function drawPuneMidcZones() {
  PUNE_MIDC_ZONES.forEach(zone => {
    // Subtle circle boundary
    L.circle([zone.lat, zone.lng], {
      radius: 2500,
      color: "#1a73e8",
      weight: 1.5,
      opacity: 0.5,
      fillColor: "#1a73e8",
      fillOpacity: 0.06,
    }).addTo(map);

    // Zone label marker
    const zoneMarker = L.marker([zone.lat, zone.lng], {
      icon: makeMidcZoneIcon(zone.sector),
      zIndexOffset: 500,
    });
    zoneMarker.bindPopup(buildMidcZonePopup(zone), {
      maxWidth: 320,
      className: "gm-leaflet-popup",
    });
    zoneMarker.on("click", function () { this.openPopup(); });
    zoneMarker.addTo(map);
  });
}

// ================================
// RADIUS / ZOOM
// ================================
function getRadiusConfig() {
  // FIX: Pune MIDC zones span 60km across the district.
  // Never shrink below 60km — otherwise Chakan/Ranjangaon
  // disappear when user zooms into Hinjewadi/Wakad area.
  return { radius: 60000 };
}

function applyRadiusFromZoom() {
  const anyActive = document.querySelector(".radius-btns button.active");
  // Only override radius if user has NOT manually selected one
  if (!anyActive) currentSearchRadius = 60000;
}

// ================================
// LOCATION DETECTION
// ================================
function detectLocation() {
  // FIX: Set default location FIRST, then load cache.
  // This prevents race condition where cache loaded with lat=0,lng=0.
  // onLocationSuccess sets userLocation before loadExternalJobsCache reads it.
  onLocationSuccess(18.6200, 73.8800);

  // Now safe to pre-load cache — userLocation is already set
  loadExternalJobsCache();

  if (!navigator.geolocation) { ipGeoFallback(); return; }
  showLoading("📍 Detecting your location...");
  navigator.geolocation.getCurrentPosition(
    pos => onLocationSuccess(pos.coords.latitude, pos.coords.longitude),
    () => ipGeoFallback(),
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
  );
}

function ipGeoFallback() {
  showLoading("📡 Using approximate location...");
  fetch("https://ip-api.com/json/?fields=lat,lon,city")
    .then(r => r.json())
    .then(d => {
      if (d.lat) onLocationSuccess(d.lat, d.lon);
      else onLocationSuccess(18.6200, 73.8800); // Pune MIDC default
    })
    .catch(() => onLocationSuccess(18.6200, 73.8800));
}

function onLocationSuccess(lat, lng) {
  userLocation = { lat, lng };
  searchLocation = null;
  locationConfirmed = false;

  if (currentLocationMarker) currentLocationMarker.remove();
  currentLocationMarker = L.marker([lat, lng], {
    icon: makeUserIcon(),
    zIndexOffset: 1000,
  })
    .bindPopup(buildUserPopup(), { maxWidth: 320, className: "gm-leaflet-popup" })
    .addTo(map);

  map.setView([lat, lng], 13);
  locationConfirmed = true;
  loadDataForMode();
}

function getUserLocation() {
  if (!navigator.geolocation) { showToast("❌ GPS not supported"); return; }
  showToast("📍 Getting your location...");
  navigator.geolocation.getCurrentPosition(
    pos => onLocationSuccess(pos.coords.latitude, pos.coords.longitude),
    () => showToast("❌ Could not get GPS. Enable location permissions."),
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

function getEffectiveLocation() {
  if (searchLocation) return searchLocation;
  if (userLocation) return userLocation;
  const c = map.getCenter();
  return { lat: c.lat, lng: c.lng };
}

// ================================
// EXTERNAL JOBS CACHE (JS side)
// ================================
// External jobs (Adzuna) are fetched ONCE from the backend cache
// and stored here in memory. Map moves/zooms only re-filter this list
// without making new API calls — making the map instant.
let _externalJobsCache = [];
let _externalCacheLoaded = false;
let _externalCacheLoading = false;

async function loadExternalJobsCache() {
  if (_externalCacheLoaded || _externalCacheLoading) return;
  _externalCacheLoading = true;
  try {
    // FIX: Always use Pune centre coords + NO radius filter on cache load.
    // Radius=0 tells backend to skip distance filtering entirely.
    // This ensures ALL 700 cached Pune jobs are loaded, regardless of
    // where the user is on the map. JS-side filtering handles display.
    const data = await fetch(
      `/api/map/external-jobs?lat=18.6200&lng=73.8800&skip_radius=1`
    ).then(r => r.json());
    _externalJobsCache = data;
    _externalCacheLoaded = true;
    console.log(`[Adzuna] ${data.length} jobs loaded into JS cache`);
    // Re-render now that cache is ready
    if (locationConfirmed) loadDataForMode();
  } catch (e) {
    console.error("[Adzuna] Cache load failed:", e);
    _externalCacheLoading = false;
  }
  _externalCacheLoading = false;
}

function getFilteredExternalJobs(keyword, activeShift) {
  let jobs = _externalJobsCache;
  if (keyword) {
    const words = keyword.toLowerCase().split(" ").filter(Boolean);
    jobs = jobs.filter(j => {
      const text = `${j.title} ${j.company} ${j.city} ${j.description}`.toLowerCase();
      return words.every(w => text.includes(w));
    });
  }
  if (activeShift) {
    jobs = jobs.filter(j => !j.shift || j.shift.toLowerCase().includes(activeShift.toLowerCase()));
  }
  return jobs;
}

// ================================
// CORE DATA LOADER
// ================================
function loadDataForMode() {
  clearMarkers();
  seenOSMIds.clear();

  const keyword = document.getElementById("search-box")?.value?.trim() || "";
  const cityName = document.getElementById("location-box")?.value?.trim() || "Pune";

  const activeTagEl = document.querySelector("#filter-tags .tag.active:not(.shift-tag)");
  const activeTag = activeTagEl ? activeTagEl.textContent.trim().replace(/\s+/g, " ") : "";
  const activeShift = document.querySelector(".shift-tag.active")?.dataset.value || "";

  const localQuery = [keyword, activeTag].filter(Boolean).join(" ").trim();
  const loc = getEffectiveLocation();

  const params = `lat=${loc.lat}&lng=${loc.lng}&radius=${currentSearchRadius}&city=${encodeURIComponent(cityName || "Pune")}&q=${encodeURIComponent(localQuery)}`;

  showLoading("🔍 Searching Pune MIDC jobs...");

  if (mapMode === "jobs") {
    fetchAndPlotJobs(params, localQuery, loc, activeShift);
  } else {
    fetchAndPlotTrades(params, localQuery, loc);
    fetchOSMIndustries(loc);
  }
}

// ================================
// JOBS — Internal DB + Naukri/Jobhai scraper cache
// ================================
async function fetchAndPlotJobs(params, query, loc, activeShift = "") {
  let localCount = 0;
  let externalCount = 0;

  // 1. Fetch local DB jobs first
  try {
    const localData = await fetch(`/api/map/jobs?${params}`).then(r => r.json());
    let filtered = localData;
    if (activeShift) {
      filtered = filtered.filter(j => j.shift && j.shift.toLowerCase().includes(activeShift.toLowerCase()));
    }
    filtered.forEach(job => {
      if (job.lat == null || job.lng == null) return;
      const popup = buildJobPopup(job, "Local DB");
      addClusteredMarker([job.lat, job.lng], popup, "red");
      addSidebarCard(job.title, job.company, job.city, "fa-briefcase", "bg-red", [job.lat, job.lng], true, "Local DB");
      localCount++;
    });
    if (localCount > 0) updateResultCount();
  } catch (e) {
    console.error("Local jobs fetch error:", e);
  }

  // 2. External jobs — served from JS memory cache (no API call on map move)
  // Cache is loaded once on page load via loadExternalJobsCache()
  if (!_externalCacheLoaded) {
    // Cache not ready yet — load it now and re-render when done
    loadExternalJobsCache().then(() => loadDataForMode());
    if (localCount === 0) showLoading("⏳ Loading Adzuna jobs...");
    return;
  }

  try {
    const keyword = document.getElementById("search-box")?.value?.trim() || "";
    // Pass the combined query (from search box + active filter) to external jobs
    const extFiltered = getFilteredExternalJobs(query, activeShift);

    extFiltered.forEach(job => {
      if (job.lat == null || job.lng == null) return;
      const popup = buildJobPopup(job, "Adzuna");
      addClusteredMarker([job.lat, job.lng], popup, "gold");
      addSidebarCard(job.title, job.company, job.city, "fa-globe", "bg-gold", [job.lat, job.lng], false, "Adzuna");
      externalCount++;
    });

    // 3. RAG AI Semantic Matches
    let ragCount = 0;
    const activeRagEl = document.querySelector("#filter-tags .tag.active:not(.shift-tag)");
    let ragQuery = activeRagEl && activeRagEl.dataset.rag ? activeRagEl.dataset.rag : "";
    if (!ragQuery && keyword.length > 3) ragQuery = keyword; // fallback to text query

    if (ragQuery) {
      try {
        const ragParams = `q=${encodeURIComponent(ragQuery)}&lat=${loc.lat}&lng=${loc.lng}&radius=${currentSearchRadius}`;
        const ragData = await fetch(`/api/rag-filter?${ragParams}`).then(r => r.json());
        ragData.forEach(job => {
          if (job.lat == null || job.lng == null) return;
          const popup = buildJobPopup(job, "RAG");
          addClusteredMarker([job.lat, job.lng], popup, "purple");
          addSidebarCard(job.title, job.company, job.city, "fa-wand-magic-sparkles", "bg-rag", [job.lat, job.lng], true, "RAG");
          ragCount++;
        });
      } catch (e) {
        console.error("RAG jobs fetch error:", e);
      }
    }

    const total = localCount + externalCount + ragCount;
    if (total === 0) {
      showNoResults(query || "jobs near you");
    } else {
      updateResultCount();
      let msg = `✅ ${total} jobs — ${localCount} local · ${externalCount} Adzuna`;
      if (ragCount > 0) msg += ` · ${ragCount} AI Matches`;
      showToast(msg);
    }
  } catch (e) {
    console.error("External/RAG jobs fetch error:", e);
    if (localCount === 0) showNoResults(query || "jobs near you");
    else updateResultCount();
  }
}

// ================================
// TRADES
// ================================
async function fetchAndPlotTrades(params, query, loc) {
  try {
    const data = await fetch(`/api/map/trades?${params}`).then(r => r.json());

    const filtered = query ? data.filter(t => {
      const text = [t.name, t.company, t.category, t.city, t.description].join(" ").toLowerCase();
      const words = query.toLowerCase().split(/\s+/);
      return words.every(word => text.includes(word));
    }) : data;

    let hasResults = false;
    filtered.forEach(trade => {
      if (trade.lat == null || trade.lng == null) return;
      hasResults = true;
      const popup = buildTradePopup(trade);
      addClusteredMarker([trade.lat, trade.lng], popup, "green");
      addSidebarCard(trade.name, trade.company, trade.city, "fa-box", "bg-green", [trade.lat, trade.lng], true);
    });

    if (hasResults) updateResultCount();
    else showNoResults(query);

  } catch (e) {
    console.error("Trades fetch error:", e);
    showNoResults(query);
  }
}

// ================================
// OSM INDUSTRIES
// ================================
function fetchOSMIndustries(loc) {
  const radius = currentSearchRadius;
  const q = `[out:json][timeout:25];(node["landuse"="industrial"](around:${radius},${loc.lat},${loc.lng});way["landuse"="industrial"](around:${radius},${loc.lat},${loc.lng});node["industrial"="factory"](around:${radius},${loc.lat},${loc.lng});node["man_made"="works"](around:${radius},${loc.lat},${loc.lng}););out center;`;

  fetch("https://overpass-api.de/api/interpreter", { method: "POST", body: q })
    .then(r => r.json())
    .then(data => {
      if (!data.elements) return;
      data.elements.forEach(el => {
        if (seenOSMIds.has(el.id)) return;
        seenOSMIds.add(el.id);

        const elLat = el.lat || el.center?.lat;
        const elLon = el.lon || el.center?.lon;
        if (!elLat || !elLon) return;

        const name = el.tags?.name || el.tags?.operator || el.tags?.brand || "Industrial Facility";
        let type = el.tags?.industrial || el.tags?.landuse || "Industry";
        type = type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, " ");

        const popup = buildOSMPopup(name, type, el, elLat, elLon);
        addClusteredMarker([elLat, elLon], popup, "gold");
        addSidebarCard(name, type, "OSM Data", "fa-industry", "bg-blue", [elLat, elLon], false);
      });
      updateResultCount();
    })
    .catch(e => console.error("Overpass error:", e));
}

// ================================
// MARKERS
// ================================
function addClusteredMarker(latlng, popupHtml, color) {
  const marker = L.marker(latlng, { icon: makeIcon(color) });
  marker.bindPopup(popupHtml, {
    maxWidth: 320,
    autoPan: true,
    autoPanPadding: [20, 20],
    closeButton: true,
    autoClose: true,
    closeOnClick: false,
    className: "gm-leaflet-popup",
  });
  marker.on("click", function () { this.openPopup(); });
  markerCluster.addLayer(marker);
  return marker;
}

function clearMarkers() {
  if (markerCluster) markerCluster.clearLayers();
  const list = document.getElementById("dynamic-industry-list");
  if (list) list.innerHTML = "";
  const cnt = document.getElementById("results-count");
  if (cnt) cnt.textContent = "0 Results";
}

// ================================
// SIDEBAR CARDS
// ================================
function addSidebarCard(title, subtitle, location, iconClass, bgColor, latlng, verified, source) {
  const list = document.getElementById("dynamic-industry-list");
  if (!list) return;
  list.querySelector(".empty-state")?.remove();
  list.querySelector(".loading-state")?.remove();

  // Source badge with styled pill
  const SOURCE_BADGES = {
    "Local DB": { cls: "local", label: "Local" },
    "Adzuna": { cls: "adzuna", label: "Adzuna" },
    "Naukri": { cls: "naukri", label: "Naukri" },
    "Jobhai": { cls: "jobhai", label: "Jobhai" },
    "jooble": { cls: "adzuna", label: "Jooble" },
    "local": { cls: "local", label: "Local" },
    "RAG": { cls: "rag", label: "AI Match" },
  };
  const badgeInfo = SOURCE_BADGES[source];
  const sourceBadge = badgeInfo
    ? `<span class="source-badge ${badgeInfo.cls}">${badgeInfo.label}</span>`
    : "";

  // Determine data-source for accent bar
  const dataSource = source === "Local DB" || source === "local" ? "local"
    : source === "Adzuna" || source === "jooble" ? "adzuna"
    : source === "RAG" ? "rag"
    : iconClass === "fa-box" ? "trade"
    : iconClass === "fa-industry" ? "osm" : "";

  const card = document.createElement("div");
  card.className = "industry-card";
  if (dataSource) card.dataset.source = dataSource;
  card.innerHTML = `
    <div class="industry-icon ${bgColor}"><i class="fa-solid ${iconClass}"></i></div>
    <div class="industry-info">
      <h4>${title}${sourceBadge}</h4>
      <p class="category">${subtitle}</p>
      <p class="location"><i class="fa-solid fa-location-dot"></i> ${location}</p>
      ${verified ? '<span class="verified"><i class="fa-solid fa-circle-check"></i> Verified</span>' : ""}
    </div>`;
  card.addEventListener("click", () => { map.setView(latlng, 15); });
  list.appendChild(card);
}

// ================================
// SEARCH
// ================================
const JOB_KEYWORDS = ["job", "jobs", "hiring", "work", "vacancy", "vacancies", "opening", "openings", "career", "careers", "employment"];
const TRADE_KEYWORDS = ["trade", "trades", "buy", "sell", "material", "materials", "product", "products", "goods", "supply", "supplies"];

function runSearch() {
  const query = document.getElementById("search-box")?.value?.trim() || "";
  const lower = query.toLowerCase();

  const foundJob = JOB_KEYWORDS.some(w => lower.includes(w));
  const foundTrade = TRADE_KEYWORDS.some(w => lower.includes(w));

  if (foundJob && mapMode !== "jobs") {
    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("mode-jobs")?.classList.add("active");
    mapMode = "jobs";
    renderFilterTags();
  } else if (foundTrade && !foundJob && mapMode !== "trades") {
    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("mode-trades")?.classList.add("active");
    mapMode = "trades";
    renderFilterTags();
  }

  loadDataForMode();
}

function runLocationSearch(city) {
  if (!city.trim()) { loadDataForMode(); return; }

  const lower = city.toLowerCase();
  if (lower.includes("near me")) { getUserLocation(); return; }

  showLoading(`📍 Finding "${city}"...`);

  fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city + " Pune Maharashtra")}&format=json&limit=1&countrycodes=in`)
    .then(r => r.json())
    .then(data => {
      if (data && data.length > 0) {
        const place = data[0];
        const lat = parseFloat(place.lat);
        const lng = parseFloat(place.lon);
        searchLocation = { lat, lng };
        locationConfirmed = true;
        map.setView([lat, lng], 13);
        showToast(`📍 Showing ${mapMode === "jobs" ? "jobs" : "trades"} near ${city}`);
        loadDataForMode();
      } else {
        showToast(`❌ Could not find location: ${city}`);
        showNoResults(city);
      }
    })
    .catch(() => {
      showToast("❌ Error finding location.");
      showNoResults(city);
    });
}

function initAutocomplete() {
  const searchInput = document.getElementById("search-box");
  if (searchInput) {
    searchInput.addEventListener("keydown", e => {
      if (e.key === "Enter") { e.preventDefault(); runSearch(); }
    });
    searchInput.addEventListener("input", () => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        if (locationConfirmed) runSearch();
      }, 600);
    });
  }

  const input = document.getElementById("location-box");
  if (!input) return;

  const wrapper = input.parentNode;
  wrapper.style.position = "relative";
  const dropdown = document.createElement("div");
  dropdown.className = "autocomplete-dropdown";
  dropdown.style.cssText = "position:absolute;background:white;width:100%;max-height:200px;overflow-y:auto;z-index:9999;box-shadow:0 4px 6px rgba(0,0,0,0.1);border-radius:4px;display:none;top:100%;left:0;";
  wrapper.appendChild(dropdown);

  let timeout;
  input.addEventListener("input", e => {
    clearTimeout(timeout);
    const val = e.target.value.trim();
    if (val.length < 3) { dropdown.style.display = "none"; return; }
    timeout = setTimeout(() => {
      // Bias autocomplete to Pune district
      fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(val + " Pune")}&format=json&limit=5&countrycodes=in`)
        .then(r => r.json())
        .then(data => {
          dropdown.innerHTML = "";
          if (data.length > 0) {
            dropdown.style.display = "block";
            data.forEach(place => {
              const item = document.createElement("div");
              item.style.cssText = "padding:10px;cursor:pointer;border-bottom:1px solid #eee;font-size:13px;color:#333;";
              item.textContent = place.display_name;
              item.addEventListener("mouseenter", () => item.style.background = "#f0f0f0");
              item.addEventListener("mouseleave", () => item.style.background = "white");
              item.addEventListener("mousedown", () => {
                input.value = place.display_name.split(",")[0];
                dropdown.style.display = "none";
                runLocationSearch(input.value);
              });
              dropdown.appendChild(item);
            });
          } else { dropdown.style.display = "none"; }
        });
    }, 400);
  });

  document.addEventListener("click", e => { if (!wrapper.contains(e.target)) dropdown.style.display = "none"; });
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); dropdown.style.display = "none"; runLocationSearch(input.value.trim()); }
  });
}

// ================================
// DIRECTIONS (OSRM)
// ================================
let routeBanner = null;

function showRouteBanner(distanceKm, durationMin) {
  if (routeBanner) routeBanner.remove();
  const mapView = document.querySelector(".map-view");
  if (!mapView) return;

  const dist = distanceKm < 1
    ? `${Math.round(distanceKm * 1000)} m`
    : `${distanceKm.toFixed(1)} km`;
  const mins = Math.round(durationMin);
  const time = mins < 60 ? `${mins} min` : `${Math.floor(mins / 60)}h ${mins % 60}m`;

  routeBanner = document.createElement("div");
  routeBanner.className = "route-active-banner";
  routeBanner.innerHTML = `
    <i class="fa-solid fa-diamond-turn-right"></i>
    <span><strong>${dist}</strong> · ${time} by road</span>
    <button class="close-route" title="Clear route" onclick="clearRoute()"><i class="fa-solid fa-xmark"></i></button>`;
  mapView.appendChild(routeBanner);
}

function clearRoute() {
  if (currentRouteLayer) { map.removeLayer(currentRouteLayer); currentRouteLayer = null; }
  if (routeBanner) { routeBanner.remove(); routeBanner = null; }
}

function getDirectionsTo(destLat, destLng) {
  const origin = getEffectiveLocation();
  showToast("🗺️ Calculating route...");
  fetch(`https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destLng},${destLat}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(data => {
      if (data.routes && data.routes.length > 0) {
        if (currentRouteLayer) map.removeLayer(currentRouteLayer);
        currentRouteLayer = L.geoJSON(data.routes[0].geometry, {
          style: { color: "#1a73e8", weight: 5, opacity: 0.85, lineCap: "round", lineJoin: "round" },
        }).addTo(map);
        map.fitBounds(currentRouteLayer.getBounds(), { padding: [50, 50] });
        const dist = data.routes[0].distance / 1000;
        const dur = data.routes[0].duration / 60;
        showRouteBanner(dist, dur);
        map.closePopup();
      } else { showToast("❌ No route found to this location."); }
    })
    .catch(() => showToast("❌ Error fetching directions."));
}

// ================================
// SIDEBAR CONTROLS
// ================================
function initSidebar() {
  document.querySelectorAll(".mode-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
      this.classList.add("active");
      mapMode = this.dataset.mode;
      renderFilterTags();
      const sb = document.getElementById("search-box");
      if (sb) sb.value = "";
      loadDataForMode();
    });
  });

  const radiusBtns = document.querySelectorAll(".radius-btns button");
  radiusBtns.forEach(btn => {
    btn.addEventListener("click", function () {
      radiusBtns.forEach(b => b.classList.remove("active"));
      this.classList.add("active");
      const t = this.textContent.trim();
      if (t === "5 km") currentSearchRadius = 5000;
      else if (t === "10 km") currentSearchRadius = 10000;
      else if (t === "20 km") currentSearchRadius = 20000;
      else if (t === "50 km") currentSearchRadius = 50000;
      else currentSearchRadius = 1000;
      loadDataForMode();
    });
  });

  document.querySelector(".clear-filters")?.addEventListener("click", e => {
    e.preventDefault();
    document.querySelectorAll(".tag").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".radius-btns button").forEach((b, i) => {
      b.classList.remove("active");
      if (i === 1) b.classList.add("active");
    });
    currentSearchRadius = 10000;
    const lb = document.getElementById("location-box");
    if (lb) lb.value = "";
    searchLocation = null;
    const sb = document.getElementById("search-box");
    if (sb) sb.value = "";
    loadDataForMode();
  });

  document.querySelector(".gps-btn")?.addEventListener("click", getUserLocation);

  renderFilterTags();
}

function renderFilterTags() {
  const container = document.getElementById("filter-tags");
  const label = document.getElementById("filter-label");
  const shiftSection = document.getElementById("shift-filter-section");
  const shiftContainer = document.getElementById("shift-filter-tags");

  if (!container) return;

  const filters = mapMode === "jobs" ? JOB_FILTERS : TRADE_FILTERS;
  if (label) label.textContent = mapMode === "jobs" ? "Job Type" : "Trade Category";

  container.innerHTML = "";
  filters.forEach(f => {
    const tag = document.createElement("span");
    tag.className = "tag";
    if (f.ragQuery) tag.dataset.rag = f.ragQuery;
    tag.innerHTML = `<i class="fa-solid fa-circle ${f.icon}"></i> ${f.label}`;
    tag.addEventListener("click", function () {
      if (this.classList.contains("active")) {
        this.classList.remove("active");
      } else {
        document.querySelectorAll("#filter-tags .tag").forEach(t => t.classList.remove("active"));
        this.classList.add("active");
      }
      loadDataForMode();
    });
    container.appendChild(tag);
  });

  if (shiftSection && shiftContainer) {
    if (mapMode === "jobs") {
      shiftSection.style.display = "block";
      shiftContainer.innerHTML = "";
      SHIFT_FILTERS.forEach(f => {
        const tag = document.createElement("span");
        tag.className = "tag shift-tag";
        tag.dataset.value = f.value;
        tag.innerHTML = `<i class="fa-solid fa-circle ${f.icon}"></i> ${f.label}`;
        tag.addEventListener("click", function () {
          if (this.classList.contains("active")) {
            this.classList.remove("active");
          } else {
            document.querySelectorAll(".shift-tag").forEach(t => t.classList.remove("active"));
            this.classList.add("active");
          }
          loadDataForMode();
        });
        shiftContainer.appendChild(tag);
      });
    } else {
      shiftSection.style.display = "none";
    }
  }
}

// ================================
// AI CHAT WIDGET (ReAct Agent Integration)
// ================================
let chatWidgetInitialized = false;

function initAIChatWidget() {
  if (chatWidgetInitialized) return;
  chatWidgetInitialized = true;
  
  const chatBtn = document.getElementById("ai-chat-btn");
  const chatPanel = document.getElementById("ai-chat-panel");
  const closeChat = document.getElementById("close-chat");
  const sendChat = document.getElementById("send-chat");
  const chatInput = document.getElementById("chat-input");
  const chatBody = document.getElementById("chat-body");
  
  if (!chatBtn || !chatPanel) return;
  
  // Toggle panel
  chatBtn.addEventListener("click", () => {
    chatPanel.classList.add("open");
    chatInput.focus();
  });
  
  closeChat.addEventListener("click", () => {
    chatPanel.classList.remove("open");
  });
  
  // Send message
  async function sendMessage(presetMsg = null) {
    const msg = presetMsg || chatInput.value.trim();
    if (!msg) return;
    
    // Add user message to UI
    addChatMessage(msg, "user");
    if (!presetMsg) chatInput.value = "";
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      const data = await response.json();
      
      removeTypingIndicator(typingId);
      if (data.response) {
        addChatMessage(data.response, "bot");
      } else {
        addChatMessage("Sorry, I encountered an error. Please try again.", "bot");
      }
    } catch (e) {
      console.error("AI Chat error:", e);
      removeTypingIndicator(typingId);
      addChatMessage("Failed to connect to the AI agent.", "bot");
    }
  }
  
  sendChat.addEventListener("click", () => sendMessage());
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
  
  // Expose function for zone popups to use
  window.askAITellMeAbout = (zoneName) => {
    chatPanel.classList.add("open");
    sendMessage(`Tell me about ${zoneName} MIDC.`);
  };
}

function addChatMessage(text, sender) {
  const chatBody = document.getElementById("chat-body");
  if (!chatBody) return;
  
  const msgDiv = document.createElement("div");
  msgDiv.className = `chat-message ${sender}`;
  // Convert basic markdown (like **bold**) to HTML
  const formattedText = escapeHtml(text).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  msgDiv.innerHTML = formattedText;
  
  chatBody.appendChild(msgDiv);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function showTypingIndicator() {
  const chatBody = document.getElementById("chat-body");
  const id = "typing-" + Date.now();
  const indicator = document.createElement("div");
  indicator.id = id;
  indicator.className = "typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  chatBody.appendChild(indicator);
  chatBody.scrollTop = chatBody.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Initialize chat widget on load
document.addEventListener("DOMContentLoaded", () => {
  initAIChatWidget();
});