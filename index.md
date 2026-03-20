---
layout: home
author_profile: true
title: "CYBERLOG"
classes: wide
---

> 밤에 만든 것들을 기록하는 개발 블로그.

<style>
  #category-inline-panel {
    margin-top: 1rem;
    border: 1px solid rgba(35, 240, 255, 0.18);
    background: var(--panel);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow-cyan);
    overflow: hidden;
  }

  #category-inline-panel.is-hidden {
    display: none;
  }

  #category-inline-panel .category-inline-title {
    font-weight: 900;
    letter-spacing: 0.02em;
    margin: 0 0 0.65rem;
  }

  #category-inline-panel ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  #category-inline-panel li {
    padding: 0.65rem 0;
    border-top: 1px solid rgba(35, 240, 255, 0.10);
  }

  #category-inline-panel li:first-child {
    border-top: 0;
  }

  #category-inline-panel a {
    color: var(--cyan);
    text-decoration: none;
  }

  #category-inline-panel a:hover {
    text-decoration: underline;
    text-shadow: 0 0 10px rgba(35, 240, 255, 0.35);
  }

  #category-inline-panel .meta {
    margin-top: 0.25rem;
    color: var(--muted);
    font-size: 0.92rem;
  }
</style>

<script>
  (function () {
    function normalizeSlug(s) {
      if (!s) return "";
      return String(s)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9가-힣\-_]/g, "");
    }

    function extractSlugFromHref(href) {
      if (!href) return "";
      try {
        const u = new URL(href, window.location.origin);
        const parts = u.pathname.split("/").filter(Boolean);
        return normalizeSlug(decodeURIComponent(parts[parts.length - 1] || ""));
      } catch (e) {
        const hash = href.split("#")[1];
        return normalizeSlug(hash || href);
      }
    }

    const POSTS = [
      {% for post in site.posts %}
        {
          url: {{ post.url | relative_url | jsonify }},
          title: {{ post.title | jsonify }},
          date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
          categories: [
            {% for c in post.categories %}
              {{ c | slugify | jsonify }}{% unless forloop.last %}, {% endunless %}
            {% endfor %}
          ]
        }{% unless forloop.last %},{% endunless %}
      {% endfor %}
    ];

    const POSTS_BY_CATEGORY = {};
    const ALL = POSTS.slice().sort((a, b) => new Date(b.date) - new Date(a.date));

    POSTS.forEach((p) => {
      (p.categories || []).forEach((slug) => {
        if (!POSTS_BY_CATEGORY[slug]) POSTS_BY_CATEGORY[slug] = [];
        POSTS_BY_CATEGORY[slug].push(p);
      });
    });

    Object.keys(POSTS_BY_CATEGORY).forEach((k) => {
      POSTS_BY_CATEGORY[k].sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    function getRecentContainer() {
      const headings = Array.from(
        document.querySelectorAll(".page__content h1, .page__content h2, .page__content h3")
      );
      const recentHeading = headings.find((h) => {
        const t = (h.textContent || "").trim();
        return t === "Recent Posts" || t.includes("Recent Posts") || t.includes("최근글");
      });
      if (!recentHeading) return null;
      return recentHeading.closest("section") || recentHeading.closest("div") || recentHeading.parentElement;
    }

    function ensurePanelMounted() {
      let panel = document.getElementById("category-inline-panel");
      if (panel) return panel;

      panel = document.createElement("div");
      panel.id = "category-inline-panel";
      panel.className = "is-hidden";
      panel.innerHTML = `
        <div class="category-inline-title">Recent Posts</div>
        <ul></ul>
      `;

      const recentContainer = getRecentContainer();
      if (recentContainer && recentContainer.parentElement) {
        // 최근글 섹션 자리에 자연스럽게 들어가 보이도록
        recentContainer.parentElement.insertBefore(panel, recentContainer);
      } else {
        const target = document.querySelector(".page__content") || document.body;
        target.appendChild(panel);
      }

      return panel;
    }

    function hideRecentContainer() {
      const recentContainer = getRecentContainer();
      if (recentContainer) recentContainer.style.display = "none";
    }

    function renderPanel(categorySlug, labelText) {
      const panel = document.getElementById("category-inline-panel");
      if (!panel) return;

      const title = panel.querySelector(".category-inline-title");
      const list = panel.querySelector("ul");
      if (!title || !list) return;

      const posts = categorySlug === "all" ? ALL : (POSTS_BY_CATEGORY[categorySlug] || []);
      title.textContent = categorySlug === "all" ? "Recent Posts" : (labelText || categorySlug);

      list.innerHTML = "";
      posts.slice(0, 10).forEach((p) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = p.url;
        a.textContent = p.title;

        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = p.date;

        li.appendChild(a);
        li.appendChild(meta);
        list.appendChild(li);
      });

      panel.classList.remove("is-hidden");
      hideRecentContainer();
    }

    document.addEventListener("DOMContentLoaded", function () {
      ensurePanelMounted();
      renderPanel("all");

      const taxonomyLinks = Array.from(document.querySelectorAll(".taxonomy__index a"));
      taxonomyLinks.forEach((a) => {
        a.addEventListener("click", function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

          const href = a.getAttribute("href") || "";
          const slugFromHref = extractSlugFromHref(href);
          const slugFromText = normalizeSlug(a.textContent || "");

          const slug =
            slugFromHref && (POSTS_BY_CATEGORY[slugFromHref] || slugFromHref === "all")
              ? slugFromHref
              : slugFromText;

          if (!slug) return;
          e.preventDefault();
          renderPanel(slug, (a.textContent || "").trim());
        });
      });
    });
  })();
