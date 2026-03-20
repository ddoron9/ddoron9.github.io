---
layout: single
title: ""
permalink: /
author_profile: false
classes: wide
---

{% assign home_categories = "dev,project,trouble,reading,log" | split: "," %}

<style>
  .layout--single .page,
  .layout--single.wide .page {
    float: none !important;
    width: min(98vw, 1880px) !important;
    max-width: 1880px !important;
    padding-right: 0 !important;
  }

  .layout--single .page__inner-wrap,
  .layout--single.wide .page__inner-wrap {
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
  }

  .layout--single .page__content,
  .layout--single.wide .page__content {
    float: none !important;
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
  }

  #home-root {
    display: grid;
    grid-template-columns: 320px minmax(0, 1fr);
    gap: 2rem;
    align-items: start;
    width: 100%;
  }

  #home-sidebar {
    display: grid;
    gap: 1rem;
    position: sticky;
    top: 1.5rem;
  }

  .home-box {
    background: rgba(8, 11, 24, 0.92);
    border: 1px solid rgba(35, 240, 255, 0.14);
    border-radius: 20px;
    box-shadow: 0 0 12px rgba(35, 240, 255, 0.22), 0 0 32px rgba(35, 240, 255, 0.08);
    backdrop-filter: blur(10px);
    padding: 1.2rem;
  }

  .home-kicker {
    margin: 0 0 0.75rem;
    color: #89a8b8;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .home-intro__title {
    margin: 0;
    font-size: 1.95rem;
    line-height: 1.18;
    color: #f4fbff;
  }

  .home-intro__body {
    margin: 0.9rem 0 0;
    color: #d8f6ff;
    line-height: 1.7;
  }

  .home-profile {
    list-style: none;
    margin: 1.2rem 0 0;
    padding: 0;
    display: grid;
    gap: 0.7rem;
  }

  .home-profile li {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    color: #d8f6ff;
  }

  .home-profile a {
    color: #23f0ff;
    text-decoration: none;
  }

  .home-profile a:hover {
    text-decoration: underline;
  }

  #home-nav {
    display: grid;
    gap: 0.7rem;
  }

  .home-nav__button {
    appearance: none;
    -webkit-appearance: none;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border: 1px solid rgba(35, 240, 255, 0.12);
    border-radius: 14px;
    background: rgba(5, 9, 18, 0.7);
    color: #d8f6ff;
    cursor: pointer;
    font: inherit;
    padding: 0.82rem 0.95rem;
    text-align: left;
    transition:
      transform 0.18s ease,
      border-color 0.18s ease,
      box-shadow 0.18s ease;
  }

  .home-nav__button:hover {
    transform: translateY(-1px);
    border-color: rgba(35, 240, 255, 0.28);
    box-shadow: 0 0 16px rgba(35, 240, 255, 0.14);
  }

  .home-nav__button.is-active {
    border-color: rgba(35, 240, 255, 0.34);
    box-shadow:
      0 0 16px rgba(35, 240, 255, 0.16),
      inset 0 0 18px rgba(35, 240, 255, 0.06);
  }

  #home-main {
    min-width: 0;
  }

  .home-result__header {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
    padding-bottom: 0.9rem;
    border-bottom: 1px solid rgba(35, 240, 255, 0.14);
  }

  .home-result__title {
    margin: 0;
    color: #f4fbff;
    font-size: 2rem;
    line-height: 1.1;
  }

  #home-result-body {
    display: grid;
    gap: 1rem;
  }

  .home-post-card {
    background: rgba(5, 9, 18, 0.78);
    border: 1px solid rgba(35, 240, 255, 0.12);
    border-radius: 18px;
    box-shadow: 0 0 16px rgba(35, 240, 255, 0.12);
    padding: 1.05rem 1.15rem;
  }

  .home-post-card__meta {
    display: flex;
    gap: 0.65rem;
    margin-bottom: 0.65rem;
    color: #89a8b8;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .home-post-card__title {
    margin: 0;
    font-size: 1.45rem;
    line-height: 1.25;
  }

  .home-post-card__title a {
    color: #f4fbff;
    text-decoration: none;
  }

  .home-post-card__title a:hover {
    color: #23f0ff;
  }

  .home-post-card__excerpt,
  .home-empty {
    margin: 0.8rem 0 0;
    color: #89a8b8;
    line-height: 1.75;
    font-size: 1.02rem;
  }

  @media (max-width: 960px) {
    #home-root {
      grid-template-columns: 1fr;
    }

    #home-sidebar {
      position: static;
    }
  }
</style>

