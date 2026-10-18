/*
 * Birds page: progressive enhancement only. With scripting off the list still
 * renders in taxonomic order; toggling the sort, expanding a row, and the
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
    // keep the sort selection through a page reload
    var saved = sessionStorage.getItem("bird-sort") === "date" ? "date" : "taxon";
    var active = tools.querySelector('[data-sort="' + saved + '"]');
    if (active) {
      tools.querySelectorAll(".sort-btn").forEach(function (b) {
        b.classList.remove("on");
        b.setAttribute("aria-pressed", "false");
      });
      active.classList.add("on");
      active.setAttribute("aria-pressed", "true");
      sortRows(saved);
    }
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
      // taxonomic rank, ties broken by common name
      var ra = Number(a.dataset.rank) || 1e9;
      var rb = Number(b.dataset.rank) || 1e9;
      return ra === rb
        ? (a.dataset.slug < b.dataset.slug ? -1 : 1)
        : (ra - rb);
    });
    rows.forEach(function (r) { list.appendChild(r); });
    sessionStorage.setItem("bird-sort", how);
  }

  /* -- expand a row to reveal its thumbnails --------------------------- */
  list.addEventListener("click", function (e) {
    var head = e.target.closest(".bird-head");
    if (!head || head.disabled) return;
    var body = head.nextElementSibling;
    var open = head.getAttribute("aria-expanded") === "true";
    head.setAttribute("aria-expanded", open ? "false" : "true");
    body.hidden = open;
    head.classList.toggle("open", !open);
  });

  /* -- lightbox -------------------------------------------------------- */
  var lb = document.querySelector(".bird-lightbox");
  if (!lb) return;
  var lbImg = lb.querySelector(".lb-img");
  var lbCap = lb.querySelector(".lb-cap");
  var shots = [];   // {src, date, alt}
  var idx = 0;

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

  list.addEventListener("click", function (e) {
    var thumb = e.target.closest(".bird-thumb");
    if (!thumb) return;
    // gather this species' shots from its expanded body
    var body = thumb.closest(".bird-body");
    shots = Array.prototype.slice.call(body.querySelectorAll(".bird-thumb"))
      .map(function (t) {
        var img = t.querySelector("img");
        return {
          src: t.dataset.src,
          cap: img && img.getAttribute("alt") ? img.getAttribute("alt") : "",
          alt: img && img.getAttribute("alt") ? img.getAttribute("alt") : ""
        };
      });
    var thisIdx = Array.prototype.indexOf.call(
      body.querySelectorAll(".bird-thumb"), thumb);
    openAt(thisIdx);
  });

  lb.addEventListener("click", function (e) {
    if (e.target === lb || e.target.closest(".lb-close")) { close(); return; }
    if (e.target.closest(".lb-prev")) { step(-1); return; }
    if (e.target.closest(".lb-next")) { step(1); return; }
  });
  document.addEventListener("keydown", function (e) {
    if (lb.hidden) return;
    if (e.key === "Escape") { close(); }
    else if (e.key === "ArrowLeft") { step(-1); }
    else if (e.key === "ArrowRight") { step(1); }
  });
})();