</script>

---
layout: home
author_profile: true
title: "CYBERLOG"
classes: wide
---

> 밤에 만든 것들을 기록하는 개발 블로그.

<style>
  #category-inline-panel {
    margin-top: 1rem;
    border: 1px solid rgba(35, 240, 255, 0.18);
    background: var(--panel);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow-cyan);
    overflow: hidden;
  }

  #category-inline-panel.is-hidden {
    display: none;
  }

  #category-inline-panel .category-inline-title {
    font-weight: 900;
    letter-spacing: 0.02em;
    margin: 0 0 0.65rem;
  }

  #category-inline-panel ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  #category-inline-panel li {
    padding: 0.65rem 0;
    border-top: 1px solid rgba(35, 240, 255, 0.10);
  }

  #category-inline-panel li:first-child {
    border-top: 0;
  }

  #category-inline-panel a {
    color: var(--cyan);
    text-decoration: none;
  }

  #category-inline-panel a:hover {
    text-decoration: underline;
    text-shadow: 0 0 10px rgba(35, 240, 255, 0.35);
  }

  #category-inline-panel .meta {
    margin-top: 0.25rem;
    color: var(--muted);
    font-size: 0.92rem;
  }
</style>

<script>
  (function () {
    function normalizeSlug(s) {
      if (!s) return "";
      return String(s)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9가-힣\-_]/g, "");
    }

    function extractSlugFromHref(href) {
      if (!href) return "";
      try {
        const u = new URL(href, window.location.origin);
        const parts = u.pathname.split("/").filter(Boolean);
        return normalizeSlug(decodeURIComponent(parts[parts.length - 1] || ""));
      } catch (e) {
        const hash = href.split("#")[1];
        return normalizeSlug(hash || href);
      }
    }

    const POSTS = [
      {% for post in site.posts %}
        {
          url: {{ post.url | relative_url | jsonify }},
          title: {{ post.title | jsonify }},
          date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
          categories: [
            {% for c in post.categories %}
              {{ c | slugify | jsonify }}{% unless forloop.last %}, {% endunless %}
            {% endfor %}
          ]
        }{% unless forloop.last %},{% endunless %}
      {% endfor %}
    ];

    const POSTS_BY_CATEGORY = {};
    const ALL = POSTS.slice().sort((a, b) => new Date(b.date) - new Date(a.date));

    POSTS.forEach((p) => {
      (p.categories || []).forEach((slug) => {
        if (!POSTS_BY_CATEGORY[slug]) POSTS_BY_CATEGORY[slug] = [];
        POSTS_BY_CATEGORY[slug].push(p);
      });
    });

    Object.keys(POSTS_BY_CATEGORY).forEach((k) => {
      POSTS_BY_CATEGORY[k].sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    function getRecentContainer() {
      const headings = Array.from(
        document.querySelectorAll(".page__content h1, .page__content h2, .page__content h3")
      );
      const recentHeading = headings.find((h) => {
        const t = (h.textContent || "").trim();
        return t === "Recent Posts" || t.includes("Recent Posts") || t.includes("최근글");
      });
      if (!recentHeading) return null;
      return recentHeading.closest("section") || recentHeading.closest("div") || recentHeading.parentElement;
    }

    function ensurePanelMounted() {
      let panel = document.getElementById("category-inline-panel");
      if (panel) return panel;

      panel = document.createElement("div");
      panel.id = "category-inline-panel";
      panel.className = "is-hidden";
      panel.innerHTML = `
        <div class="category-inline-title">Recent Posts</div>
        <ul></ul>
      `;

      const recentContainer = getRecentContainer();
      if (recentContainer && recentContainer.parentElement) {
        recentContainer.parentElement.insertBefore(panel, recentContainer.nextSibling);
      } else {
        const target = document.querySelector(".page__content") || document.body;
        target.appendChild(panel);
      }

      return panel;
    }

    function hideRecentContainer() {
      const recentContainer = getRecentContainer();
      if (recentContainer) recentContainer.style.display = "none";
    }

    function renderPanel(categorySlug, labelText) {
      const panel = document.getElementById("category-inline-panel");
      if (!panel) return;

      const title = panel.querySelector(".category-inline-title");
      const list = panel.querySelector("ul");
      if (!title || !list) return;

      const posts = categorySlug === "all" ? ALL : (POSTS_BY_CATEGORY[categorySlug] || []);

      title.textContent = categorySlug === "all" ? "Recent Posts" : (labelText || categorySlug);

      list.innerHTML = "";
      posts.slice(0, 10).forEach((p) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = p.url;
        a.textContent = p.title;

        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = p.date;

        li.appendChild(a);
        li.appendChild(meta);
        list.appendChild(li);
      });

      panel.classList.remove("is-hidden");
      hideRecentContainer();
    }

    document.addEventListener("DOMContentLoaded", function () {
      ensurePanelMounted();
      renderPanel("all");

      // 사이드바 카테고리(기존 버튼)를 클릭하면 목록만 바꿈
      const taxonomyLinks = Array.from(document.querySelectorAll(".taxonomy__index a"));
      taxonomyLinks.forEach((a) => {
        a.addEventListener("click", function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

          const href = a.getAttribute("href") || "";
          const slugFromHref = extractSlugFromHref(href);
          const slugFromText = normalizeSlug(a.textContent || "");

          const slug =
            slugFromHref && (POSTS_BY_CATEGORY[slugFromHref] || slugFromHref === "all")
              ? slugFromHref
              : slugFromText;

          if (!slug) return;
          e.preventDefault();
          renderPanel(slug, a.textContent.trim());
        });
      });
    });
  })();
