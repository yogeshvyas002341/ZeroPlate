"use strict";

const dateElement = document.getElementById("service-date");
const statusElement = document.getElementById("api-status");
const rowsElement = document.getElementById("forecast-rows");
const itemStyles = {
  "Rajma chawal": ["🍛", "dish-yellow", "Main course"],
  "Seasonal veg thali": ["🥗", "dish-green", "Main course"],
  "Masala dosa": ["🍲", "dish-red", "Live counter"],
  "Gulab jamun": ["🍮", "dish-pink", "Dessert"],
};

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function makeCell(text, className) {
  const cell = document.createElement("td");
  if (className) cell.className = className;
  cell.textContent = text;
  return cell;
}

function makeDishCell(item) {
  const [emoji, style, category] = itemStyles[item.item] || ["🍽️", "dish-green", "Menu item"];
  const cell = document.createElement("td");
  const icon = document.createElement("span");
  icon.className = `dish-icon ${style}`;
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = emoji;
  const name = document.createElement("span");
  name.className = "dish-name";
  name.append(document.createTextNode(item.item));
  const detail = document.createElement("small");
  detail.textContent = category;
  name.append(detail);
  cell.append(icon, name);
  return cell;
}

function makeQuantityCell(value, emphasize) {
  const cell = document.createElement("td");
  if (emphasize) {
    const strong = document.createElement("strong");
    strong.textContent = value;
    cell.append(strong, document.createTextNode(" portions"));
  } else {
    cell.textContent = `${value} portions`;
  }
  return cell;
}

function renderForecast(data) {
  rowsElement.replaceChildren();

  for (const item of data.forecasts) {
    const row = document.createElement("tr");
    row.append(
      makeDishCell(item),
      makeQuantityCell(item.predicted_qty, false),
      makeQuantityCell(item.recommended_qty, true),
      makeQuantityCell(item.last_week_qty, false),
    );

    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `status-pill ${item.status === "Review" ? "status-review" : "status-ready"}`;
    const indicator = document.createElement("i");
    indicator.setAttribute("aria-hidden", "true");
    status.append(indicator, document.createTextNode(item.status));
    statusCell.append(status);
    row.append(statusCell);
    rowsElement.append(row);
  }

  const total = data.forecasts.reduce((sum, item) => sum + item.predicted_qty, 0);
  const production = data.forecasts.reduce((sum, item) => sum + item.recommended_qty, 0);
  setText("total-forecast", total);
  setText("total-prepare", production);
  setText("pipeline-total", production);
  setText("model-rmse", data.average_rmse.toFixed(1));
  setText("history-days", data.history_days);
  setText("model-name", data.model);
  setText("model-detail", "trained on demo history");
  setText("updated-at", `Updated ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`);
  statusElement.classList.add("model-online");
  statusElement.classList.remove("model-offline");
  statusElement.lastChild.textContent = "Scikit-learn model online";
}

function showDemoFallback() {
  statusElement.classList.add("model-offline");
  statusElement.classList.remove("model-online");
  statusElement.lastChild.textContent = "Demo preview · API offline";
  setText("model-detail", "demo preview");
  setText("updated-at", "Start Flask for live forecasts");
}

if (dateElement) {
  dateElement.textContent = new Intl.DateTimeFormat("en", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date()).toUpperCase();
}

statusElement.innerHTML = "<i></i>Connecting to forecast model…";
fetch("/api/forecast")
  .then((response) => {
    if (!response.ok) throw new Error(`Forecast API returned ${response.status}`);
    return response.json();
  })
  .then(renderForecast)
  .catch(() => showDemoFallback());
