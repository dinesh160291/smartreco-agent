/* SmartReco UI behaviors: theme toggle, tabs, toast. No frameworks. */
(function () {
  "use strict";
  var stored = localStorage.getItem("sr_theme");
  if (stored) document.documentElement.dataset.theme = stored;

  window.srToggleTheme = function () {
    var html = document.documentElement;
    var dark = html.dataset.theme === "dark" ||
      (!html.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    html.dataset.theme = dark ? "light" : "dark";
    localStorage.setItem("sr_theme", html.dataset.theme);
  };

  window.srToast = function (message) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    setTimeout(function () { el.classList.remove("show"); }, 2600);
  };

  document.addEventListener("click", function (e) {
    var tab = e.target.closest(".tabs button");
    if (!tab) return;
    var name = tab.dataset.tab;
    tab.closest(".tabs").querySelectorAll("button").forEach(function (b) {
      b.classList.toggle("active", b === tab);
    });
    document.querySelectorAll(".tabpane").forEach(function (p) {
      p.classList.toggle("active", p.dataset.pane === name);
    });
    if (window.smartreco && tab.dataset.dwellTopic !== undefined) {
      window.smartreco.setDwellTopic(tab.dataset.dwellTopic || null);
    }
  });
})();