</script>

---
layout: home
author_profile: true
title: "CYBERLOG"
classes: wide
---

> 밤에 만든 것들을 기록하는 개발 블로그.

<style>
  /* Sidebar category 클릭 시, 오른쪽에 표시될 리스트 패널 */
  #category-inline-panel {
    margin-top: 1rem;
    border: 1px solid rgba(35, 240, 255, 0.18);
    background: var(--panel);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow-cyan);
    overflow: hidden;
  }

  #category-inline-panel.is-hidden {
    display: none;
  }

  #category-inline-panel .category-inline-title {
    font-weight: 900;
    letter-spacing: 0.02em;
    margin: 0 0 0.65rem;
  }

  #category-inline-panel ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  #category-inline-panel li {
    padding: 0.65rem 0;
    border-top: 1px solid rgba(35, 240, 255, 0.10);
  }

  #category-inline-panel li:first-child {
    border-top: 0;
  }

  #category-inline-panel a {
    color: var(--cyan);
    text-decoration: none;
  }

  #category-inline-panel a:hover {
    text-decoration: underline;
    text-shadow: 0 0 10px rgba(35, 240, 255, 0.35);
  }

  #category-inline-panel .meta {
    margin-top: 0.25rem;
    color: var(--muted);
    font-size: 0.92rem;
  }

  /* 기본 “Recent Posts” 섹션을 우리 패널로 대체 */
  .category-inline-hidden-recent {
    display: none !important;
  }
