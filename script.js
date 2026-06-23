(function () {
  "use strict";

  var DATA = window.PORTFOLIO || { rubrics: [], items: [] };
  var items = DATA.items;
  var rubrics = DATA.rubrics;

  var gridEl = document.getElementById("grid");
  var filtersEl = document.getElementById("filters");
  var countEl = document.getElementById("countWorks");

  var current = "all";
  var visible = []; // items currently shown (for lightbox navigation)

  // ---- helpers ----
  function encode(path) {
    // encode each segment but keep slashes
    return path.split("/").map(encodeURIComponent).join("/");
  }

  function fmtSize(bytes) {
    if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + " МБ";
    return Math.max(1, Math.round(bytes / 1024)) + " КБ";
  }

  var PLAY_SVG =
    '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';

  // Плавное проявление картинки: место уже зарезервировано, поэтому вместо
  // резкого «щелчка» превью мягко появляется, как только декодировано.
  function fadeOnLoad(img) {
    if (img.complete && img.naturalWidth) {
      img.classList.add("is-loaded");
      return;
    }
    function reveal() { img.classList.add("is-loaded"); }
    img.addEventListener("load", reveal);
    img.addEventListener("error", reveal); // не прячем превью при сбое загрузки
  }

  // ---- build рубрикатор ----
  function buildFilters() {
    var frag = document.createDocumentFragment();

    frag.appendChild(makeChip("all", "Все", items.length));

    // group rubrics by their group, with a thin separator between groups
    var lastGroup = null;
    rubrics.forEach(function (r) {
      if (lastGroup !== null && r.group !== lastGroup) {
        var sep = document.createElement("span");
        sep.className = "chip__sep";
        frag.appendChild(sep);
      }
      lastGroup = r.group;
      var count = items.filter(function (i) { return i.rubric === r.key; }).length;
      frag.appendChild(makeChip(r.key, r.label, count));
    });

    filtersEl.appendChild(frag);
  }

  function makeChip(key, label, count) {
    var b = document.createElement("button");
    b.className = "chip" + (key === current ? " is-active" : "");
    b.dataset.key = key;
    b.innerHTML = label + ' <span class="chip__count">' + count + "</span>";
    b.addEventListener("click", function () { setFilter(key); });
    return b;
  }

  function setFilter(key) {
    current = key;
    Array.prototype.forEach.call(filtersEl.children, function (c) {
      if (c.dataset) c.classList.toggle("is-active", c.dataset.key === key);
    });
    render();
  }

  // ---- render grid ----
  function render() {
    visible = current === "all"
      ? items.slice()
      : items.filter(function (i) { return i.rubric === current; });

    gridEl.innerHTML = "";
    if (!visible.length) {
      gridEl.innerHTML = '<p class="empty">Нет работ в этой рубрике.</p>';
      return;
    }

    var frag = document.createDocumentFragment();
    visible.forEach(function (item, idx) {
      frag.appendChild(makeCard(item, idx));
    });
    gridEl.appendChild(frag);
  }

  function makeCard(item, idx) {
    var card = document.createElement("article");
    card.className = "card";
    card.addEventListener("click", function () { openLightbox(idx); });

    var media = document.createElement("div");
    media.className = "card__media";

    // Резервируем место под медиа заранее, чтобы при загрузке карточки
    // не «прыгали»: задаём элементу его пропорцию (CLS = 0).
    if (item.w && item.h) {
      if (item.type === "image") {
        // у картинок — настоящая пропорция
        media.style.aspectRatio = item.w + " / " + item.h;
      } else {
        // у видео постер заполняет карточку через object-fit:cover, поэтому
        // ограничиваем пропорцию, чтобы сверхширокие «ленты» не превращались
        // в тонкие полоски и сетка выглядела опрятно.
        var ratio = Math.min(1.85, Math.max(0.6, item.w / item.h));
        media.style.aspectRatio = ratio.toFixed(4);
      }
    }

    if (item.type === "image") {
      var img = document.createElement("img");
      img.loading = "lazy";
      img.decoding = "async";
      img.alt = item.title;
      img.className = "card__img";
      // width/height-атрибуты дают браузеру пропорцию ещё до загрузки файла —
      // место под картинку резервируется сразу, сетка не пересчитывается.
      if (item.w && item.h) { img.width = item.w; img.height = item.h; }
      fadeOnLoad(img);
      img.src = encode(item.src);
      media.appendChild(img);
    } else {
      // Видео НЕ грузим в сетке — это главный тормоз: ролики без faststart
      // браузер вынужден качать целиком ради первого кадра. Вместо этого
      // показываем лёгкий постер (jpg-кадр), а сам ролик грузится в лайтбоксе.
      media.classList.add("card__media--video");

      if (item.poster) {
        var pimg = document.createElement("img");
        pimg.loading = "lazy";
        pimg.decoding = "async";
        pimg.alt = item.title;
        pimg.className = "card__poster card__img";
        fadeOnLoad(pimg);
        pimg.src = encode(item.poster);
        media.appendChild(pimg);
      }

      var play = document.createElement("div");
      play.className = "card__play";
      play.innerHTML = PLAY_SVG;
      media.appendChild(play);

      var meta = document.createElement("span");
      meta.className = "card__vmeta";
      meta.textContent = item.ext.toUpperCase() + " · " + fmtSize(item.size);
      media.appendChild(meta);
    }

    var badge = document.createElement("span");
    badge.className = "card__badge";
    badge.textContent = item.rubricLabel;
    media.appendChild(badge);

    card.appendChild(media);
    return card;
  }

  // ---- lightbox ----
  var lb = document.getElementById("lightbox");
  var lbStage = document.getElementById("lbStage");
  var lbCaption = document.getElementById("lbCaption");
  var lbIndex = 0;

  function openLightbox(idx) {
    lbIndex = idx;
    showLightbox();
    lb.classList.add("is-open");
    lb.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function showLightbox() {
    var item = visible[lbIndex];
    lbStage.innerHTML = "";
    if (item.type === "image") {
      var img = document.createElement("img");
      img.src = encode(item.src);
      img.alt = item.title;
      lbStage.appendChild(img);
    } else {
      var v = document.createElement("video");
      v.src = encode(item.src);
      v.controls = true;
      v.autoplay = true;
      v.playsInline = true;
      lbStage.appendChild(v);
    }
    lbCaption.textContent =
      item.group + " · " + item.rubricLabel + " — " + item.title +
      "  ·  " + item.ext.toUpperCase() + " · " + fmtSize(item.size);
  }

  function closeLightbox() {
    lb.classList.remove("is-open");
    lb.setAttribute("aria-hidden", "true");
    lbStage.innerHTML = "";
    document.body.style.overflow = "";
  }

  function step(dir) {
    lbIndex = (lbIndex + dir + visible.length) % visible.length;
    showLightbox();
  }

  document.getElementById("lbClose").addEventListener("click", closeLightbox);
  document.getElementById("lbPrev").addEventListener("click", function () { step(-1); });
  document.getElementById("lbNext").addEventListener("click", function () { step(1); });
  lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("is-open")) return;
    if (e.key === "Escape") closeLightbox();
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.key === "ArrowRight") step(1);
  });

  // ---- init ----
  countEl.textContent = items.length;
  buildFilters();
  render();
})();
