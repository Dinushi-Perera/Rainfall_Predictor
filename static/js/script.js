(function () {
  "use strict";

  const form = document.getElementById("predictForm");
  const submitBtn = document.getElementById("submitBtn");
  const formHint = document.getElementById("formHint");
  const fillSampleBtn = document.getElementById("fillSampleBtn");

  const mascotSvg = document.getElementById("mascotSvg");
  const miniRain = document.getElementById("miniRain");
  const sunBurst = document.getElementById("sunBurst");
  const sky = document.getElementById("sky");
  const rainLayer = document.getElementById("rainLayer");
  const sunGlow = document.getElementById("sunGlow");

  const resultPlaceholder = document.getElementById("resultPlaceholder");
  const resultContent = document.getElementById("resultContent");
  const resultBadge = document.getElementById("resultBadge");
  const resultHeadline = document.getElementById("resultHeadline");
  const resultSub = document.getElementById("resultSub");
  const resultNote = document.getElementById("resultNote");
  const gaugeFill = document.getElementById("gaugeFill");
  const gaugeValue = document.getElementById("gaugeValue");

  const historyBody = document.getElementById("historyBody");
  const statsStrip = document.getElementById("statsStrip");

  const FIELDS = [
    "day", "pressure", "maxtemp", "temparature", "mintemp", "dewpoint",
    "humidity", "cloud", "sunshine", "winddirection", "windspeed",
  ];

  const SAMPLE_DAYS = [
    { day: 1, pressure: 1019.5, maxtemp: 17.5, temparature: 15.8, mintemp: 12.7, dewpoint: 14.9, humidity: 96, cloud: 99, sunshine: 0, winddirection: 50, windspeed: 24.3 },
    { day: 4, pressure: 1022.9, maxtemp: 20.6, temparature: 17.3, mintemp: 15.2, dewpoint: 9.5, humidity: 75, cloud: 45, sunshine: 7.1, winddirection: 20, windspeed: 50.6 },
    { day: 5, pressure: 1022.2, maxtemp: 16.1, temparature: 13.8, mintemp: 6.4, dewpoint: 4.3, humidity: 68, cloud: 49, sunshine: 9.2, winddirection: 20, windspeed: 19.4 },
    { day: 3, pressure: 1023.9, maxtemp: 11.2, temparature: 10.4, mintemp: 9.4, dewpoint: 8.9, humidity: 86, cloud: 96, sunshine: 0, winddirection: 40, windspeed: 16.9 },
  ];

  // ---------------------------------------------------------------------
  // Ambient background: a few dozen falling raindrops, built once.
  // ---------------------------------------------------------------------
  function buildRainLayer(container, count, opts) {
    container.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const drop = document.createElement("span");
      const left = Math.random() * 100;
      const duration = (opts.minDur + Math.random() * (opts.maxDur - opts.minDur)).toFixed(2);
      const delay = (Math.random() * opts.maxDur).toFixed(2);
      drop.style.left = left + "%";
      drop.style.animationDuration = duration + "s";
      drop.style.animationDelay = "-" + delay + "s";
      if (opts.mini) {
        drop.style.left = (10 + Math.random() * 80) + "%";
      }
      container.appendChild(drop);
    }
  }
  buildRainLayer(rainLayer, 60, { minDur: 1.4, maxDur: 3.2 });
  buildRainLayer(miniRain, 14, { minDur: 0.7, maxDur: 1.3, mini: true });

  // ---------------------------------------------------------------------
  // Validation
  // ---------------------------------------------------------------------
  function fieldEl(name) { return document.querySelector(`.field[data-field="${name}"]`); }

  function validateField(input) {
    const wrap = fieldEl(input.name);
    const errEl = document.getElementById("err-" + input.name);
    const lo = parseFloat(input.min);
    const hi = parseFloat(input.max);
    const raw = input.value.trim();

    let message = "";
    if (raw === "") {
      message = "Required.";
    } else {
      const val = parseFloat(raw);
      if (Number.isNaN(val)) message = "Enter a number.";
      else if (val < lo || val > hi) message = `Must be ${lo}–${hi}.`;
    }

    if (message) {
      wrap.classList.add("invalid");
      wrap.classList.remove("valid");
      errEl.textContent = message;
      return false;
    }
    wrap.classList.remove("invalid");
    wrap.classList.add("valid");
    errEl.textContent = "";
    return true;
  }

  FIELDS.forEach((name) => {
    const input = document.getElementById(name);
    input.addEventListener("input", () => validateField(input));
    input.addEventListener("blur", () => validateField(input));
  });

  function validateAll() {
    let allValid = true;
    FIELDS.forEach((name) => {
      const input = document.getElementById(name);
      if (!validateField(input)) allValid = false;
    });
    // cross-field: mintemp <= maxtemp
    const mintemp = parseFloat(document.getElementById("mintemp").value);
    const maxtemp = parseFloat(document.getElementById("maxtemp").value);
    if (!Number.isNaN(mintemp) && !Number.isNaN(maxtemp) && mintemp > maxtemp) {
      const wrap = fieldEl("mintemp");
      wrap.classList.add("invalid");
      document.getElementById("err-mintemp").textContent = "Can't exceed max temp.";
      allValid = false;
    }
    return allValid;
  }

  // ---------------------------------------------------------------------
  // Sample data button
  // ---------------------------------------------------------------------
  fillSampleBtn.addEventListener("click", () => {
    const sample = SAMPLE_DAYS[Math.floor(Math.random() * SAMPLE_DAYS.length)];
    FIELDS.forEach((name) => {
      const input = document.getElementById(name);
      input.value = sample[name];
      validateField(input);
    });
    formHint.textContent = "";
    fillSampleBtn.classList.add("btn-ghost");
  });

  // ---------------------------------------------------------------------
  // Mascot state machine
  // ---------------------------------------------------------------------
  function setMascotState(state) {
    mascotSvg.classList.remove("thinking", "rainy", "sunny");
    miniRain.classList.remove("active");
    sunBurst.classList.remove("active");
    rainLayer.classList.remove("active");
    sunGlow.classList.remove("active");
    sky.classList.remove("mood-sun");

    if (state === "thinking") {
      mascotSvg.classList.add("thinking");
    } else if (state === "rain") {
      mascotSvg.classList.add("rainy");
      miniRain.classList.add("active");
      rainLayer.classList.add("active");
    } else if (state === "sun") {
      mascotSvg.classList.add("sunny");
      sunBurst.classList.add("active");
      sunGlow.classList.add("active");
      sky.classList.add("mood-sun");
    }
  }

  // ---------------------------------------------------------------------
  // Result rendering
  // ---------------------------------------------------------------------
  const RAIN_HEADLINES = [
    "Grab your umbrella!", "Splash alert! ☔", "The clouds mean business.",
    "Puddle-jumping weather ahead.",
  ];
  const NO_RAIN_HEADLINES = [
    "Sunny skies ahead!", "Clear day — go enjoy it!", "Not a raindrop in sight.",
    "Blue skies, no umbrella needed.",
  ];

  function renderResult(data) {
    resultPlaceholder.hidden = true;
    resultContent.hidden = false;

    const willRain = data.will_rain;
    resultBadge.textContent = willRain ? "Rain" : "No Rain";
    resultBadge.className = "result-badge " + (willRain ? "rain" : "no-rain");

    const headlines = willRain ? RAIN_HEADLINES : NO_RAIN_HEADLINES;
    resultHeadline.textContent = headlines[Math.floor(Math.random() * headlines.length)];
    resultSub.textContent = willRain
      ? "There's a strong chance of rain today — the model is fairly confident."
      : "Conditions point to a dry day — enjoy the sunshine.";

    const pct = data.probability;
    const circumference = 157; // matches the SVG path length
    const offset = circumference - (circumference * pct) / 100;
    gaugeFill.style.stroke = willRain ? "var(--rain-teal-bright)" : "var(--sunshine-gold)";
    requestAnimationFrame(() => {
      gaugeFill.style.strokeDashoffset = offset;
    });

    let frame = 0;
    const target = pct;
    const counter = setInterval(() => {
      frame += 1;
      const current = Math.min(target, (target / 20) * frame);
      gaugeValue.textContent = current.toFixed(0) + "%";
      if (frame >= 20) clearInterval(counter);
    }, 35);

    resultNote.textContent = `confidence ${data.confidence}% · saved ${data.saved ? "to database ✓" : "locally (DB unavailable)"}`;

    setMascotState(willRain ? "rain" : "sun");
  }

  // ---------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    formHint.textContent = "";

    if (!validateAll()) {
      formHint.textContent = "Please fix the highlighted fields.";
      const firstInvalid = document.querySelector(".field.invalid input");
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    const payload = {};
    FIELDS.forEach((name) => { payload[name] = document.getElementById(name).value; });

    submitBtn.classList.add("loading");
    submitBtn.disabled = true;
    setMascotState("thinking");

    try {
      const resp = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();

      if (!resp.ok || !data.ok) {
        if (data.errors) {
          Object.entries(data.errors).forEach(([field, msg]) => {
            const errEl = document.getElementById("err-" + field);
            if (errEl) {
              errEl.textContent = msg;
              fieldEl(field) && fieldEl(field).classList.add("invalid");
            } else {
              formHint.textContent = msg;
            }
          });
        } else {
          formHint.textContent = "Something went wrong. Please try again.";
        }
        setMascotState("idle");
        return;
      }

      renderResult(data);
      loadHistory();
      loadStats();
    } catch (err) {
      formHint.textContent = "Network error — is the server running?";
      setMascotState("idle");
    } finally {
      submitBtn.classList.remove("loading");
      submitBtn.disabled = false;
    }
  });

  // ---------------------------------------------------------------------
  // History + stats
  // ---------------------------------------------------------------------
  async function loadHistory() {
    try {
      const resp = await fetch("/history");
      const data = await resp.json();
      if (!data.ok || !data.history.length) return;

      historyBody.innerHTML = "";
      data.history.forEach((row) => {
        const tr = document.createElement("tr");
        const isRain = row.prediction_label === "Rain";
        tr.innerHTML = `
          <td>${row.created_at}</td>
          <td>${row.day}</td>
          <td>${row.temparature}°C</td>
          <td>${row.humidity}%</td>
          <td>${row.cloud}%</td>
          <td><span class="pill ${isRain ? "rain" : "no-rain"}">${row.prediction_label}</span></td>
          <td>${(row.rain_probability * 100).toFixed(1)}%</td>
        `;
        historyBody.appendChild(tr);
      });
    } catch (err) { /* silent — history is a nice-to-have */ }
  }

  async function loadStats() {
    try {
      const resp = await fetch("/stats");
      const data = await resp.json();
      if (!data.ok) return;
      const s = data.stats;
      statsStrip.innerHTML = `
        <span><b>${s.total}</b> logged</span>
        <span><b>${s.rain_count}</b> rain calls</span>
        <span><b>${(s.avg_probability * 100).toFixed(0)}%</b> avg. chance</span>
      `;
    } catch (err) { /* silent */ }
  }

  loadHistory();
  loadStats();
})();
