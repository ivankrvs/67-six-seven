console.log("Приложение запущено");


const map = L.map('map').setView([52.3702, 4.8952], 13);
setTimeout(() => {
    map.invalidateSize();
}, 300);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);



let userMarker = null;
let parkingZoneGeoJSON = null;

let isInZone = false;
let wasInZone = false;
let isParkingActive = false;
let parkingStartTime = null;
let timerInterval = null;
let zoneInitialized = false;
let liveCostInterval = null;
let zones = [];
let activeZone = null;
let zoneLayers = [];
let lastZonePrice = 5;
let lastZoneName = "";
let parkingHistory = [];
let pulseInterval = null;

let watchId = null;
let exitTimeout = null;

// загружаем зоны из geojsopn
function loadParkingZones() {

    if (!map) {
        console.error("Map not initialized");
        return;
    }

    console.log(" Loading GeoJSON zones");

    fetch('data/parking-zone.geojson', {
        cache: "no-store"
    })
    .then(res => {

        console.log(" Response:", res.status);

        if (!res.ok) {
            throw new Error(`HTTP error ${res.status}`);
        }

        return res.json();
    })
    
    
    .then(data => {

    console.log(" GeoJSON loaded");

    if (!data || data.type !== "FeatureCollection") {
        throw new Error("Invalid GeoJSON format");
    }

    zones = data.features || [];
    zoneLayers = [];

    zones.forEach((feature, index) => {

        try {
            if (!feature?.geometry?.coordinates) {
                console.warn("Skipping invalid feature:", feature);
                return;
            }

            const layer = L.geoJSON(feature, {
                style: {
                    color: "#3b82f6",
                    fillColor: "#3b82f6",
                    fillOpacity: 0.3,
                    weight: 2
                }
            }).addTo(map);

            const zoneName =
                feature.properties?.name || `Zone ${index + 1}`;

            const price =
                feature.properties?.price_per_hour ?? 5;

            zoneLayers.push({
                id: feature.id ?? index,
                name: zoneName,
                price: price,
                layer: layer,
                data: feature
            });

        } catch (featureError) {
            console.error("Ошибка в зоне:", featureError);
        }
    });

    

    console.log(`Zones rendered: ${zoneLayers.length}`);

    // отдельно защищаем
    try {
        fitMapToZones();
    } catch (e) {
        console.warn("fitMapToZones error:", e);
    }

    
})

.catch(err => {
    console.error(" GeoJSON load error:", err);

    // показываем только если реально ничего не загрузилось
    if (!zones || zones.length === 0) {
        showNotification("Ошибка загрузки зон парковки", "error");
    }
});
}

loadParkingZones();


//логика зоны парковки

function handleZoneLogic(lat, lng) {

    const point = turf.point([lng, lat]);

    let foundZone = null;

    zones.forEach(zone => {
        const poly = turf.polygon(zone.geometry.coordinates);

        if (turf.booleanPointInPolygon(point, poly)) {
            foundZone = zone;
        }
    });

    const statusEl = document.getElementById("status");

    if (foundZone) {

        statusEl.textContent =
            `В зоне: ${foundZone.properties.name}`;

        statusEl.style.color = "green";

        highlightZone(foundZone);

        if (!activeZone && !isParkingActive) {
            activeZone = foundZone;
            startParkingWithZone(foundZone);

            showNotification("Парковка началась");
        }

    } else {

        statusEl.textContent = "Вне зон";
        statusEl.style.color = "red";

        zoneLayers.forEach(z => {
            z.layer.setStyle({
                fillOpacity: 0.2,
                color: "#999",
                weight: 1
            });
        });

        //  автозавершение при выходе
        if (isParkingActive && activeZone) {
            showNotification("Вы вышли из зоны — завершение");

            activeZone = null;
            stopParking();
        }
    }

    updateButtons();
}