</style>

<script>
  (function () {
    function normalizeSlug(s) {
      if (!s) return "";
      return String(s)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9가-힣\-_]/g, "");
    }

    function extractSlugFromHref(href) {
      if (!href) return "";
      try {
        const u = new URL(href, window.location.origin);
        const parts = u.pathname.split("/").filter(Boolean);
        const last = parts[parts.length - 1] || "";
        return normalizeSlug(decodeURIComponent(last));
      } catch (e) {
        const hash = href.split("#")[1];
        return normalizeSlug(hash || href);
      }
    }

    const POSTS = [
      {% for post in site.posts %}
        {
          url: {{ post.url | relative_url | jsonify }},
          title: {{ post.title | jsonify }},
          date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
          categories: [
            {% for c in post.categories %}
              {{ c | slugify | jsonify }}{% unless forloop.last %}, {% endunless %}
            {% endfor %}
          ]
        }{% unless forloop.last %},{% endunless %}
      {% endfor %}
    ];

    const POSTS_BY_CATEGORY = {};
    const ALL = POSTS.slice().sort((a, b) => new Date(b.date) - new Date(a.date));

    POSTS.forEach((p) => {
      (p.categories || []).forEach((slug) => {
        if (!POSTS_BY_CATEGORY[slug]) POSTS_BY_CATEGORY[slug] = [];
        POSTS_BY_CATEGORY[slug].push(p);
      });
    });
    Object.keys(POSTS_BY_CATEGORY).forEach((k) => {
      POSTS_BY_CATEGORY[k].sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    function hideDefaultRecentPosts() {
      const recentlyHeadings = Array.from(
        document.querySelectorAll(
          ".page__content h1, .page__content h2, .page__content h3"
        )
      );

      recentlyHeadings.forEach((h) => {
        const t = (h.textContent || "").trim().toLowerCase();
        const isRecent =
          t === "recent posts" ||
          t.includes("recent posts") ||
          t.includes("최근글") ||
          (t.includes("recent") && t.includes("post"));

        if (!isRecent) return;

        const container = h.closest("section") || h.closest("div") || h.parentElement;
        if (container) container.classList.add("category-inline-hidden-recent");
      });
    }

    function ensurePanelMounted() {
      let panel = document.getElementById("category-inline-panel");
      if (panel) return panel;

      panel = document.createElement("div");
      panel.id = "category-inline-panel";
      panel.className = "is-hidden";

      panel.innerHTML = `
        <div class="category-inline-title">Recent Posts</div>
        <ul></ul>
      `;

      // 홈 메인 영역에 삽입 (Minimal Mistakes의 중앙 컬럼)
      const target =
        document.querySelector(".page__content .initial-content") ||
        document.querySelector(".page__content") ||
        document.querySelector("main") ||
        document.body;

      target.appendChild(panel);
      return panel;
    }

    function renderPanel(categorySlug, label) {
      const panel = document.getElementById("category-inline-panel");
      if (!panel) return;

      const title = panel.querySelector(".category-inline-title");
      const list = panel.querySelector("ul");
      if (!title || !list) return;

      const posts = categorySlug === "all" ? ALL : (POSTS_BY_CATEGORY[categorySlug] || []);

      title.textContent = categorySlug === "all" ? "Recent Posts" : ("Category: " + (label || categorySlug));

      list.innerHTML = "";
      posts.slice(0, 10).forEach((p) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = p.url;
        a.textContent = p.title;

        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = p.date;

        li.appendChild(a);
        li.appendChild(meta);
        list.appendChild(li);
      });

      panel.classList.remove("is-hidden");
      hideDefaultRecentPosts();
    }

    document.addEventListener("DOMContentLoaded", function () {
      ensurePanelMounted();
      renderPanel("all");

      // 사이드바 카테고리(기존 버튼)를 클릭하면 목록만 바꿈
      const taxonomyLinks = Array.from(document.querySelectorAll(".taxonomy__index a"));
      taxonomyLinks.forEach((a) => {
        a.addEventListener("click", function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

          const href = a.getAttribute("href") || "";
          const slugFromHref = extractSlugFromHref(href);
          const slugFromText = normalizeSlug((a.textContent || "").trim());
          const label = (a.textContent || "").trim();

          const slug =
            slugFromHref && (POSTS_BY_CATEGORY[slugFromHref] || slugFromHref === "all")
              ? slugFromHref
              : slugFromText;

          if (!slug) return;

          e.preventDefault();
          renderPanel(slug, label);
        });
      });
    });
  })();
