const $ = (q) => document.querySelector(q);
const escapeHTML = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const icon = (name) => `<i data-lucide="${name}" aria-hidden="true"></i>`;
let items = [],
  byId = new Map(),
  recommendations = [],
  ratings = {},
  saved = [],
  view = "home",
  type = "전체",
  activeId = null,
  heroId = null,
  sequence = 0,
  pageSize = 24,
  loadError = false;
try {
  const state = JSON.parse(localStorage.getItem("next-learning-v1") || "{}");
  ratings = Object.fromEntries(
    Object.entries(state.ratings || {}).filter(
      ([id, r]) =>
        Number.isInteger(Number(id)) && Number.isInteger(r) && r >= 1 && r <= 5,
    ),
  );
  saved = Array.isArray(state.saved)
    ? [...new Set(state.saved.filter(Number.isInteger))]
    : [];
} catch {}
function icons() {
  lucide.createIcons();
}
function toast(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => ($("#toast").hidden = true), 2500);
}
function persist() {
  try {
    localStorage.setItem(
      "next-learning-v1",
      JSON.stringify({ ratings, saved }),
    );
    return true;
  } catch {
    toast("저장 공간이 부족해요. 이번 기록은 새로고침하면 사라집니다.");
    return false;
  }
}
async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Request failed");
  return response.json();
}
async function refresh() {
  const token = ++sequence;
  $("#status").textContent = "취향에 맞는 콘텐츠를 찾고 있어요…";
  try {
    const data = await request("/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ratings: Object.entries(ratings).map(([item_id, rating]) => ({
          item_id: Number(item_id),
          rating,
        })),
      }),
    });
    if (token !== sequence) return;
    recommendations = data.recommendations;
    loadError = false;
    render();
  } catch {
    if (token !== sequence) return;
    loadError = true;
    render();
  }
}
function card(item, rank) {
  const el = document.createElement("article");
  el.className = "card" + (rank ? " ranked" : "");
  const rated = ratings[item.item_id];
  el.innerHTML = `<div class="card-image"><button class="image-open" aria-label="${escapeHTML(item.title)} 자세히 보기"><img src="/static/images/${escapeHTML(item.image)}.jpg" alt="" loading="lazy"><span class="image-type">${escapeHTML(item.category)}</span>${rank ? `<span class="rank">${rank}</span>` : ""}</button><button class="bookmark" aria-label="${escapeHTML(item.title)} ${saved.includes(item.item_id) ? "찜 취소" : "찜하기"}" title="${saved.includes(item.item_id) ? "찜 취소" : "찜하기"}" aria-pressed="${saved.includes(item.item_id)}">${icon(saved.includes(item.item_id) ? "check" : "plus")}</button></div><button class="card-title">${escapeHTML(item.title)}</button><div class="card-meta"><span class="rating">★ ${item.average.toFixed(1)}</span><span>${escapeHTML(item.genre)}</span><span>${item.year}</span></div><p class="card-reason"></p>`;
  el.querySelector(".card-reason").textContent = rated
    ? `내 평점 ${"★".repeat(rated)}`
    : item.reason || `${item.duration} · ${item.category}`;
  el.querySelector(".image-open").onclick = el.querySelector(
    ".card-title",
  ).onclick = () => openDetail(item.item_id);
  el.querySelector(".bookmark").onclick = () => toggleSave(item.item_id);
  return el;
}
function shelf(title, list, subtitle = "", ranked = false, grid = false) {
  if (!list.length) return;
  const section = document.createElement("section");
  section.className = "shelf";
  const header = document.createElement("div");
  header.className = "shelf-heading";
  header.innerHTML = `<div><h2>${escapeHTML(title)}</h2>${subtitle ? `<small>${escapeHTML(subtitle)}</small>` : ""}</div>`;
  const rail = document.createElement("div");
  rail.className = grid ? "results-grid" : "rail";
  rail.setAttribute("aria-label", title);
  list.forEach((item, index) =>
    rail.append(card(item, ranked ? index + 1 : null)),
  );
  if (!grid) {
    const arrows = document.createElement("div");
    arrows.className = "arrows";
    for (const [direction, name, label] of [
      [-1, "chevron-left", "이전"],
      [1, "chevron-right", "다음"],
    ]) {
      const b = document.createElement("button");
      b.className = "icon-button";
      b.innerHTML = icon(name);
      b.title = `${title} ${label}`;
      b.setAttribute("aria-label", `${title} ${label}`);
      b.onclick = () =>
        rail.scrollBy({
          left: direction * rail.clientWidth * 0.8,
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
        });
      arrows.append(b);
    }
    header.append(arrows);
  }
  section.append(header, rail);
  $("#shelves").append(section);
}
function filtered(list) {
  const genre = $("#genre").value;
  const query = $("#search").value.trim().toLowerCase();
  return list.filter(
    (i) =>
      (type === "전체" || i.category === type) &&
      (genre === "전체" || i.genre === genre) &&
      `${i.title} ${i.genre} ${i.category}`.toLowerCase().includes(query),
  );
}
function render() {
  if (!items.length) return;
  $("#saved-count").textContent = saved.length;
  $("#taste-count").textContent =
    `내 취향 기록 ${Object.keys(ratings).length}개`;
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
    if (b.dataset.view === view) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  const ranked = recommendations
    .filter((r) => byId.has(r.item_id) && !ratings[r.item_id])
    .map((r) => ({ ...byId.get(r.item_id), ...r }));
  let source =
    view === "saved"
      ? items.filter((i) => saved.includes(i.item_id))
      : view === "rated"
        ? items.filter((i) => ratings[i.item_id])
        : view === "all"
          ? items
          : ranked;
  let list = filtered(source);
  if ($("#sort").value === "recommended" && view !== "home") {
    const positions = new Map(ranked.map((item, index) => [item.item_id, index]));
    list.sort((a, b) =>
      (positions.get(a.item_id) ?? items.length) -
      (positions.get(b.item_id) ?? items.length) || b.average - a.average,
    );
  }
  if ($("#sort").value === "rating")
    list.sort((a, b) => b.average - a.average || b.count - a.count);
  if ($("#sort").value === "year")
    list.sort((a, b) => b.year - a.year || b.average - a.average);
  $("#collection-count").textContent =
    `${items.length}개 콘텐츠 · ${new Set(items.map((i) => i.category)).size}가지 종류`;
  $("#shelves").replaceChildren();
  const isHome =
    view === "home" &&
    type === "전체" &&
    $("#genre").value === "전체" &&
    !$("#search").value.trim() &&
    $("#sort").value === "recommended";
  $("#hero").hidden = !isHome || !ranked.length;
  if (isHome && ranked.length) {
    const feature = ranked.find((i) => i.category === "영화") || ranked[0];
    heroId = feature.item_id;
    $("#hero-open").disabled = $("#hero-save").disabled = false;
    $("#hero-image").src = `/static/images/${feature.image}.jpg`;
    $("#hero-title").textContent = feature.title;
    $("#hero-category").textContent = Object.keys(ratings).length
      ? "당신의 취향에서 이어지는 이야기"
      : "오늘, 새롭게 발견할 이야기";
    $("#hero-meta").innerHTML =
      `<span class="match">${escapeHTML(feature.genre)}</span><span>${feature.year}</span><span class="age">${feature.audience}</span><span>${feature.duration}</span>`;
    $("#hero-description").textContent = feature.description;
    $("#hero-reason").textContent = feature.reason;
    $("#hero-save").innerHTML =
      icon(saved.includes(heroId) ? "check" : "plus") +
      (saved.includes(heroId) ? "내 목록에 저장됨" : "내 목록에 추가");
    shelf(
      Object.keys(ratings).length
        ? "지금, 당신을 위한 추천"
        : "새로운 취향을 발견해보세요",
      ranked.slice(0, 12),
      "다른 종류의 콘텐츠로 이어지는 취향",
    );
    shelf(
      "샘플 평점 TOP 10",
      [...ranked]
        .sort((a, b) => b.average - a.average || b.count - a.count)
        .slice(0, 10),
      "가상 사용자들의 평균 평점 기준",
      true,
    );
    const liked = items
      .filter((i) => ratings[i.item_id] >= 4)
      .sort((a, b) => ratings[b.item_id] - ratings[a.item_id])[0];
    if (liked)
      shelf(
        `「${liked.title}」을 좋아하셨다면`,
        ranked.filter((i) => i.genre === liked.genre).slice(0, 12),
        `${liked.genre}에서 발견하는 또 다른 이야기`,
      );
    for (const category of ["영화", "시리즈", "다큐", "도서", "강좌"])
      shelf(
        {
          영화: "오늘 밤, 한 편의 영화",
          시리즈: "다음 이야기가 기다리는 시리즈",
          다큐: "세상을 넓혀주는 다큐멘터리",
          도서: "화면을 넘어, 한 권의 이야기",
          강좌: "호기심을 배움으로",
        }[category],
        ranked.filter((i) => i.category === category).slice(0, 12),
      );
  } else {
    const title = {
      home: "취향으로 고른 콘텐츠",
      all: "모든 콘텐츠",
      saved: "내가 찜한 목록",
      rated: "나의 취향 기록",
    }[view];
    shelf(
      title,
      list.slice(0, pageSize),
      `${list.length}개 콘텐츠`,
      false,
      true,
    );
    if (list.length > pageSize) {
      const more = document.createElement("button");
      more.className = "more";
      more.textContent = `더 보기 (${Math.min(pageSize, list.length)} / ${list.length})`;
      more.onclick = () => {
        pageSize += 24;
        render();
      };
      $("#shelves").append(more);
    }
  }
  $("#status").textContent = loadError
    ? "추천을 불러오지 못했어요. 다시 시도해주세요."
    : !list.length
      ? view === "saved"
        ? "찜한 콘텐츠가 없어요. 마음에 드는 작품을 내 목록에 담아보세요."
        : view === "rated"
          ? "콘텐츠를 열고 별점을 남겨보세요."
          : "조건에 맞는 콘텐츠가 없어요. 다른 종류나 장르를 골라보세요."
      : "";
  $("#retry").hidden = !loadError;
  icons();
}
function toggleSave(id) {
  saved = saved.includes(id) ? saved.filter((x) => x !== id) : [...saved, id];
  const ok = persist();
  const scrolls = [...document.querySelectorAll(".rail")].map(
    (r) => r.scrollLeft,
  );
  render();
  document
    .querySelectorAll(".rail")
    .forEach((r, i) => (r.scrollLeft = scrolls[i] || 0));
  if (activeId === id) drawDetail();
  if (ok)
    toast(saved.includes(id) ? "내 목록에 담았어요." : "내 목록에서 지웠어요.");
}
function drawDetail() {
  const i = byId.get(activeId);
  if (!i) return;
  $("#detail-content").innerHTML =
    `<img class="detail-image" src="/static/images/${escapeHTML(i.image)}.jpg" alt=""><div class="detail-body"><p class="detail-topic">${escapeHTML(i.category)} · ${escapeHTML(i.genre)} · ${i.year} · ${i.duration}</p><h2 id="detail-title">${escapeHTML(i.title)}</h2><p class="detail-description">${escapeHTML(i.description)}</p><p class="detail-topic">★ ${i.average.toFixed(1)} · ${i.count}개 샘플 평점</p><div class="rating-section"><h3>나의 평점</h3><div class="stars" role="group" aria-label="별점 선택">${[1, 2, 3, 4, 5].map((r) => `<button class="${r <= (ratings[activeId] || 0) ? "on" : ""}" data-rating="${r}" aria-label="${r}점" aria-pressed="${r === ratings[activeId]}">★</button>`).join("")}</div><div class="rating-label">${ratings[activeId] ? ["", "내 취향이 아니에요", "조금 아쉬워요", "보통이에요", "마음에 들어요", "아주 좋아요"][ratings[activeId]] : "이 콘텐츠는 내 취향일까요?"}</div></div><div class="detail-actions"><button class="save-action">${saved.includes(activeId) ? "내 목록에서 삭제" : "내 목록에 추가"}</button><button class="remove-rating" ${ratings[activeId] ? "" : "hidden"}>평점 지우기</button></div><h3 class="similar-heading">비슷한 취향의 콘텐츠</h3><div class="similar-list"></div><p class="sample-note">가상 콘텐츠 · 실제 재생, 수강 또는 구매는 제공하지 않습니다.</p></div>`;
  const similar = items
    .filter((x) => x.item_id !== activeId && x.genre === i.genre)
    .sort((a, b) => b.average - a.average)
    .slice(0, 3);
  for (const x of similar) {
    const b = document.createElement("button");
    b.textContent = x.title;
    b.onclick = () => {
      activeId = x.item_id;
      drawDetail();
      $("#detail").scrollTop = 0;
      $("#detail .close").focus();
    };
    $("#detail .similar-list").append(b);
  }
  $("#detail .save-action").onclick = () => toggleSave(activeId);
  $("#detail .remove-rating").onclick = () => {
    delete ratings[activeId];
    persist();
    drawDetail();
    refresh();
  };
  document.querySelectorAll("[data-rating]").forEach(
    (b) =>
      (b.onclick = () => {
        const r = Number(b.dataset.rating);
        ratings[activeId] = r;
        const ok = persist();
        drawDetail();
        document.querySelector(`[data-rating="${r}"]`).focus();
        refresh();
        if (ok) toast("취향을 기록했어요.");
      }),
  );
  icons();
}
function openDetail(id) {
  activeId = id;
  drawDetail();
  if (!$("#detail").open) $("#detail").showModal();
}
$("#detail .close").onclick = () => $("#detail").close();
$("#detail").addEventListener("close", () => (activeId = null));
$("#detail").addEventListener("click", (e) => {
  if (e.target !== $("#detail")) return;
  const r = $("#detail").getBoundingClientRect();
  if (
    e.clientX < r.left ||
    e.clientX > r.right ||
    e.clientY < r.top ||
    e.clientY > r.bottom
  )
    $("#detail").close();
});
$("#hero-open").onclick = () => openDetail(heroId);
$("#hero-save").onclick = () => toggleSave(heroId);
document.querySelectorAll("[data-view]").forEach(
  (b) =>
    (b.onclick = () => {
      view = b.dataset.view;
      pageSize = 24;
      render();
    }),
);
$("#profile").onclick = () => {
  view = "rated";
  render();
};
document.querySelectorAll("[data-type]").forEach(
  (b) =>
    (b.onclick = () => {
      type = b.dataset.type;
      pageSize = 24;
      document.querySelectorAll("[data-type]").forEach((x) => {
        x.classList.toggle("selected", x === b);
        x.setAttribute("aria-pressed", x === b);
      });
      render();
    }),
);
for (const selector of ["#genre", "#sort"])
  $(selector).onchange = () => {
    pageSize = 24;
    render();
  };
$("#search").oninput = () => {
  pageSize = 24;
  render();
};
async function init() {
  try {
    const data = await request("/catalog");
    items = data.items;
    byId = new Map(items.map((i) => [i.item_id, i]));
    ratings = Object.fromEntries(
      Object.entries(ratings).filter(([id]) => byId.has(Number(id))),
    );
    saved = saved.filter((id) => byId.has(id));
    const current = $("#genre").value;
    $("#genre").replaceChildren(new Option("모든 장르", "전체"));
    for (const genre of [...new Set(items.map((i) => i.genre))])
      $("#genre").append(new Option(genre, genre));
    $("#genre").value = current || "전체";
    await refresh();
  } catch {
    $("#status").textContent =
      "콘텐츠를 불러오지 못했어요. 잠시 후 다시 시도해주세요.";
    $("#retry").hidden = false;
  }
}
$("#retry").onclick = init;
icons();
init();