<div id="home-root">
  <aside id="home-sidebar">
    <section class="home-box">
      <p class="home-kicker">DDORON9</p>
      <h1 class="home-intro__title">밤에 만든 것들을 기록하는 개발 블로그.</h1>
      <p class="home-intro__body">
        개발 기록, 프로젝트 회고, 트러블슈팅, 읽은 것들, 작업 로그를 다섯 개 카테고리로 정리합니다.
      </p>

      <ul class="home-profile">
        <li>
          <span aria-hidden="true">📧</span>
          <a href="mailto:doyikim34@naver.com">doyikim34@naver.com</a>
        </li>
        <li>
          <span aria-hidden="true">📍</span>
          <span>Seoul</span>
        </li>
        <li>
          <span aria-hidden="true">🐙</span>
          <a href="https://github.com/ddoron9">GitHub</a>
        </li>
      </ul>
    </section>

    <nav class="home-box" id="home-nav" aria-label="Category navigation">
      <p class="home-kicker">Categories</p>
      <button class="home-nav__button is-active" type="button" data-key="recent">
        <span>recent</span>
        <span>{{ site.posts | size }}</span>
      </button>
      {% for category in home_categories %}
        {% assign category_count = 0 %}
        {% for post in site.posts %}
          {% if post.categories contains category %}
            {% assign category_count = category_count | plus: 1 %}
          {% endif %}
        {% endfor %}
        <button class="home-nav__button" type="button" data-key="{{ category }}">
          <span>{{ category }}</span>
          <span>{{ category_count }}</span>
        </button>
      {% endfor %}
    </nav>
  </aside>

  <main id="home-main">
    <section class="home-box">
      <div class="home-result__header">
        <p class="home-kicker" id="home-result-kicker">Recent</p>
        <h2 class="home-result__title" id="home-result-title">최신 글</h2>
      </div>

      <div id="home-result-body">
        {% if site.posts.size > 0 %}
          {% for post in site.posts limit: 8 %}
            <article class="home-post-card">
              <div class="home-post-card__meta">
                <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y-%m-%d" }}</time>
                {% if post.categories and post.categories.size > 0 %}
                  <span>{{ post.categories | first }}</span>
                {% endif %}
              </div>
              <h3 class="home-post-card__title">
                <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
              </h3>
              <p class="home-post-card__excerpt">
                {{ post.excerpt | strip_html | strip_newlines | truncate: 180 }}
              </p>
            </article>
          {% endfor %}
        {% else %}
          <p class="home-empty">아직 작성된 글이 없습니다.</p>
        {% endif %}
      </div>
    </section>
  </main>
</div>

<script>
  document.addEventListener("DOMContentLoaded", function () {
    const buttons = Array.from(document.querySelectorAll(".home-nav__button"));
    const kicker = document.getElementById("home-result-kicker");
    const title = document.getElementById("home-result-title");
    const body = document.getElementById("home-result-body");

    const postIndex = {
      recent: [
        {% for post in site.posts limit: 8 %}
          {
            title: {{ post.title | jsonify }},
            url: {{ post.url | relative_url | jsonify }},
            date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
            category: {{ post.categories | first | default: "" | jsonify }},
            excerpt: {{ post.excerpt | strip_html | strip_newlines | truncate: 180 | jsonify }}
          }{% unless forloop.last %},{% endunless %}
        {% endfor %}
      ],
      {% for category in home_categories %}
        {{ category | jsonify }}: [
          {% assign emitted = false %}
          {% for post in site.posts %}
            {% if post.categories contains category %}
              {% if emitted %},{% endif %}
              {
                title: {{ post.title | jsonify }},
                url: {{ post.url | relative_url | jsonify }},
                date: {{ post.date | date: "%Y-%m-%d" | jsonify }},
                category: {{ category | jsonify }},
                excerpt: {{ post.excerpt | strip_html | strip_newlines | truncate: 180 | jsonify }}
              }
              {% assign emitted = true %}
            {% endif %}
          {% endfor %}
        ]{% unless forloop.last %},{% endunless %}
      {% endfor %}
    };

    const panelMeta = {
      recent: { kicker: "Recent", title: "최신 글" },
      dev: { kicker: "Category", title: "Dev" },
      project: { kicker: "Category", title: "Project" },
      trouble: { kicker: "Category", title: "Trouble" },
      reading: { kicker: "Category", title: "Reading" },
      log: { kicker: "Category", title: "Log" }
    };

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function renderPosts(key) {
      const posts = postIndex[key] || [];
      const meta = panelMeta[key] || panelMeta.recent;

      kicker.textContent = meta.kicker;
      title.textContent = meta.title;

      if (posts.length === 0) {
        body.innerHTML = '<p class="home-empty">이 카테고리에는 아직 글이 없습니다.</p>';
        return;
      }

      body.innerHTML = posts.map((post) => {
        const categoryBadge = post.category
          ? "<span>" + escapeHtml(post.category) + "</span>"
          : "";

        return (
          '<article class="home-post-card">' +
            '<div class="home-post-card__meta">' +
              '<time datetime="' + escapeHtml(post.date) + '">' + escapeHtml(post.date) + "</time>" +
              categoryBadge +
            "</div>" +
            '<h3 class="home-post-card__title">' +
              '<a href="' + escapeHtml(post.url) + '">' + escapeHtml(post.title) + "</a>" +
            "</h3>" +
            '<p class="home-post-card__excerpt">' + escapeHtml(post.excerpt) + "</p>" +
          "</article>"
        );
      }).join("");
    }

    buttons.forEach((button) => {
      button.addEventListener("click", function () {
        const key = button.dataset.key;
        buttons.forEach((item) => item.classList.toggle("is-active", item === button));
        renderPosts(key);
      });
    });
  });
</script>