</script>

---
layout: home
author_profile: true
title: "CYBERLOG"
classes: wide
---

> 밤에 만든 것들을 기록하는 개발 블로그.

<style>
  /* Sidebar category 클릭 시, 오른쪽에 표시될 리스트 패널 */
  #category-inline-panel {
    margin-top: 1rem;
    border: 1px solid rgba(35, 240, 255, 0.14);
    background: rgba(10, 14, 28, 0.42);
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 0 18px rgba(35, 240, 255, 0.05);
    overflow: hidden;
  }

  #category-inline-panel.is-hidden {
    display: none;
  }

  #category-inline-panel .category-inline-title {
    font-weight: 900;
    letter-spacing: 0.02em;
    margin: 0 0 0.65rem;
  }

  #category-inline-panel ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  #category-inline-panel li {
    padding: 0.65rem 0;
    border-top: 1px solid rgba(35, 240, 255, 0.10);
  }

  #category-inline-panel li:first-child {
    border-top: 0;
  }

  #category-inline-panel a {
    color: #23f0ff;
    text-decoration: none;
  }

  #category-inline-panel a:hover {
    text-decoration: underline;
    text-shadow: 0 0 10px rgba(35, 240, 255, 0.35);
  }

  #category-inline-panel .meta {
    margin-top: 0.25rem;
    color: rgba(137, 168, 184, 0.95);
    font-size: 0.92rem;
  }

  /* 최소한의 일치: “Recent Posts” 섹션은 클릭 시 우리 패널로 대체 */
  .category-inline-hidden-recent {
    display: none !important;
  }
</style>