// постоянная геолокация
function getUserLocation() {
    if (!navigator.geolocation) {
        showNotification("Геолокация не поддерживается");
        return;
    }

    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
    }

    watchId = navigator.geolocation.watchPosition(
        (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;

            if (userMarker) {
                userMarker.setLatLng([lat, lng]);
            } else {
                userMarker = L.marker([lat, lng]).addTo(map);
            }

            map.setView([lat, lng], 15);

            handleZoneLogic(lat, lng);
        },
        (error) => {
            console.error("Ошибка геолокации:", error);
        },
        {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 10000
        }
    );
}

// кнопки
function updateButtons() {
    document.getElementById("startBtn").disabled =
        !isInZone || isParkingActive;

    document.getElementById("stopBtn").disabled =
        !isParkingActive;
}

// стартуем
function startParking(zone) {

    isParkingActive = true;
    activeZone = zone;


    // фикс тарифа и зоны
    lastZonePrice = zone.properties.price_per_hour || 5;
    lastZoneName = zone.properties.name || "Zone";

    parkingStartTime = Date.now();

   timerInterval = setInterval(() => {
    updateTimer();
    updateLiveCost();
    checkZoneExit();   
}, 1000);
    document.getElementById("sessionCard").classList.add("active");
}

// таймер
function updateTimer() {

    const seconds = Math.floor((Date.now() - parkingStartTime) / 1000);

    const minutes = Math.floor(seconds / 60);
    const sec = seconds % 60;

    document.getElementById("timer").textContent =
        `${minutes} мин ${sec} сек`;

    document.getElementById("sessionTime").textContent =
        `⏱ ${seconds} сек`;

    const cost = (seconds / 3600) * lastZonePrice;

    document.getElementById("sessionCost").textContent =
        `💰 ${cost.toFixed(2)} BYN`;
}

// завершении пакровки
function stopParking(reason = "manual") {

    if (!isParkingActive) return;

    // запрет только для ручного завершения
    if (reason === "manual" && activeZone) {
        showNotification(" Выйдите из зоны для завершения", "warning");
        return;
    }

    clearInterval(timerInterval);
    stopZoneAnimation();

    const totalSeconds =
        Math.floor((Date.now() - parkingStartTime) / 1000);

    const cost =
        (totalSeconds / 3600) * lastZonePrice;

    const roundedCost = cost.toFixed(2);

    //  сохраняем
    saveParkingToHistory(totalSeconds, roundedCost);

    // вывод результата
    document.getElementById("result").innerHTML = `
        ⏱ <b>Время:</b> ${totalSeconds} сек <br>
        💰 <b>Стоимость:</b> ${roundedCost} BYN <br>
        ✅ <b>Статус:</b> Завершено
    `;

    //  уведомление
    if (reason === "auto") {
        showNotification(" Парковка завершена автоматически", "warning");
    } else {
        showNotification(" Парковка завершена", "success");
    }

    // сброс состояния
    isParkingActive = false;
    parkingStartTime = null;
    activeZone = null;

    // UI reset
    document.getElementById("timer").textContent = "0";

    document.getElementById("sessionCard").classList.remove("active");

    document.getElementById("sessionStatus").textContent =
        "Нет активной парковки";

    document.getElementById("sessionTime").textContent =
        "⏱ 0 сек";

    document.getElementById("sessionCost").textContent =
        "💰 0 BYN";

    updateZonePanel(null);

    updateButtons();

    // чек
    showReceipt(totalSeconds, roundedCost);
}

function checkZoneExit() {
    if (!isParkingActive || !activeZone) return;

    const inside = turf.booleanPointInPolygon(
        userMarker.getLatLng().toGeoJSON(),
        activeZone
    );

    if (!inside) {
        showNotification("Вы покинули зону парковки. Сессия завершена.", "warning");
        stopParking();
    }
}

// события
document.getElementById("locateBtn")
    .addEventListener("click", getUserLocation);

document.getElementById("startBtn")
    .addEventListener("click", startParking);

document.getElementById("stopBtn")
    .addEventListener("click", stopParking);

    // сохранение в локальном сторедже
