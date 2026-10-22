/*
 * Birds page: progressive enhancement only. With scripting off the list still
 * renders in alphabetical order; toggling the sort, expanding a row, and the
 * lightbox are additive. No dependencies, no build step.
 */
(function () {
  "use strict";

  var list = document.querySelector(".birds");
  if (!list) return;

  /* -- sort toggle ---------------------------------------------------- */
  var tools = document.querySelector(".bird-tools");
  if (tools) {
    tools.addEventListener("click", function (e) {
      var btn = e.target.closest(".sort-btn");
      if (!btn || btn.classList.contains("on")) return;
      tools.querySelectorAll(".sort-btn").forEach(function (b) {
        b.classList.remove("on");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("on");
      btn.setAttribute("aria-pressed", "true");
      sortRows(btn.dataset.sort);
    });
    // The server renders the list in alphabetical order, so the default view
    // is already right; nothing is remembered across visits.
  }

  function sortRows(how) {
    var rows = Array.prototype.slice.call(list.querySelectorAll(".bird"));
    rows.sort(function (a, b) {
      if (how === "date") {
        var da = a.dataset.date || "9999-12-31";
        var db = b.dataset.date || "9999-12-31";
        // chronological, ties broken by common name
        return da === db
          ? (a.dataset.slug < b.dataset.slug ? -1 : 1)
          : (da < db ? -1 : 1);
      }
      if (how === "alpha") {
        // common name, case- and punctuation-insensitive, matching the
        // server-rendered order; ties broken by the raw name
        var ka = (a.dataset.name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        var kb = (b.dataset.name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
        if (ka === kb) {
          var na = a.dataset.name || "", nb = b.dataset.name || "";
          return na === nb ? 0 : (na < nb ? -1 : 1);
        }
        return ka < kb ? -1 : 1;
      }
      // taxonomic rank, ties broken by common name
      var ra = Number(a.dataset.rank) || 1e9;
      var rb = Number(b.dataset.rank) || 1e9;
      return ra === rb
        ? (a.dataset.slug < b.dataset.slug ? -1 : 1)
        : (ra - rb);
    });
    rows.forEach(function (r) { list.appendChild(r); });
  }

  /* -- lightbox -------------------------------------------------------- */
  var lb = document.querySelector(".bird-lightbox");
  if (!lb) return;
  var lbImg = lb.querySelector(".lb-img");
  var lbCap = lb.querySelector(".lb-cap");
  var shots = [];   // {src, cap, alt}
  var idx = 0;

  // Collect this species' sighting photos (as rendered in its strip). Each
  // entry's caption is drawn from the thumbnail's alt text, which the server
  // fills with the date and place.
  function gatherShots(body) {
    return Array.prototype.slice.call(body.querySelectorAll(".bird-thumb"))
      .map(function (t) {
        var img = t.querySelector("img");
        var alt = img && img.getAttribute("alt") ? img.getAttribute("alt") : "";
        return { src: t.dataset.src, cap: alt, alt: alt };
      });
  }

  function openAt(i) {
    if (!shots.length) return;
    idx = (i + shots.length) % shots.length;
    lbImg.src = shots[idx].src;
    lbImg.alt = shots[idx].alt || "";
    lbCap.textContent = shots[idx].cap || "";
    lb.hidden = false;
    document.body.classList.add("lb-open");
    lb.querySelector(".lb-close").focus();
  }
  function close() {
    lb.hidden = true;
    document.body.classList.remove("lb-open");
  }
  function step(d) { openAt(idx + d); }

  // Open the lightbox on the given species' photo. `el` is the row head or an
  // expanded body; `src` is the photo to land on (defaults to the first).
  function openSpecies(el, src) {
    var row = el.classList.contains("bird") ? el : el.closest(".bird");
    var body = row && row.querySelector(".bird-body");
    if (!body) return;
    shots = gatherShots(body);
    if (!shots.length) return;
    var i = 0;
    for (var k = 0; k < shots.length; k++) {
      if (shots[k].src === src) { i = k; break; }
    }
    openAt(i);
  }

  /* -- row head: clicking the photo opens the lightbox there; clicking
        anywhere else on the row toggles the expanded strip ------------ */
  list.addEventListener("click", function (e) {
    var head = e.target.closest(".bird-head");
    if (!head || head.disabled) return;

    var photo = e.target.closest(".bird-head-thumb");
    if (photo) {
      // The row photo is a direct lightbox shortcut; keep it from reaching
      // the row toggle below so the row stays collapsed.
      e.stopPropagation();
      openSpecies(head, photo.dataset.src);
      return;
    }

    var body = head.nextElementSibling;
    var open = head.getAttribute("aria-expanded") === "true";
    head.setAttribute("aria-expanded", open ? "false" : "true");
    body.hidden = open;
    head.classList.toggle("open", !open);
  });

  /* -- click a thumbnail in the expanded strip ------------------------- */
  list.addEventListener("click", function (e) {
    var thumb = e.target.closest(".bird-thumb");
    if (!thumb) return;
    openSpecies(thumb.closest(".bird-body"), thumb.dataset.src);
  });

  /* -- lightbox controls ---------------------------------------------- */
  lb.addEventListener("click", function (e) {
    if (e.target === lb || e.target.closest(".lb-close")) { close(); return; }
    if (e.target.closest(".lb-prev")) { step(-1); return; }
    if (e.target.closest(".lb-next")) { step(1); return; }
  });

  /* -- keyboard: Enter on the focused row photo opens the lightbox;
        the open lightbox closes on Escape and steps on the arrows ------- */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      var photo = e.target && e.target.closest
        ? e.target.closest(".bird-head-thumb") : null;
      if (photo) {
        e.preventDefault();
        e.stopPropagation();
        openSpecies(photo.closest(".bird-head"), photo.dataset.src);
        return;
      }
    }
    if (lb.hidden) return;
    if (e.key === "Escape") { close(); }
    else if (e.key === "ArrowLeft") { step(-1); }
    else if (e.key === "ArrowRight") { step(1); }
  });
})();