<script>
  (function () {
    function normalizeSlug(s) {
      if (!s) return "";
      return String(s)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9가-힣\-_]/g, "");
    }

    function extractSlugFromHref(href) {
      if (!href) return "";
      try {
        const u = new URL(href, window.location.origin);
        const parts = u.pathname.split("/").filter(Boolean);
        const last = parts[parts.length - 1] || "";
        return normalizeSlug(decodeURIComponent(last));
      } catch (e) {
        const hash = href.split("#")[1];
        return normalizeSlug(hash || href);
      }
    }

    const POSTS = [
      {% for post in site.posts %}
        {
          url: {{ post.url | relative_url | jsonify }},
          title: {{ post.title | jsonify }},
          date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
          categories: [
            {% for c in post.categories %}
              {{ c | slugify | jsonify }}{% unless forloop.last %}, {% endunless %}
            {% endfor %}
          ]
        }{% unless forloop.last %},{% endunless %}
      {% endfor %}
    ];

    const POSTS_BY_CATEGORY = {};
    const ALL = POSTS.slice().sort((a, b) => new Date(b.date) - new Date(a.date));

    POSTS.forEach((p) => {
      (p.categories || []).forEach((slug) => {
        if (!POSTS_BY_CATEGORY[slug]) POSTS_BY_CATEGORY[slug] = [];
        POSTS_BY_CATEGORY[slug].push(p);
      });
    });
    Object.keys(POSTS_BY_CATEGORY).forEach((k) => {
      POSTS_BY_CATEGORY[k].sort((a, b) => new Date(b.date) - new Date(a.date));
    });

    function renderPanel(categorySlug) {
      const panel = document.getElementById("category-inline-panel");
      if (!panel) return;

      const title = panel.querySelector(".category-inline-title");
      const list = panel.querySelector("ul");
      if (!title || !list) return;

      const posts = categorySlug === "all" ? ALL : (POSTS_BY_CATEGORY[categorySlug] || []);

      const label =
        categorySlug === "all"
          ? "Recent Posts"
          : ("Category: " + categorySlug);

      title.textContent = label;

      list.innerHTML = "";
      posts.slice(0, 10).forEach((p) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = p.url;
        a.textContent = p.title;
        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = p.date;
        li.appendChild(a);
        li.appendChild(meta);
        list.appendChild(li);
      });

      panel.classList.remove("is-hidden");

      // Recent Posts(기본 섹션) 숨기고, 우리 패널로 대체
      const recentlyHeadings = Array.from(document.querySelectorAll(".page__content h1, .page__content h2, .page__content h3"));
      recentlyHeadings.forEach((h) => {
        const t = (h.textContent || "").trim().toLowerCase();
        if (t === "recent posts" || t.includes("recent posts") || t.includes("최근글")) {
          const container = h.closest("section") || h.closest("div") || h.parentElement;
          if (container) container.classList.add("category-inline-hidden-recent");
        }
      });
    }

    function ensurePanelMounted() {
      let panel = document.getElementById("category-inline-panel");
      if (panel) return panel;

      panel = document.createElement("div");
      panel.id = "category-inline-panel";
      panel.className = "is-hidden";

      panel.innerHTML = `
        <div class="category-inline-title">Recent Posts</div>
        <ul></ul>
      `;

      // 홈 메인 영역에 삽입 (Minimal Mistakes의 중앙 컬럼)
      const target =
        document.querySelector(".page__content .initial-content") ||
        document.querySelector(".page__content") ||
        document.querySelector("main") ||
        document.body;

      target.appendChild(panel);
      return panel;
    }

    document.addEventListener("DOMContentLoaded", function () {
      ensurePanelMounted();

      // 기본은 전체(최신글) 표시
      renderPanel("all");

      // 사이드바 카테고리(기존 버튼)를 클릭하면 목록만 바꿈
      const taxonomyLinks = Array.from(document.querySelectorAll(".taxonomy__index a"));
      taxonomyLinks.forEach((a) => {
        a.addEventListener("click", function (e) {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return; // 보조 클릭은 기본 동작 유지

          const slug = extractSlugFromHref(a.getAttribute("href")) || normalizeSlug(a.textContent);
          if (!slug) return;

          e.preventDefault();
          renderPanel(slug);
        });
      });
    });
  })();
</script>

---
layout: home
author_profile: true
title: "CYBERLOG"
classes: wide
---

