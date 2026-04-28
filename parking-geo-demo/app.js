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
fetch('data/parking-zone.geojson')
    .then(res => res.json())
    .then(data => {
        zones = data.features;

        // отрисовка всех зон
        zones.forEach((zone, index) => {

    const layer = L.geoJSON(zone, {
        style: {
            color: getColor(index),
            fillColor: getColor(index),
            fillOpacity: 0.25,
            weight: 2
        }
    }).addTo(map);

    zoneLayers.push({
        id: zone.id,
        name: zone.properties.name,
        layer: layer,
        data: zone
    });
});

        console.log("Зоны загружены:", zones.length);
    });



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
            `В зоне: ${foundZone.properties.name || "Zone"}`;
        statusEl.style.color = "green";

        //  ПОДСВЕТКА АКТИВНОЙ ЗОНЫ
        highlightZone(foundZone);

        //  автостарт
        if (!activeZone && !isParkingActive) {
            activeZone = foundZone;

            startParkingWithZone(foundZone);

            showToast("🚀 Парковка началась");
        }

        if (exitTimeout) {
            clearTimeout(exitTimeout);
            exitTimeout = null;
        }

    } else {

        statusEl.textContent = "ВНЕ всех зон";
        statusEl.style.color = "red";

        //  сброс подсветки
        zoneLayers.forEach(z => {
            z.layer.setStyle({
                fillOpacity: 0.25,
                color: "#666",
                weight: 2
            });
        });

        if (isParkingActive && !exitTimeout) {
            exitTimeout = setTimeout(() => {
                stopParking();
                activeZone = null;

                showToast("⛔ Парковка завершена автоматически");

            }, 10000);
        }
    }

    updateButtons();
}

// постоянная геолокация
function getUserLocation() {
    if (!navigator.geolocation) {
        alert("Геолокация не поддерживается");
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

    timerInterval = setInterval(updateUI, 1000);

    document.getElementById("sessionCard").classList.add("active");
}

// таймер
function updateTimer() {
    const seconds = Math.floor((Date.now() - parkingStartTime) / 1000);

    const minutes = Math.floor(seconds / 60);
    const sec = seconds % 60;

    document.getElementById("timer").textContent =
        `${minutes} мин ${sec} сек`;

    // обновление ui состояния сессии
    document.getElementById("sessionTime").textContent =
        `⏱ ${seconds} сек`;

    const pricePerHour =
        parkingZoneGeoJSON.features[0].properties.price_per_hour;

    const cost = (seconds / 3600) * pricePerHour;

    document.getElementById("sessionCost").textContent =
        `💰 ${cost.toFixed(2)} €`;
}

// завершении пакровки
function stopParking() {

    //  НЕЛЬЗЯ остановить в зоне
    if (activeZone) {
        showToast("❌ Нельзя завершить парковку, пока вы в зоне");
        return;
    }

    if (!isParkingActive) return;

    clearInterval(timerInterval);

    const totalSeconds =
        Math.floor((Date.now() - parkingStartTime) / 1000);

    // надо взять последний тариф

    const cost = (totalSeconds / 3600) * lastZonePrice;
    const roundedCost = cost.toFixed(2);

    saveParkingToHistory(totalSeconds, roundedCost);

    // UI результат
    const resultEl = document.getElementById("result");

    resultEl.innerHTML = `
    ⏱ <b>Время:</b> ${totalSeconds} сек <br>
    💰 <b>Стоимость:</b> ${roundedCost} € <br>
    ✅ <b>Статус:</b> Оплачено (демо)
    `;

    showToast("Парковка завершена");

    // сброс состояния
    isParkingActive = false;
    parkingStartTime = null;

    document.getElementById("timer").textContent = "Время: 0 сек";

    document.getElementById("sessionCard").classList.remove("active");

    document.getElementById("sessionStatus").textContent =
        "Нет активной парковки";

    document.getElementById("sessionTime").textContent =
        "⏱ 0 сек";

    document.getElementById("sessionCost").textContent =
        "💰 0 €";

    updateZonePanel(null);

    updateButtons();

    showReceipt(totalSeconds, roundedCost);
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

// отрисовка истории праковок
function renderHistory() {
    const history = JSON.parse(localStorage.getItem("parkingHistory")) || [];
    const list = document.getElementById("historyList");

    list.innerHTML = "";

    history.forEach(item => {
        const li = document.createElement("li");

        li.innerHTML = `
            🕒 ${item.date}<br>
            ⏱ ${item.time} сек<br>
            💰 ${item.cost} €
        `;

        list.appendChild(li);
    });
}

renderHistory();

function showToast(message) {
    const toast = document.getElementById("toast");

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

function getColor(index) {
    const colors = ["blue", "green", "red", "orange", "purple"];
    return colors[index % colors.length];
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

function highlightZone(activeZone) {

    zoneLayers.forEach(z => {

        if (z.data === activeZone) {
            z.layer.setStyle({
                fillOpacity: 0.6,
                color: "lime",
                weight: 3
            });
        } else {
            z.layer.setStyle({
                fillOpacity: 0.1,
                color: "#999",
                weight: 1
            });
        }
    });
}

function updateUI() {

    if (!isParkingActive) return;

    const seconds =
        Math.floor((Date.now() - parkingStartTime) / 1000);

    const cost = (seconds / 3600) * lastZonePrice;

    document.getElementById("sessionTime").textContent =
        "⏱ " + seconds + " сек";

    document.getElementById("sessionCost").textContent =
        "💰 " + cost.toFixed(2) + " €";

    // используем lastZoneName если activeZone уже null
    updateZonePanel(
        activeZone || { properties: { name: lastZoneName, price_per_hour: lastZonePrice } },
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
                fillOpacity: 0.4,
                weight: 2
            });

            animateActiveZone(z.layer); // 👈 ВОТ ЭТО

        } else {

            z.layer.setStyle({
                color: "#94a3b8",
                fillOpacity: 0.1,
                weight: 1
            });
        }
    });
}