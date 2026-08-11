/* SmartReco tracking client — Core 22 contract, dependency-free by design.
   Buffered batches, throttled dwell heartbeats, sendBeacon flush on exit,
   client UUID event IDs (idempotency), capped retry, silent failure.
   Policy values (POL-TRACK-001/002/003) are injected via data- attributes. */
(function () {
  "use strict";
  var cfg = document.currentScript.dataset;
  var BATCH = +cfg.batchSize || 10, FLUSH_MS = (+cfg.flushInterval || 15) * 1000;
  var HEART_MS = (+cfg.heartbeat || 10) * 1000, RETRIES = +cfg.maxRetries || 3;
  var MAX_BUFFER = 100;

  var buffer = [], timer = null, dwellTopic = cfg.dwellTopic || null;

  function uuid() {
    return (crypto.randomUUID && crypto.randomUUID()) ||
      "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        var r = (Math.random() * 16) | 0; return (c === "x" ? r : (r & 3) | 8).toString(16);
      });
  }
  function sessionId() {
    try {
      var s = JSON.parse(sessionStorage.getItem("sr_session") || "null");
      var now = Date.now(), timeout = (+cfg.sessionTimeout || 30) * 60000;
      // sessionStorage is scoped to the tab, not to the person using it: a
      // logout/login keeps the previous shopper's id alive. A session is one
      // person's sitting, so a different user starts a new one. The server
      // namespaces by user regardless (Decision #043) — this keeps the
      // behavioural boundary honest, it is not what enforces isolation.
      if (!s || now - s.last > timeout || s.user !== (cfg.user || ""))
        s = { id: "s-" + uuid(), last: now, user: cfg.user || "" };
      s.last = now;
      sessionStorage.setItem("sr_session", JSON.stringify(s));
      return s.id;
    } catch (e) { return "s-fallback"; }
  }

  function track(type, metadata) {
    buffer.push({ event_id: uuid(), session_id: sessionId(), event_type: type,
                  ts: new Date().toISOString(), metadata: metadata || {} });
    if (buffer.length > MAX_BUFFER) {          // overflow: drop oldest low-signal first
      var i = buffer.findIndex(function (e) { return e.event_type === "DWELL"; });
      buffer.splice(i >= 0 ? i : 0, 1);
    }
    var el = document.getElementById("buffer-count");
    if (el) el.textContent = buffer.length;
    if (buffer.length >= BATCH) flush();
    else if (!timer) timer = setTimeout(flush, FLUSH_MS);
  }

  function send(events, attempt) {
    fetch("/events/batch", {
      method: "POST", credentials: "same-origin", keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: events })
    }).then(function (r) { if (!r.ok) throw new Error(); })
      .catch(function () {                     // capped retry, then drop — silent
        if (attempt < RETRIES) setTimeout(function () { send(events, attempt + 1); },
                                          1000 * Math.pow(2, attempt));
      });
  }

  function flush() {
    clearTimeout(timer); timer = null;
    if (!buffer.length) return;
    var out = buffer.splice(0, buffer.length);
    var el = document.getElementById("buffer-count");
    if (el) el.textContent = "0";
    send(out, 0);
  }

  function beacon() {                          // exit flush — survives navigation
    if (!buffer.length) return;
    var payload = JSON.stringify({ events: buffer.splice(0, buffer.length) });
    try { navigator.sendBeacon("/events/batch", new Blob([payload], { type: "application/json" })); }
    catch (e) { /* silent by design */ }
  }

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") beacon();
  });
  window.addEventListener("pagehide", beacon);

  setInterval(function () {                    // throttled heartbeats, visible only
    if (dwellTopic && document.visibilityState === "visible")
      track("DWELL", { topic: dwellTopic, seconds: HEART_MS / 1000 });
  }, HEART_MS);

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-track]");
    if (t) { try { track(t.dataset.track, JSON.parse(t.dataset.trackMeta || "{}")); } catch (err) {} }
  });

  window.smartreco = { track: track, flush: flush,    // page templates emit via this
                       setDwellTopic: function (t) { dwellTopic = t; } };
  var initial = document.getElementById("sr-page-events");
  if (initial) {
    try { JSON.parse(initial.textContent).forEach(function (e) { track(e.type, e.metadata); }); }
    catch (e) { /* silent by design */ }
  }
})();