<!--
<style>
  .hero {
    background: linear-gradient(135deg, #dbeafe 0%, #f5f3ff 100%);
    border: 1px solid #dbeafe;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    margin: 1rem 0 1.5rem;
  }
  .hero h1 { margin: 0 0 0.6rem; }
  .hero p { margin: 0; color: #4b5563; }
  .quick-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin: 0.9rem 0 0;
  }
  .quick-btn {
    display: inline-block;
    text-decoration: none;
    padding: 0.4rem 0.75rem;
    border-radius: 10px;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
    color: #1e3a8a;
    font-size: 0.88rem;
    font-weight: 600;
  }
  .quick-btn:hover {
    background: #dbeafe;
  }
  .toc {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 0.85rem 1rem;
    margin: 1rem 0 1.4rem;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    position: sticky;
    top: 0.8rem;
    z-index: 20;
  }
  .toc strong {
    display: block;
    margin-bottom: 0.5rem;
  }
  .toc ul {
    margin: 0;
    padding-left: 1.1rem;
  }
  .toc li { margin: 0.2rem 0; }
  .toc a {
    color: #1f2937;
    text-decoration: none;
  }
  .toc a:hover { text-decoration: underline; }
  @media (max-width: 700px) {
    .toc {
      top: 0.4rem;
    }
  }
  .grid { display: grid; gap: 1rem; margin: 1rem 0 1.5rem; }
  .grid-3 { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
  .card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
  }
  .card h3 { margin: 0 0 0.5rem; font-size: 1.05rem; }
  .card p { margin: 0; color: #4b5563; line-height: 1.6; }
  .pill-list { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.8rem; }
  .pill {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e3a8a;
    font-size: 0.85rem;
  }
  .muted { color: #4b5563; }
  .callout {
    border-left: 4px solid #2563eb;
    background: #f9fafb;
    padding: 0.85rem 1rem;
    border-radius: 8px;
    color: #4b5563;
  }
</style>

<section class="hero">
  <h1>내 블로그 시작 🚀</h1>
  <p>기술 + 일상 + 독서를 함께 기록하는 공간입니다.</p>
  <div class="quick-nav">
    <a class="quick-btn" href="#categories">카테고리 보기</a>
    <a class="quick-btn" href="#guide">운영 방식</a>
    <a class="quick-btn" href="#template">작성 템플릿</a>
    <a class="quick-btn" href="./categories.md">카테고리 가이드</a>
  </div>
</section>

<nav class="toc" aria-label="페이지 목차">
  <strong>빠른 목차</strong>
  <ul>
    <li><a href="#categories">카테고리</a></li>
    <li><a href="#guide">추천 운영 방식</a></li>
    <li><a href="#template">글 작성 템플릿</a></li>
  </ul>
</nav>

<h2 id="categories">카테고리</h2>

<section class="grid grid-3">
  <article class="card">
    <h3>💻 Tech</h3>
    <p>개발 기록, 삽질기, 문제 해결, 프로젝트 회고</p>
  </article>
  <article class="card">
    <h3>🌿 Life</h3>
    <p>일상, 생각, 루틴, 주간/월간 회고</p>
  </article>
  <article class="card">
    <h3>📚 Books</h3>
    <p>읽은 책 정리, 인사이트, 실천 포인트</p>
  </article>
</section>

<p class="muted">자세한 기준은 <a href="./categories.md"><code>categories.md</code></a> 에 정리해두었습니다.</p>

<h2 id="guide">추천 운영 방식</h2>

<div class="callout">
  카테고리는 3개로 고정하고, 세부 주제는 태그로 확장하면 글이 많아져도 구조가 무너지지 않습니다.
</div>

<div class="pill-list">
  <span class="pill">Category: Tech</span>
  <span class="pill">Category: Life</span>
  <span class="pill">Category: Books</span>
  <span class="pill">Tag: ai</span>
  <span class="pill">Tag: productivity</span>
  <span class="pill">Tag: fiction</span>
</div>

<h2 id="template">글 작성 템플릿 (GitHub Pages/Jekyll)</h2>

```md
---
layout: post
title: "글 제목"
date: 2026-03-20
category: Tech
tags: [ai, blog]
---

본문 내용...
```

`category`는 `Tech`, `Life`, `Books` 중 하나를 사용하면 됩니다.
-->

> 밤에 만든 것들을 기록하는 개발 블로그.

<style>
  .category-filter__panel {
    display: none;
  }

  .category-filter__panel.is-active {
    display: block;
  }

  .category-filter__list {
    margin-top: 0.75rem;
  }

  .category-filter__item {
    border: 1px solid rgba(35, 240, 255, 0.14);
    border-radius: 16px;
    background: rgba(10, 14, 28, 0.55);
    padding: 0.9rem 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 0 18px rgba(35, 240, 255, 0.05);
  }

  .category-filter__item-title {
    font-weight: 800;
    letter-spacing: 0.01em;
    margin: 0;
  }

  .category-filter__item-title a {
    color: var(--cyan);
    text-decoration: none;
  }

  .category-filter__item-title a:hover {
    text-decoration: underline;
  }

  .category-filter__item-meta {
    margin-top: 0.35rem;
    color: var(--muted);
    font-size: 0.9rem;
  }

  .category-filter__hint {
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 0.3rem;
  }
</style>

<!--
<div class="category-filter">
  <h2>Recent Posts</h2>
  <div class="category-filter__hint">사이드바 카테고리를 누르면 오른쪽 목록이 해당 카테고리 최신순으로 바뀝니다.</div>

  <div class="category-filter__panels">
    {% assign all_posts_sorted = site.posts | sort: "date" | reverse %}
    <section class="category-filter__panel is-active" data-category-panel="all">
      <div class="category-filter__list">
        {% for post in all_posts_sorted limit: 10 %}
          <article class="category-filter__item">
            <h3 class="category-filter__item-title">
              <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            </h3>
            <div class="category-filter__item-meta">
              {{ post.date | date: "%Y-%m-%d" }}
            </div>
          </article>
        {% endfor %}
      </div>
    </section>

    {% for category_pair in site.categories %}
      {% assign cat_name = category_pair[0] %}
      {% assign cat_slug = cat_name | slugify %}
      {% assign cat_posts_sorted = category_pair[1] | sort: "date" | reverse %}
      <section class="category-filter__panel" data-category-panel="{{ cat_slug }}">
        <div class="category-filter__list">
          {% for post in cat_posts_sorted limit: 10 %}
            <article class="category-filter__item">
              <h3 class="category-filter__item-title">
                <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
              </h3>
              <div class="category-filter__item-meta">
                {{ post.date | date: "%Y-%m-%d" }}
              </div>
            </article>
          {% endfor %}
        </div>
      </section>
    {% endfor %}
  </div>
</div>

<script>
  (function () {
    function normalizeSlug(s) {
      if (!s) return "";
      return String(s)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-");
    }

    function extractSlugFromHref(href) {
      if (!href) return "";
      try {
        const u = new URL(href, window.location.origin);
        const parts = u.pathname.split("/").filter(Boolean);
        const last = parts[parts.length - 1] || "";
        return normalizeSlug(decodeURIComponent(last));
      } catch (e) {
        // Fallback: try to use fragment or raw href
        const hash = href.split("#")[1];
        return normalizeSlug(hash || href);
      }
    }

    function hideRecentPosts() {
      // Minimal Mistakes home에는 "Recent Posts" 섹션이 기본으로 들어가 있음.
      // 그 영역은 우리가 렌더링한 필터 섹션으로 대체되도록 숨김 처리.
      const headings = Array.from(document.querySelectorAll("h1, h2, h3"));
      headings.forEach((h) => {
        // 우리가 만든 섹션은 숨기지 않음
        if (h.closest(".category-filter")) return;
        const t = (h.textContent || "").trim().toLowerCase();
        if (t === "recent posts" || t.includes("recent posts") || t.includes("최근글")) {
          const container = h.closest("section") || h.closest("div") || h.parentElement;
          if (container) container.style.display = "none";
        }
      });
    }

    document.addEventListener("DOMContentLoaded", function () {
      hideRecentPosts();

      const panels = Array.from(document.querySelectorAll("[data-category-panel]"));
      const panelBySlug = {};
      panels.forEach((p) => {
        panelBySlug[p.dataset.categoryPanel] = p;
      });

      // Minimal Mistakes taxonomy widget (categories/tags) 링크
      const links = Array.from(document.querySelectorAll(".taxonomy__index a"));
      links.forEach((a) => {
        a.addEventListener("click", function (e) {
          const slug = extractSlugFromHref(a.getAttribute("href"));
          if (!slug) return;
          if (panelBySlug[slug]) {
            e.preventDefault();
            panels.forEach((p) => p.classList.toggle("is-active", p.dataset.categoryPanel === slug));
          }
        });
      });
    });
  })();
</script>
-->
