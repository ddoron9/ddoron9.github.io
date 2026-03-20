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
</style>

<section class="hero">
  <h1>카테고리 가이드</h1>
  <p>이 블로그는 3개의 메인 카테고리로 운영합니다.</p>
</section>

<section class="grid grid-3">
  <article class="card">
    <h3>💻 Tech</h3>
    <p>개발 관련 기록을 모읍니다. 트러블슈팅, 개념 정리, 프로젝트 회고를 담습니다.</p>
    <div class="pill-list">
      <span class="pill">frontend</span>
      <span class="pill">backend</span>
      <span class="pill">ai</span>
      <span class="pill">architecture</span>
    </div>
  </article>
  <article class="card">
    <h3>🌿 Life</h3>
    <p>개발 외 일상과 생각을 기록합니다. 일상 로그, 회고, 루틴 관리를 담습니다.</p>
    <div class="pill-list">
      <span class="pill">routine</span>
      <span class="pill">thoughts</span>
      <span class="pill">work-life</span>
    </div>
  </article>
  <article class="card">
    <h3>📚 Books</h3>
    <p>책에서 얻은 내용과 해석을 남깁니다. 요약, 문장 수집, 실천 포인트를 기록합니다.</p>
    <div class="pill-list">
      <span class="pill">nonfiction</span>
      <span class="pill">fiction</span>
      <span class="pill">self-improvement</span>
    </div>
  </article>
</section>

## 운영 원칙

- 카테고리는 **하나만 선택** (글의 중심 주제 기준)
- 태그는 2~5개 권장
- 애매할 때 판단 우선순위
  - 코드/기술 설명 중심이면 `Tech`
  - 삶/태도/경험 중심이면 `Life`
  - 책 내용 해석 중심이면 `Books`
