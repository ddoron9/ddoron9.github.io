---
layout: single
title: ""
permalink: /
author_profile: false
classes: wide
---

{% assign home_categories = "dev,project,trouble,reading,log" | split: "," %}

<div class="home-shell">
  <aside class="home-sidebar">
    <section class="home-sidebar__panel home-intro">
      <p class="home-intro__eyebrow">DDORON9</p>
      <h1 class="home-intro__title">밤에 만든 것들을 기록하는 개발 블로그.</h1>
      <p class="home-intro__body">
        개발 기록, 프로젝트 회고, 트러블슈팅, 읽은 것들, 작업 로그를 다섯 개 카테고리로 정리합니다.
      </p>

      <ul class="home-profile">
        <li>
          <a href="mailto:doyikim34@naver.com">doyikim34@naver.com</a>
        </li>
        <li>Seoul</li>
        <li>
          <a href="https://github.com/ddoron9">GitHub</a>
        </li>
      </ul>
    </section>

    <nav class="home-sidebar__panel home-nav" aria-label="Category navigation">
      <p class="home-nav__label">Categories</p>
      <a class="home-nav__link" href="#recent-posts">
        <span>all</span>
        <span>{{ site.posts | size }}</span>
      </a>
      {% for category in home_categories %}
        {% assign category_posts = site.categories[category] %}
        <a class="home-nav__link" href="#category-{{ category }}">
          <span>{{ category }}</span>
          <span>{{ category_posts | size }}</span>
        </a>
      {% endfor %}
    </nav>
  </aside>

  <div class="home-main">
    <section class="home-section" id="recent-posts">
      <div class="home-section__header">
        <p class="home-section__kicker">Recent</p>
        <h2>최신 글</h2>
      </div>

      {% if site.posts.size > 0 %}
        <div class="home-post-list">
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
                {{ post.excerpt | strip_html | strip_newlines | truncate: 140 }}
              </p>
            </article>
          {% endfor %}
        </div>
      {% else %}
        <p class="home-empty">아직 작성된 글이 없습니다.</p>
      {% endif %}
    </section>

    {% for category in home_categories %}
      {% assign category_posts = site.categories[category] %}
      <section class="home-section" id="category-{{ category }}">
        <div class="home-section__header">
          <p class="home-section__kicker">Category</p>
          <h2>{{ category | capitalize }}</h2>
        </div>

        {% if category_posts and category_posts.size > 0 %}
          <div class="home-post-list">
            {% for post in category_posts %}
              <article class="home-post-card">
                <div class="home-post-card__meta">
                  <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y-%m-%d" }}</time>
                  <span>{{ category }}</span>
                </div>
                <h3 class="home-post-card__title">
                  <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
                </h3>
                <p class="home-post-card__excerpt">
                  {{ post.excerpt | strip_html | strip_newlines | truncate: 140 }}
                </p>
              </article>
            {% endfor %}
          </div>
        {% else %}
          <p class="home-empty">{{ category }} 카테고리 글을 아직 추가하지 않았습니다.</p>
        {% endif %}
      </section>
    {% endfor %}
  </div>
</div>
