/*
 * Bird gallery: progressive enhancement. Without scripting the grid still
 * renders; opening a photo in the lightbox, prev/next, and Escape are
 * additive. No dependencies, no build step.
 */
(function () {
  "use strict";

  var grid = document.querySelector(".gallery-grid");
  if (!grid) return;
  var items = Array.prototype.slice.call(grid.querySelectorAll(".gal-item"));
  var lb = document.querySelector(".gallery-lightbox");
  if (!lb) return;

  var lbImg = lb.querySelector(".lb-img");
  var lbCap = lb.querySelector(".lb-cap");
  var idx = 0;

  function openAt(i) {
    if (!items.length) return;
    idx = (i + items.length) % items.length;
    var d = items[idx].dataset;
    lbImg.src = d.src;
    lbImg.alt = d.cap || "";
    lbCap.textContent = d.cap || "";
    lb.hidden = false;
    document.body.classList.add("lb-open");
    lb.querySelector(".lb-close").focus();
  }
  function close() {
    lb.hidden = true;
    document.body.classList.remove("lb-open");
  }
  function step(d) { openAt(idx + d); }

  grid.addEventListener("click", function (e) {
    var item = e.target.closest(".gal-item");
    if (!item) return;
    openAt(items.indexOf(item));
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
