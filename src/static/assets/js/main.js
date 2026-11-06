/* ReNEW. — main.js（依存ライブラリなし） */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");

  /* GA4 イベント送信（gtag が無ければ何もしない） */
  function track(name, params) {
    if (typeof window.gtag === "function") window.gtag("event", name, params || {});
  }

  /* ヘッダー：スクロールで背景を付ける */
  var header = document.querySelector("[data-header]");
  function onScroll() {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 40);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* 現在のページのナビに aria-current を付ける */
  var here = location.pathname.replace(/index\.html$/, "");
  document.querySelectorAll(".gnav a").forEach(function (a) {
    var p = a.getAttribute("href");
    if (p !== "/" && here.indexOf(p) === 0) a.setAttribute("aria-current", "page");
  });

  /* SPメニュー（全画面） */
  var burger = document.querySelector("[data-burger]");
  var drawer = document.querySelector("[data-drawer]");
  var spbar = document.querySelector("[data-spbar]");
  function setDrawer(open) {
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "メニューを閉じる" : "メニューを開く");
    header.classList.toggle("is-open", open);
    document.body.classList.toggle("is-locked", open);
    if (spbar) spbar.classList.toggle("is-hidden", open);
    if (open) {
      drawer.hidden = false;
      requestAnimationFrame(function () { drawer.classList.add("is-open"); });
    } else {
      drawer.classList.remove("is-open");
      setTimeout(function () { if (!drawer.classList.contains("is-open")) drawer.hidden = true; }, 300);
    }
  }
  if (burger && drawer) {
    burger.addEventListener("click", function () {
      setDrawer(burger.getAttribute("aria-expanded") !== "true");
    });
    drawer.addEventListener("click", function (e) {
      if (e.target.closest("a")) setDrawer(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && burger.getAttribute("aria-expanded") === "true") {
        setDrawer(false);
        burger.focus();
      }
    });
    window.matchMedia("(min-width: 841px)").addEventListener("change", function (m) {
      if (m.matches) setDrawer(false);
    });
  }

  /* ふわっとフェードイン */
  var targets = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    targets.forEach(function (el) { io.observe(el); });
  } else {
    targets.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* 動画：画面に入ったときだけ読み込み・再生し、外れたら止める（省データ・省電力） */
  var videos = document.querySelectorAll("[data-lazy-video]");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) {
    videos.forEach(function (v) { v.controls = true; });
  } else {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var v = en.target;
        if (en.isIntersecting) {
          var p = v.play();
          if (p && p.catch) p.catch(function () { v.controls = true; });
        } else {
          v.pause();
        }
      });
    }, { threshold: 0.4 });
    videos.forEach(function (v) { vio.observe(v); });
  }

  /* FAQ：開閉をなめらかに（高さ＋フェード）。動きを減らす設定のときは即時 */
  document.querySelectorAll(".rn-faq-item").forEach(function (item) {
    var summary = item.querySelector("summary");
    var panel = item.querySelector(".rn-faq-a");
    if (!summary || !panel || reduce || !panel.animate) return;
    var running = null;
    function run(from, to, done) {
      if (running) running.cancel();
      panel.style.overflow = "hidden";
      running = panel.animate(
        [{ height: from + "px", opacity: from ? 1 : 0 }, { height: to + "px", opacity: to ? 1 : 0 }],
        { duration: 320, easing: "cubic-bezier(.22,.61,.36,1)" }
      );
      running.onfinish = function () {
        running = null;
        panel.style.overflow = "";
        done();
      };
      running.oncancel = function () { panel.style.overflow = ""; };
    }
    summary.addEventListener("click", function (e) {
      e.preventDefault();
      if (item.open && !item.classList.contains("is-closing")) {
        item.classList.add("is-closing");
        run(panel.offsetHeight, 0, function () {
          item.open = false;
          item.classList.remove("is-closing");
        });
      } else if (!item.open) {
        item.open = true;
        run(0, panel.scrollHeight, function () {});
      }
    });
  });

  /* 施工事例の絞り込み */
  document.querySelectorAll(".chips").forEach(function (group) {
    var grid = group.nextElementSibling;
    group.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      var f = btn.getAttribute("data-filter");
      group.querySelectorAll(".chip").forEach(function (c) {
        c.classList.toggle("is-active", c === btn);
        c.setAttribute("aria-pressed", String(c === btn));
      });
      grid.querySelectorAll(".work-card").forEach(function (card) {
        card.hidden = f !== "all" && card.getAttribute("data-cat") !== f;
      });
    });
  });

  /* 計測：LINE・SNSクリック、電話タップ */
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (!a) return;
    var t = a.getAttribute("data-track");
    if (t) track(t, { link_url: a.href });
    if (a.protocol === "tel:") track("tel_tap", { link_url: a.href });
  });

  /* お問い合わせフォーム：入力 → 確認 → 送信 */
  var form = document.querySelector("[data-contact-form]");
  var confirmBox = document.querySelector("[data-confirm]");
  if (form && confirmBox) {
    var list = confirmBox.querySelector("[data-confirm-list]");
    form.addEventListener("submit", function (e) {
      if (form.dataset.confirmed === "1") {
        track("form_submit", { form: "contact" });
        return;
      }
      e.preventDefault();
      if (!form.reportValidity()) return;
      list.innerHTML = "";
      form.querySelectorAll("[data-label]").forEach(function (field) {
        var value = field.tagName === "SELECT" ? field.options[field.selectedIndex].text : field.value.trim();
        var row = document.createElement("div");
        var dt = document.createElement("dt");
        var dd = document.createElement("dd");
        dt.textContent = field.getAttribute("data-label");
        dd.textContent = value || "（未入力）";
        row.appendChild(dt);
        row.appendChild(dd);
        list.appendChild(row);
      });
      form.hidden = true;
      confirmBox.hidden = false;
      confirmBox.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    confirmBox.querySelector("[data-back]").addEventListener("click", function () {
      confirmBox.hidden = true;
      form.hidden = false;
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    confirmBox.querySelector("[data-send]").addEventListener("click", function () {
      this.disabled = true;
      this.textContent = "送信中…";
      form.dataset.confirmed = "1";
      form.requestSubmit ? form.requestSubmit() : form.submit();
    });
  }
})();
