/**
 * IndusTech Industrial Ecosystem - OpenStreetMap + Leaflet Map & Vis.js Knowledge Graph
 * Free, open-source interactive industrial map and force-directed Knowledge Graph.
 */

let map;
let markers = [];
let userLocationMarker = null;
let activeCategory = null;
let currentRadiusKm = 10;
let userCoords = null;

// Vis.js Knowledge Graph Variables
let visNetwork = null;
let graphNodes = null;
let graphEdges = null;
let currentViewMode = "map"; // "map" or "graph"

// Multi-City Industrial Dataset across Pune, Mumbai, Delhi/Noida, Bangalore, Gujarat, Hyderabad, Chennai
const ALL_INDUSTRIES = [
    // --- PUNE HUB ---
    {
        id: 1,
        name: "ABC Manufacturing Pvt Ltd",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-industry",
        lat: 18.627,
        lng: 73.812,
        address: "Bhosari MIDC, Pune, Maharashtra",
        rating: 4.5,
        verified: true,
        phone: "+91 98230 12345",
        products: "CNC Machining, Precision Sheet Metal"
    },
    {
        id: 2,
        name: "XYZ Textiles & Fabrics",
        category: "Textile",
        color: "#22c55e",
        iconClass: "fa-scissors",
        lat: 18.508,
        lng: 73.926,
        address: "Hadapsar Industrial Zone, Pune, Maharashtra",
        rating: 4.2,
        verified: true,
        phone: "+91 98220 54321",
        products: "Industrial Yarns, Technical Canvas"
    },
    {
        id: 3,
        name: "BioPharma Synth Labs",
        category: "Pharmaceuticals",
        color: "#3b82f6",
        iconClass: "fa-vial",
        lat: 18.675,
        lng: 73.882,
        address: "Chakan Industrial Zone, Pune, Maharashtra",
        rating: 4.7,
        verified: true,
        phone: "+91 98110 88990",
        products: "APIs, Fine Intermediates, Bulk Drugs"
    },
    {
        id: 4,
        name: "PolyChem Polymers India",
        category: "Chemical",
        color: "#a855f7",
        iconClass: "fa-flask",
        lat: 18.562,
        lng: 73.781,
        address: "Pimpri MIDC, Pune, Maharashtra",
        rating: 4.6,
        verified: true,
        phone: "+91 98765 43210",
        products: "Industrial Resins, Polymer Adhesives"
    },

    // --- MUMBAI & THANE HUB ---
    {
        id: 5,
        name: "Reliance Heavy Engineering Complex",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-industry",
        lat: 19.1983,
        lng: 72.9634,
        address: "Thane Industrial Belapur Corridor, Mumbai",
        rating: 4.9,
        verified: true,
        phone: "+91 98200 11122",
        products: "Heavy Pressure Vessels, Turbines"
    },
    {
        id: 6,
        name: "Godrej Process Equipment Division",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-gears",
        lat: 19.0850,
        lng: 72.9300,
        address: "Vikhroli Industrial Complex, Mumbai",
        rating: 4.8,
        verified: true,
        phone: "+91 98201 33445",
        products: "Heat Exchangers, Reactor Vessels"
    },

    // --- DELHI & NOIDA HUB ---
    {
        id: 7,
        name: "Noida Electronics & Hardware City",
        category: "Construction",
        color: "#f59e0b",
        iconClass: "fa-microchip",
        lat: 28.5355,
        lng: 77.3910,
        address: "Sector 63 Industrial Area, Noida, UP",
        rating: 4.6,
        verified: true,
        phone: "+91 98100 55667",
        products: "PCB Assembly, Structural Enclosures"
    },
    {
        id: 8,
        name: "Gurugram Auto Ancillaries Works",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-car",
        lat: 28.4595,
        lng: 77.0266,
        address: "Manesar Industrial Belt, Gurugram, Haryana",
        rating: 4.7,
        verified: true,
        phone: "+91 98180 77889",
        products: "Automotive Forgings, Axles, Gears"
    },

    // --- BANGALORE (BENGALURU) HUB ---
    {
        id: 9,
        name: "Peenya Precision Tools & Dies",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-wrench",
        lat: 13.0285,
        lng: 77.5197,
        address: "Peenya Industrial Estate, Bengaluru, Karnataka",
        rating: 4.7,
        verified: true,
        phone: "+91 98450 12345",
        products: "Aerospace Machining, Injection Moulds"
    },
    {
        id: 10,
        name: "Karnataka Pharma Biotech Hub",
        category: "Pharmaceuticals",
        color: "#3b82f6",
        iconClass: "fa-capsules",
        lat: 12.8398,
        lng: 77.6770,
        address: "Electronic City Phase 2, Bengaluru, Karnataka",
        rating: 4.8,
        verified: true,
        phone: "+91 98451 99887",
        products: "Vaccine Formulations, Clinical Reagents"
    },

    // --- AHMEDABAD & SURAT (GUJARAT) ---
    {
        id: 11,
        name: "GIDC Vatva Chemical Consortium",
        category: "Chemical",
        color: "#a855f7",
        iconClass: "fa-flask",
        lat: 22.9567,
        lng: 72.6321,
        address: "Vatva GIDC Phase IV, Ahmedabad, Gujarat",
        rating: 4.5,
        verified: true,
        phone: "+91 98980 44332",
        products: "Dyes, Organic Intermediates, Solvents"
    },
    {
        id: 12,
        name: "Surat Premium Weaving Mills",
        category: "Textile",
        color: "#22c55e",
        iconClass: "fa-scissors",
        lat: 21.1702,
        lng: 72.8311,
        address: "Pandesara Industrial Estate, Surat, Gujarat",
        rating: 4.6,
        verified: true,
        phone: "+91 98981 66778",
        products: "Synthetic Fibers, Technical Textiles"
    },

    // --- HYDERABAD HUB ---
    {
        id: 13,
        name: "Genome Valley BioSciences",
        category: "Pharmaceuticals",
        color: "#3b82f6",
        iconClass: "fa-vial",
        lat: 17.6521,
        lng: 78.6189,
        address: "Shamirpet BioTech Corridor, Hyderabad, Telangana",
        rating: 4.9,
        verified: true,
        phone: "+91 98490 22334",
        products: "Oncology Formulations, Biosimilars"
    },

    // --- CHENNAI HUB ---
    {
        id: 14,
        name: "Chennai Auto & Heavy Machining Park",
        category: "Manufacturing",
        color: "#ef4444",
        iconClass: "fa-gears",
        lat: 12.9719,
        lng: 79.9430,
        address: "Sriperumbudur Industrial Corridor, Chennai, Tamil Nadu",
        rating: 4.8,
        verified: true,
        phone: "+91 98400 55443",
        products: "Engine Castings, Hydraulic Pumps"
    }
];

