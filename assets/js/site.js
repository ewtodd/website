/*
 * Progressive enhancement only. Every behaviour here is additive: with
 * scripting off the page renders complete and static, which is why the reveal
 * class is applied by CSS but cleared by JS rather than the other way round.
 *
 * No dependencies and no build step — this ships as one small file alongside
 * the stylesheet.
 */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* -- reveal on first view ------------------------------------------- */
  function reveal() {
    var targets = document.querySelectorAll(".reveal");
    if (!targets.length) return;
    if (reduced || !("IntersectionObserver" in window)) {
      targets.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        // Staggered within a group, so a row of cards arrives as a sequence.
        var delay = Number(e.target.dataset.revealDelay || 0);
        setTimeout(function () { e.target.classList.add("in"); }, delay);
        io.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    targets.forEach(function (el) { io.observe(el); });

    // Backstop: content must never stay invisible because an observer did not
    // fire — inside a print or screenshot pass, for instance.
    setTimeout(function () {
      targets.forEach(function (el) { el.classList.add("in"); });
    }, 2500);
  }

  /* -- copy buttons on code blocks ------------------------------------ */
  function copyButtons() {
    if (!navigator.clipboard) return;
    document.querySelectorAll("pre > code").forEach(function (code) {
      var pre = code.parentNode;
      if (!pre.parentNode || pre.parentNode.classList.contains("codewrap")) return;
      var wrap = document.createElement("div");
      wrap.className = "codewrap";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy";
      btn.textContent = "copy";
      btn.setAttribute("aria-label", "Copy code to clipboard");
      btn.addEventListener("click", function () {
        navigator.clipboard.writeText(code.innerText).then(function () {
          btn.textContent = "copied";
          btn.classList.add("done");
          setTimeout(function () {
            btn.textContent = "copy";
            btn.classList.remove("done");
          }, 1600);
        });
      });
      wrap.appendChild(btn);
    });
  }

  /* -- reading progress in the nav hairline --------------------------- */
  function progress() {
    var bar = document.querySelector(".nav .progress");
    if (!bar) return;
    var ticking = false;
    function update() {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
      bar.style.width = pct.toFixed(2) + "%";
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /* -- CV contents rail: highlight the section in view ----------------- */
  function scrollspy() {
    var links = document.querySelectorAll(".cv-toc a[href^='#']");
    if (!links.length || !("IntersectionObserver" in window)) return;
    var byId = {};
    var sections = [];
    links.forEach(function (a) {
      var el = document.getElementById(a.getAttribute("href").slice(1));
      if (!el) return;
      byId[el.id] = a;
      sections.push(el);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { a.classList.remove("on"); });
        if (byId[e.target.id]) byId[e.target.id].classList.add("on");
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    sections.forEach(function (s) { io.observe(s); });
  }

  /* -- hero terminal: lines arrive in sequence ------------------------- */
  function terminal() {
    var term = document.querySelector("[data-term-animate]");
    if (!term) return;
    var lines = Array.prototype.slice.call(term.querySelectorAll(".ln"));
    if (!lines.length || reduced || !("IntersectionObserver" in window)) return;

    lines.forEach(function (l) { l.style.opacity = "0"; });
    var io = new IntersectionObserver(function (entries, obs) {
      if (!entries[0].isIntersecting) return;
      obs.disconnect();
      lines.forEach(function (l, i) {
        setTimeout(function () {
          l.style.transition = "opacity .22s ease-out";
          l.style.opacity = "1";
        }, 180 + i * 170);
      });
    }, { threshold: 0.3 });
    io.observe(term);
  }

  function init() {
    reveal();
    copyButtons();
    progress();
    scrollspy();
    terminal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
