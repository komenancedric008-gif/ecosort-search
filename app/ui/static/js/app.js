/**
 * EcoSort — script client
 * Machine à vues (single page) : accueil → recherche → résultats Jumia
 * → analyse IA → résultat plein écran coloré selon la poubelle.
 */
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  /* ---------------- Accueil : carousel photo de fond ---------------- */
  const heroCarousel = document.getElementById("hero-carousel");
  if (heroCarousel) {
    const slides = heroCarousel.querySelectorAll(".home-hero-bg");
    if (slides.length > 1) {
      let slideIndex = 0;
      setInterval(() => {
        slides[slideIndex].classList.remove("is-active");
        slideIndex = (slideIndex + 1) % slides.length;
        slides[slideIndex].classList.add("is-active");
      }, 5000);
    }
  }

  /* ---------------- Fluidité : apparition au défilement ---------------- */
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if ("IntersectionObserver" in window) {
      const revealObserver = new IntersectionObserver(
        (entries, obs) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("is-visible");
              obs.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach((el) => revealObserver.observe(el));
    } else {
      revealEls.forEach((el) => el.classList.add("is-visible"));
    }
  }

  /* ---------------- Navbar : effet au scroll ---------------- */
  const siteNav = document.getElementById("site-nav");
  if (siteNav) {
    const onScroll = () => siteNav.classList.toggle("is-scrolled", window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------- Menu mobile (drawer) ---------------- */
  const navBurger = document.getElementById("nav-burger");
  const navDrawer = document.getElementById("nav-drawer");
  const navBackdrop = document.getElementById("nav-drawer-backdrop");

  function openDrawer() {
    navDrawer.hidden = false;
    navBackdrop.hidden = false;
    requestAnimationFrame(() => {
      navDrawer.classList.add("is-open");
      navBackdrop.classList.add("is-open");
    });
    navBurger.setAttribute("aria-expanded", "true");
  }
  function closeDrawer() {
    navDrawer.classList.remove("is-open");
    navBackdrop.classList.remove("is-open");
    navBurger.setAttribute("aria-expanded", "false");
    setTimeout(() => { navDrawer.hidden = true; navBackdrop.hidden = true; }, 350);
  }
  if (navBurger) {
    navBurger.addEventListener("click", () => {
      navDrawer.classList.contains("is-open") ? closeDrawer() : openDrawer();
    });
    navBackdrop.addEventListener("click", closeDrawer);
    navDrawer.querySelectorAll("a").forEach((a) => a.addEventListener("click", closeDrawer));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && navDrawer.classList.contains("is-open")) closeDrawer();
    });
  }

  /* ---------------- Thème sombre / clair ---------------- */
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    const iconMoon = themeToggle.querySelector(".icon-moon");
    const iconSun = themeToggle.querySelector(".icon-sun");

    function reflectTheme(theme) {
      iconMoon.hidden = theme === "dark";
      iconSun.hidden = theme !== "dark";
    }
    reflectTheme(document.documentElement.getAttribute("data-theme") || "light");

    themeToggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("ecosort-theme", next);
      reflectTheme(next);
    });
  }

  /* ---------------- Statistiques : compteurs + barres animés ---------------- */
  const kpiValues = document.querySelectorAll(".kpi-value[data-count]");
  const breakdownBars = document.querySelectorAll(".breakdown-bar[data-percent]");
  if (kpiValues.length || breakdownBars.length) {
    const animateCounters = () => {
      kpiValues.forEach((el) => {
        const target = parseFloat(el.getAttribute("data-count"));
        const decimals = parseInt(el.getAttribute("data-decimals") || "0", 10);
        const duration = 1100;
        const start = performance.now();
        function tick(now) {
          const progress = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          const value = target * eased;
          el.textContent = decimals
            ? value.toFixed(decimals).replace(".", ",")
            : Math.round(value).toLocaleString("fr-FR");
          if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });
      breakdownBars.forEach((bar) => {
        requestAnimationFrame(() => { bar.style.width = `${bar.getAttribute("data-percent")}%`; });
      });
    };

    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) { animateCounters(); obs.disconnect(); }
        });
      }, { threshold: 0.3 });
      const target = document.querySelector(".kpi-grid, .breakdown-card");
      if (target) observer.observe(target);
    } else {
      animateCounters();
    }
  }

  /* ---------------- Parcours produit (page d'accueil uniquement) ---------------- */
  if (!document.getElementById("app")) return;

  /* ---------------- Machine à vues ---------------- */
  function activate(name) {
    const current = document.querySelector(".view.is-active");
    const next = document.querySelector(`.view[data-view="${name}"]`);
    if (!next || current === next) return;

    if (current) {
      current.classList.add("is-leaving");
      setTimeout(() => current.classList.remove("is-active", "is-leaving"), 280);
    }
    requestAnimationFrame(() => {
      next.classList.add("is-active");
      if (window.lucide) lucide.createIcons();
    });
  }

  /* ---------------- Accueil : puces rapides ---------------- */
  const searchInput = document.getElementById("search-input");
  const searchForm = document.getElementById("search-form");

  document.querySelectorAll(".quick-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      searchInput.value = chip.getAttribute("data-fill");
      searchForm.requestSubmit();
    });
  });

  /* ---------------- Recherche ---------------- */
  const searchSubmit = document.getElementById("search-submit");
  const progressBar = document.getElementById("search-progress");
  const searchingLabel = document.getElementById("searching-label");

  function toggleSubmitLoading(isLoading) {
    searchSubmit.disabled = isLoading;
    searchSubmit.querySelector(".btn-icon-idle").hidden = isLoading;
    searchSubmit.querySelector(".btn-icon-loading").hidden = !isLoading;
    searchSubmit.querySelector(".btn-label").textContent = isLoading ? "Recherche…" : "Rechercher";
  }

  function animateProgress(el, to, duration) {
    el.style.transition = "none";
    el.style.width = "0%";
    requestAnimationFrame(() => {
      el.style.transition = `width ${duration}ms cubic-bezier(.22,.68,0,1)`;
      el.style.width = `${to}%`;
    });
  }

  searchForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const keyword = searchInput.value.trim();
    if (keyword.length < 2) return;

    toggleSubmitLoading(true);
    activate("searching");
    searchingLabel.textContent = `Recherche « ${keyword} » sur Jumia…`;
    animateProgress(progressBar, 88, 900);

    const start = Date.now();
    let data;
    try {
      const res = await fetch("/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keyword }),
      });
      data = await res.json();
    } catch (err) {
      console.error("Erreur /search :", err);
      data = { produits: [], error: "Une erreur est survenue. Réessayez." };
    }

    const elapsed = Date.now() - start;
    if (elapsed < 700) await sleep(700 - elapsed);
    progressBar.style.transition = "width .25s var(--ease)";
    progressBar.style.width = "100%";
    await sleep(220);

    renderResults(keyword, data);
    activate("results");
    toggleSubmitLoading(false);
  });

  /* ---------------- Résultats Jumia ---------------- */
  const resultsKeyword = document.getElementById("results-keyword");
  const demoBanner = document.getElementById("demo-banner");
  const emptyState = document.getElementById("empty-state");
  const emptyStateText = document.getElementById("empty-state-text");
  const productGrid = document.getElementById("product-grid");
  const cardTemplate = document.getElementById("product-card-template");

  document.getElementById("back-to-home").addEventListener("click", () => activate("home"));

  function renderResults(keyword, data) {
    resultsKeyword.textContent = `« ${keyword} »`;
    productGrid.innerHTML = "";

    const produits = data.produits || [];
    demoBanner.hidden = !(produits.length && produits[0].source === "demo");
    emptyState.hidden = produits.length > 0;
    if (produits.length === 0) {
      emptyStateText.textContent = data.error || `Aucun résultat pour « ${keyword} ». Essayez un autre mot-clé.`;
    }

    produits.forEach((produit, index) => {
      const node = cardTemplate.content.firstElementChild.cloneNode(true);
      node.style.animationDelay = `${index * 70}ms`;
      const img = node.querySelector("img");
      img.src = produit.image;
      img.alt = produit.name;
      node.querySelector(".product-name").textContent = produit.name;
      node.querySelector(".product-price").textContent = produit.price;
      node.querySelector(".choose-btn").addEventListener("click", (e) => chooseProduct(produit, e.currentTarget));
      productGrid.appendChild(node);
    });

    if (window.lucide) lucide.createIcons();
  }

  /* ---------------- Analyse IA ---------------- */
  const analyzingLabel = document.getElementById("analyzing-label");
  const stepDots = document.querySelectorAll(".step-dot");
  const ANALYSIS_STEPS = ["Identification…", "Recherche du matériau…", "Classification…"];
  const ANALYSIS_MIN_DURATION = 2000;

  function setAnalysisStep(index) {
    analyzingLabel.textContent = ANALYSIS_STEPS[index];
    stepDots.forEach((dot, i) => {
      dot.classList.toggle("is-active", i === index);
      dot.classList.toggle("is-done", i < index);
    });
  }

  const FALLBACK_CATEGORY = {
    bin: "MARRON/NOIRE", color: "#8B5E3C", text_on: "light", label: "Poubelle marron / noire",
    icon: "trash-2", matiere: "indéterminé", recyclable: false,
    conseil: "Impossible d'analyser ce produit pour le moment. Réessayez plus tard.",
  };

  async function chooseProduct(produit, btn) {
    btn.classList.add("is-loading");
    activate("analyzing");

    let stepIndex = 0;
    setAnalysisStep(stepIndex);
    const stepTimer = setInterval(() => {
      stepIndex = Math.min(stepIndex + 1, ANALYSIS_STEPS.length - 1);
      setAnalysisStep(stepIndex);
    }, ANALYSIS_MIN_DURATION / ANALYSIS_STEPS.length);

    const start = Date.now();
    let category;
    try {
      const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: produit.image, product_name: produit.name }),
      });
      if (!res.ok) throw new Error("Réponse serveur invalide");
      category = await res.json();
    } catch (err) {
      console.error("Erreur /predict :", err);
      category = FALLBACK_CATEGORY;
    }

    const elapsed = Date.now() - start;
    if (elapsed < ANALYSIS_MIN_DURATION) await sleep(ANALYSIS_MIN_DURATION - elapsed);
    clearInterval(stepTimer);

    btn.classList.remove("is-loading");
    showResult(category);
  }

  /* ---------------- Résultat plein écran ---------------- */
  const resultView = document.getElementById("result-view");
  const resultIconWrap = document.getElementById("result-icon-wrap");
  const resultBadge = document.getElementById("result-badge");
  const resultTitle = document.getElementById("result-title");
  const resultDetail = document.getElementById("result-detail");
  const adviceText = document.getElementById("advice-text");

  function showResult(category) {
    resultView.style.setProperty("--result-color", category.color || "#22C55E");
    resultView.dataset.text = category.text_on || "light";

    resultIconWrap.innerHTML = `<i data-lucide="${category.icon || "recycle"}"></i>`;
    resultTitle.textContent = category.label || category.bin || "Résultat";
    resultDetail.textContent = `Matériau détecté : ${category.matiere || "indéterminé"}.`;
    adviceText.textContent = category.conseil || "Vérifiez la consigne de tri locale.";
    resultBadge.innerHTML = category.recyclable
      ? `<i data-lucide="check-circle-2"></i> Recyclable`
      : `<i data-lucide="alert-circle"></i> Non recyclable`;

    activate("result");
  }

  function resetToHome() {
    activate("home");
    searchInput.value = "";
    setTimeout(() => searchInput.focus(), 300);
  }

  document.getElementById("result-close").addEventListener("click", resetToHome);
  document.getElementById("result-restart").addEventListener("click", resetToHome);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && resultView.classList.contains("is-active")) resetToHome();
  });
});