// Helper: Calculate Haversine distance in KM
function getDistanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Initialize Map & Graph on DOM Ready
document.addEventListener("DOMContentLoaded", function () {
    initMap();
    initUIControls();
    initKnowledgeGraph();
});

function initMap() {
    const defaultCenter = [18.5204, 73.8567]; // Pune fallback

    map = L.map("map", {
        center: defaultCenter,
        zoom: 11,
        zoomControl: true
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | IndusTech'
    }).addTo(map);

    renderIndustries(ALL_INDUSTRIES);

    if (typeof HOME_SEARCH_QUERY !== "undefined" && HOME_SEARCH_QUERY.trim() !== "") {
        const searchInput = document.getElementById("search-box");
        if (searchInput) searchInput.value = HOME_SEARCH_QUERY;
        searchLocation(HOME_SEARCH_QUERY);
    }
}

// ===================================
// KNOWLEDGE GRAPH (VIS.JS INTEGRATION)
// ===================================
function initKnowledgeGraph() {
    fetch("/api/v1/graph/full")
        .then(res => res.json())
        .then(data => {
            renderKnowledgeGraph(data);
        })
        .catch(err => {
            console.error("Knowledge Graph fetch error:", err);
        });
}

function renderKnowledgeGraph(graphData) {
    const container = document.getElementById("kg-canvas");
    if (!container || !window.vis) return;

    const groupColors = {
        "Company": { background: "#ef4444", border: "#b91c1c" },
        "Sector": { background: "#0d3b8e", border: "#1e3a8a" },
        "Product": { background: "#3b82f6", border: "#1d4ed8" },
        "Location": { background: "#64748b", border: "#334155" },
        "Skill": { background: "#22c55e", border: "#15803d" }
    };

    const formattedNodes = (graphData.nodes || []).map(n => ({
        id: n.id,
        label: n.label,
        shape: "dot",
        size: n.type === "Company" ? 22 : (n.type === "Sector" ? 28 : (n.type === "Location" ? 24 : 16)),
        color: groupColors[n.type] || { background: "#94a3b8", border: "#64748b" },
        font: { color: "#f8fafc", size: 12, face: "Inter, sans-serif" },
        type: n.type
    }));

    const formattedEdges = (graphData.edges || []).map(e => ({
        from: e.from,
        to: e.to,
        label: e.label,
        color: { color: "#334155", highlight: "#38bdf8" },
        arrows: { to: { enabled: true, scaleFactor: 0.6 } },
        font: { color: "#94a3b8", size: 10, align: "middle" }
    }));

    graphNodes = new vis.DataSet(formattedNodes);
    graphEdges = new vis.DataSet(formattedEdges);

    const options = {
        nodes: {
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 1.5,
            smooth: { type: "continuous" }
        },
        physics: {
            barnesHut: {
                gravitationalConstant: -2500,
                centralGravity: 0.3,
                springLength: 90
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 150
        }
    };

    visNetwork = new vis.Network(container, { nodes: graphNodes, edges: graphEdges }, options);

    // Node click handler
    visNetwork.on("click", function (params) {
        if (params.nodes.length > 0) {
            const selectedNodeId = params.nodes[0];
            const nodeObj = formattedNodes.find(n => n.id === selectedNodeId);
            if (nodeObj && nodeObj.type === "Company") {
                const compNumId = parseInt(selectedNodeId.replace("comp_", ""));
                const targetComp = ALL_INDUSTRIES.find(c => c.id === compNumId);
                if (targetComp) {
                    // Fly map to company when clicked in Knowledge Graph
                    map.flyTo([targetComp.lat, targetComp.lng], 14);
                }
            }
        }
    });
}

// Perform Knowledge Graph Search
function searchKnowledgeGraph(queryText) {
    if (!queryText || queryText.trim() === "") {
        initKnowledgeGraph();
        return;
    }

    fetch(`/api/v1/graph/search?q=${encodeURIComponent(queryText)}`)
        .then(res => res.json())
        .then(data => {
            renderKnowledgeGraph(data);
        })
        .catch(err => {
            console.error("Knowledge Graph search error:", err);
        });
}

// Create Custom Colored Leaflet Marker Icon
function createCustomIcon(color, iconClass) {
    return L.divIcon({
        className: "custom-leaflet-marker",
        html: `
            <div style="
                background-color: ${color};
                width: 38px;
                height: 38px;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.35);
                border: 2px solid #ffffff;
            ">
                <i class="fa-solid ${iconClass}" style="
                    transform: rotate(45deg);
                    color: white;
                    font-size: 16px;
                "></i>
            </div>
        `,
        iconSize: [38, 38],
        iconAnchor: [19, 38],
        popupAnchor: [0, -34]
    });
}

// Render Markers on Map & Sidebar Cards
function renderIndustries(items) {
    markers.forEach(m => map.removeLayer(m.leafletMarker));
    markers = [];

    const industryListEl = document.querySelector(".industry-list");
    const countEl = document.querySelector(".results-header span");

    let filteredItems = items;

    if (activeCategory) {
        filteredItems = filteredItems.filter(item => item.category.toLowerCase() === activeCategory.toLowerCase());
    }

    if (countEl) {
        countEl.innerHTML = `<strong>${filteredItems.length} Industries Found</strong>`;
    }

    if (industryListEl) {
        industryListEl.innerHTML = "";
    }

    if (filteredItems.length === 0) {
        if (industryListEl) {
            industryListEl.innerHTML = `
                <div style="padding: 24px; text-align: center; color: #64748b;">
                    <i class="fa-solid fa-map-location-dot" style="font-size: 2.2rem; margin-bottom: 12px; color: #94a3b8;"></i>
                    <p style="font-weight: 600; color: #334155;">No industries match your search.</p>
                    <small style="color: #64748b;">Try searching another city or category tag.</small>
                </div>
            `;
        }
        return;
    }

    filteredItems.forEach(item => {
        const icon = createCustomIcon(item.color, item.iconClass || "fa-industry");
        const leafletMarker = L.marker([item.lat, item.lng], { icon: icon }).addTo(map);

        const popupContent = `
            <div style="font-family: 'Inter', sans-serif; min-width: 230px; padding: 4px;">
                <h4 style="margin: 0 0 6px 0; font-size: 1rem; color: #0f172a; font-weight: 700;">${item.name}</h4>
                <div style="margin-bottom: 8px;">
                    <span style="background: ${item.color}22; color: ${item.color}; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; display: inline-block;">
                        ${item.category}
                    </span>
                    ${item.verified ? '<span style="color: #0284c7; font-size: 0.75rem; margin-left: 6px;"><i class="fa-solid fa-circle-check"></i> Verified</span>' : ''}
                </div>
                <p style="margin: 4px 0; font-size: 0.85rem; color: #475569;">
                    <i class="fa-solid fa-location-dot" style="color: #ef4444;"></i> ${item.address}
                </p>
                <p style="margin: 4px 0; font-size: 0.85rem; color: #475569;">
                    <i class="fa-solid fa-box" style="color: #3b82f6;"></i> ${item.products || 'Industrial Goods'}
                </p>
                <p style="margin: 4px 0; font-size: 0.85rem; color: #f59e0b;">
                    <i class="fa-solid fa-star"></i> ${item.rating} / 5.0
                </p>
                <div style="margin-top: 10px; display: flex; gap: 8px;">
                    <a href="tel:${item.phone}" style="flex: 1; text-align: center; background: #0d3b8e; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 0.8rem; font-weight: 600;">
                        <i class="fa-solid fa-phone"></i> Contact
                    </a>
                </div>
            </div>
        `;

        leafletMarker.bindPopup(popupContent);

        markers.push({
            id: item.id,
            leafletMarker: leafletMarker,
            data: item
        });

        if (industryListEl) {
            const card = document.createElement("div");
            card.className = "industry-card";
            card.dataset.id = item.id;
            card.innerHTML = `
                <div class="industry-icon" style="background-color: ${item.color}; color: white;">
                    <i class="fa-solid ${item.iconClass || 'fa-industry'}"></i>
                </div>
                <div class="industry-info">
                    <h4>${item.name}</h4>
                    <p class="category">${item.category}</p>
                    <p class="location">
                        <i class="fa-solid fa-location-dot"></i> ${item.address}
                        <span class="rating"><i class="fa-solid fa-star"></i> ${item.rating}</span>
                    </p>
                    ${item.verified ? '<span class="verified"><i class="fa-solid fa-circle-check"></i> Verified</span>' : ''}
                </div>
            `;

            card.addEventListener("click", function () {
                map.flyTo([item.lat, item.lng], 14, { duration: 1.2 });
                leafletMarker.openPopup();
            });

            industryListEl.appendChild(card);
        }
    });
}

// Search Location OR Company Name/Category across Map & Knowledge Graph
function searchLocation(queryText) {
    // Also trigger Knowledge Graph traversal search
    searchKnowledgeGraph(queryText);

    if (!queryText || queryText.trim() === "") {
        renderIndustries(ALL_INDUSTRIES);
        map.flyTo([18.5204, 73.8567], 11, { duration: 1.2 });
        return;
    }

    const cleanQuery = queryText.trim().toLowerCase();

    const directMatches = ALL_INDUSTRIES.filter(item => 
        item.name.toLowerCase().includes(cleanQuery) ||
        item.address.toLowerCase().includes(cleanQuery) ||
        item.category.toLowerCase().includes(cleanQuery) ||
        (item.products && item.products.toLowerCase().includes(cleanQuery))
    );

    if (directMatches.length > 0) {
        renderIndustries(directMatches);
        const topMatch = directMatches[0];
        map.flyTo([topMatch.lat, topMatch.lng], 13, { duration: 1.5 });
        const targetMarker = markers.find(m => m.id === topMatch.id);
        if (targetMarker) {
            setTimeout(() => targetMarker.leafletMarker.openPopup(), 1600);
        }
        return;
    }

    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(queryText)}`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lon = parseFloat(result.lon);

                map.flyTo([lat, lon], 12, { duration: 1.5 });

                const nearby = ALL_INDUSTRIES.filter(ind => getDistanceKm(lat, lon, ind.lat, ind.lng) <= 150);

                if (nearby.length > 0) {
                    renderIndustries(nearby);
                } else {
                    fetchNearbyIndustries(lat, lon, result.display_name.split(",")[0]);
                }
            } else {
                renderIndustries([]);
            }
        })
        .catch(err => {
            console.error("Geocoding fetch error:", err);
            renderIndustries([]);
        });
}

function fetchNearbyIndustries(lat, lon, placeName) {
    const dynamicItems = [
        {
            id: 101,
            name: `${placeName} Industrial Engineering Hub`,
            category: "Manufacturing",
            color: "#ef4444",
            iconClass: "fa-industry",
            lat: lat + 0.02,
            lng: lon + 0.02,
            address: `Phase I Industrial Zone, ${placeName}`,
            rating: 4.6,
            verified: true,
            phone: "+91 98000 11223",
            products: "Machinery Parts, Structural Assemblies"
        },
        {
            id: 102,
            name: `${placeName} High-Tech Pharma Labs`,
            category: "Pharmaceuticals",
            color: "#3b82f6",
            iconClass: "fa-vial",
            lat: lat - 0.025,
            lng: lon - 0.015,
            address: `Bio Corridor, ${placeName}`,
            rating: 4.7,
            verified: true,
            phone: "+91 98000 44556",
            products: "Pharmaceutical Formulations"
        },
        {
            id: 103,
            name: `${placeName} Synthetic Chemical Works`,
            category: "Chemical",
            color: "#a855f7",
            iconClass: "fa-flask",
            lat: lat + 0.015,
            lng: lon - 0.03,
            address: `GIDC Industrial Area, ${placeName}`,
            rating: 4.4,
            verified: false,
            phone: "+91 98000 77889",
            products: "Industrial Solvents, Reagents"
        }
    ];

    renderIndustries(dynamicItems);
}

// Setup Event Listeners for UI Controls & View Switcher
function initUIControls() {
    // View Switcher (Map View vs Knowledge Graph View)
    const mapBtn = document.getElementById("view-mode-map");
    const graphBtn = document.getElementById("view-mode-graph");
    const mapDiv = document.getElementById("map");
    const gpsBtn = document.querySelector(".gps-btn");
    const kgContainer = document.getElementById("knowledge-graph-container");

    if (mapBtn && graphBtn) {
        mapBtn.addEventListener("click", function () {
            currentViewMode = "map";
            mapBtn.classList.add("active");
            graphBtn.classList.remove("active");

            mapDiv.style.display = "block";
            if (gpsBtn) gpsBtn.style.display = "block";
            if (kgContainer) kgContainer.style.display = "none";

            setTimeout(() => map.invalidateSize(), 100);
        });

        graphBtn.addEventListener("click", function () {
            currentViewMode = "graph";
            graphBtn.classList.add("active");
            mapBtn.classList.remove("active");

            mapDiv.style.display = "none";
            if (gpsBtn) gpsBtn.style.display = "none";
            if (kgContainer) kgContainer.style.display = "block";

            // If graph not rendered yet, fetch and render
            if (!visNetwork) {
                initKnowledgeGraph();
            }
        });
    }

    // Search Box Listener
    const searchInput = document.getElementById("search-box");
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            const val = this.value;
            debounceTimer = setTimeout(() => {
                searchLocation(val);
            }, 300);
        });

        searchInput.addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                clearTimeout(debounceTimer);
                searchLocation(this.value);
            }
        });
    }

    // Category Filter Tags
    const filterTags = document.querySelectorAll(".filter-tags .tag");
    filterTags.forEach(tag => {
        tag.addEventListener("click", function () {
            const isAlreadyActive = this.classList.contains("active");

            filterTags.forEach(t => t.classList.remove("active"));

            if (!isAlreadyActive) {
                this.classList.add("active");
                activeCategory = this.textContent.trim();
            } else {
                activeCategory = null;
            }

            renderIndustries(ALL_INDUSTRIES);
            if (activeCategory) {
                searchKnowledgeGraph(activeCategory);
            } else {
                initKnowledgeGraph();
            }
        });
    });

    // Search Radius Buttons
    const radiusBtns = document.querySelectorAll(".radius-btns button");
    radiusBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            radiusBtns.forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            const radiusText = this.textContent.trim();
            currentRadiusKm = parseInt(radiusText) || 10;

            let targetZoom = 12;
            if (currentRadiusKm <= 1) targetZoom = 15;
            else if (currentRadiusKm <= 5) targetZoom = 14;
            else if (currentRadiusKm <= 10) targetZoom = 12;
            else targetZoom = 9;

            map.setZoom(targetZoom);
        });
    });

    // Clear Filters Button
    const clearFiltersBtn = document.querySelector(".clear-filters");
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener("click", function (e) {
            e.preventDefault();
            activeCategory = null;

            filterTags.forEach(t => t.classList.remove("active"));
            radiusBtns.forEach(b => b.classList.remove("active"));

            const tenKmBtn = document.querySelector(".radius-btns button:nth-child(3)");
            if (tenKmBtn) tenKmBtn.classList.add("active");

            if (searchInput) searchInput.value = "";

            renderIndustries(ALL_INDUSTRIES);
            initKnowledgeGraph();
            map.flyTo([18.5204, 73.8567], 11, { duration: 1.2 });
        });
    }

    // GPS / My Location Button
    if (gpsBtn) {
        gpsBtn.addEventListener("click", function () {
            if (!navigator.geolocation) {
                alert("Geolocation is not supported by your browser.");
                return;
            }

            gpsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

            navigator.geolocation.getCurrentPosition(
                pos => {
                    const lat = pos.coords.latitude;
                    const lng = pos.coords.longitude;
                    userCoords = [lat, lng];

                    map.flyTo(userCoords, 13, { duration: 1.5 });

                    if (userLocationMarker) {
                        map.removeLayer(userLocationMarker);
                    }

                    userLocationMarker = L.circleMarker(userCoords, {
                        radius: 10,
                        fillColor: "#3b82f6",
                        color: "#ffffff",
                        weight: 3,
                        opacity: 1,
                        fillOpacity: 0.9
                    }).addTo(map);

                    userLocationMarker.bindPopup("<b>Your Current Location</b>").openPopup();

                    gpsBtn.innerHTML = '<i class="fa-solid fa-location-arrow"></i>';
                },
                err => {
                    console.error("GPS Error:", err);
                    alert("Could not obtain your GPS location. Please check browser permissions.");
                    gpsBtn.innerHTML = '<i class="fa-solid fa-location-arrow"></i>';
                }
            );
        });
    }
}
