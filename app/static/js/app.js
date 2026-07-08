/* Comportements front génériques : bandeau cookies + zone de dépôt de fichier. */
(function () {
  "use strict";

  // -- Bandeau cookies (RGPD) : affiché tant que l'utilisateur n'a pas validé.
  var banner = document.getElementById("cookie-banner");
  if (banner) {
    var CLE = "pdv_cookie_consent";
    if (!localStorage.getItem(CLE)) {
      banner.hidden = false;
    }
    var accept = banner.querySelector("[data-cookie-accept]");
    if (accept) {
      accept.addEventListener("click", function () {
        localStorage.setItem(CLE, "1");
        banner.hidden = true;
      });
    }
  }

  // -- Zone de dépôt de fichier (écran Import) : glisser-déposer + nom affiché.
  var dropzone = document.querySelector("[data-dropzone]");
  if (dropzone) {
    var input = dropzone.querySelector('input[type="file"]');
    var label = dropzone.querySelector("[data-filename]");
    var parcourir = dropzone.querySelector("[data-browse]");

    if (parcourir && input) {
      parcourir.addEventListener("click", function (e) {
        e.preventDefault();
        input.click();
      });
    }
    if (input) {
      input.addEventListener("change", function () {
        if (input.files.length && label) {
          label.textContent = "Fichier sélectionné : " + input.files[0].name;
        }
      });
    }
    ["dragenter", "dragover"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });
    dropzone.addEventListener("drop", function (e) {
      if (e.dataTransfer.files.length && input) {
        input.files = e.dataTransfer.files;
        if (label) label.textContent = "Fichier sélectionné : " + input.files[0].name;
      }
    });
  }
})();
