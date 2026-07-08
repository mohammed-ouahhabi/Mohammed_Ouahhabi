/* Graphiques du tableau de bord (Chart.js). Les données proviennent de balises
   <script type="application/json"> remplies côté serveur (aucune donnée en dur). */
(function () {
  "use strict";
  var VERT = "#0f8b6c";
  var VERT_CLAIR = "rgba(15, 139, 108, 0.12)";
  var GRILLE = "#eef2f7";
  var TEXTE = "#64748b";

  function lire(id, defaut) {
    var el = document.getElementById(id);
    if (!el) return defaut;
    try { return JSON.parse(el.textContent); } catch (e) { return defaut; }
  }

  // -- Évolution du CA (aire) --
  var evo = lire("data-evolution", { labels: [], valeurs: [] });
  var cEvo = document.getElementById("chart-evolution");
  if (cEvo && window.Chart) {
    new Chart(cEvo, {
      type: "line",
      data: {
        labels: evo.labels,
        datasets: [{
          data: evo.valeurs,
          borderColor: VERT,
          backgroundColor: VERT_CLAIR,
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: TEXTE, maxTicksLimit: 8 } },
          y: { grid: { color: GRILLE }, ticks: { color: TEXTE }, beginAtZero: true }
        }
      }
    });
  }

  // -- Pics d'activité (barres par heure) --
  var pics = lire("data-pics", {});
  var cPics = document.getElementById("chart-pics");
  if (cPics && window.Chart) {
    // On affiche la plage d'ouverture 10h -> 23h pour rester lisible.
    var heures = [], valeurs = [], couleurs = [];
    var max = 0;
    for (var h = 10; h <= 23; h++) { max = Math.max(max, pics[h] || 0); }
    for (var i = 10; i <= 23; i++) {
      var v = pics[i] || 0;
      heures.push(i + "h");
      valeurs.push(v);
      couleurs.push(v >= max && max > 0 ? VERT : "#bfd8cf");
    }
    new Chart(cPics, {
      type: "bar",
      data: { labels: heures, datasets: [{ data: valeurs, backgroundColor: couleurs, borderRadius: 6 }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: TEXTE } },
          y: { grid: { color: GRILLE }, ticks: { color: TEXTE, precision: 0 }, beginAtZero: true }
        }
      }
    });
  }
})();