function saveParkingToHistory(seconds, cost) {
    const history = JSON.parse(localStorage.getItem("parkingHistory")) || [];

    const record = {
        time: seconds,
        cost: cost,
        date: new Date().toLocaleString()
    };

    history.unshift(record); // добавляем в начало

    localStorage.setItem("parkingHistory", JSON.stringify(history));

    renderHistory();
}


function startParkingWithZone(zone) {

    isParkingActive = true;
    parkingStartTime = Date.now();

    document.getElementById("sessionCard").classList.add("active");

    document.getElementById("sessionStatus").textContent =
        "🟢 " + (zone.properties.name || "Активная зона");

    timerInterval = setInterval(updateTimer, 1000);

    updateButtons();
}

function showReceipt(seconds, cost) {

    const zoneName =
        activeZone?.properties?.name || "Без зоны";

    document.getElementById("receiptZone").textContent =
        "📍 Зона: " + zoneName;

    document.getElementById("receiptTime").textContent =
        "⏱ Время: " + seconds + " сек";

    document.getElementById("receiptCost").textContent =
        "💰 Сумма: " + cost + " €";

    document.getElementById("receiptModal").classList.remove("hidden");
}

document.getElementById("closeReceiptBtn").addEventListener("click", () => {
    document.getElementById("receiptModal").classList.add("hidden");
});



function updateUI() {

    if (!isParkingActive) return;

    const seconds =
        Math.floor((Date.now() - parkingStartTime) / 1000);

    const cost =
        (seconds / 3600) * lastZonePrice;

    document.getElementById("sessionTime").textContent =
        "⏱ " + seconds + " сек";

    document.getElementById("sessionCost").textContent =
        "💰 " + cost.toFixed(2) + " BYN";

    updateZonePanel(
        activeZone,
        seconds,
        cost
    );
}

function renderHistory() {

    const container = document.getElementById("historyList");
    container.innerHTML = "";

    parkingHistory.forEach(item => {

        const div = document.createElement("div");
        div.className = "history-item";

        div.innerHTML = `
            ⏱ ${item.time} сек <br>
            💰 ${item.cost} Br
        `;

        container.appendChild(div);
    });
}

function saveParkingToHistory(time, cost) {

    parkingHistory.push({
        time: time,
        cost: cost
    });

    renderHistory(); 
}

function animateActiveZone(layer) {

    if (!layer) return;

    let growing = true;
    let opacity = 0.2;

    clearInterval(pulseInterval);

    pulseInterval = setInterval(() => {

        if (growing) {
            opacity += 0.02;
            if (opacity >= 0.5) growing = false;
        } else {
            opacity -= 0.02;
            if (opacity <= 0.2) growing = true;
        }

        layer.setStyle({
            fillOpacity: opacity,
            weight: 2,
            color: "#22c55e"
        });

    }, 50);
}

function stopZoneAnimation() {
    clearInterval(pulseInterval);
}

function highlightZone(active) {

    zoneLayers.forEach(z => {

        if (z.data === active) {

            z.layer.setStyle({
                color: "#22c55e",
                fillOpacity: 0.45,
                weight: 3
            });

            animateActiveZone(z.layer);

        } else {

            z.layer.setStyle({
                color: "#94a3b8",
                fillOpacity: 0.1,
                weight: 1
            });
        }
    });
}

function showNotification(message, type = "info") {
    const container = document.getElementById("notifications");

    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.innerText = message;

    container.appendChild(el);

    setTimeout(() => {
        el.remove();
    }, 3000);
}

function updateLiveCost() {
    if (!isParkingActive || !parkingStartTime || !activeZone) return;

    const seconds = Math.floor((Date.now() - parkingStartTime) / 1000);
    const pricePerHour = activeZone.properties.price_per_hour;

    const cost = (seconds / 3600) * pricePerHour;

    document.getElementById("sessionTime").textContent =
        `⏱ ${seconds} сек`;

    document.getElementById("sessionCost").textContent =
        `💰 ${cost.toFixed(2)} BYN`;
}