// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Searching, sorting and collapsing for every list of tags on the platform.
//
// There are three of them -- the tag administration page, the factsheet
// editor's Tags tab, and the factsheet overview's filter -- and each showed
// its whole vocabulary at once: ~825 pills on the first two, 273 on the third.
// One module so the three cannot drift into three different behaviours, and
// so the behaviour is testable without a page.
//
// The markup contract is three data attributes and nothing else:
//
//   [data-tag-list]                     the container
//     [data-tag-name] [data-tag-usage]  one per item
//   [data-tag-search]                   an input, optional
//   [data-tag-expand]                   a button, optional
//
// Everything degrades: without javascript the server has already rendered
// every tag, which is exactly what the pages did before.

/**
 * Whether a tag name matches what the reader typed.
 *
 * A plain case-insensitive substring test -- these are short labels, and a
 * cleverer match would surprise more often than it would help.
 *
 * @param {string} name the tag's name.
 * @param {string} query what the reader typed.
 * @return {boolean} true when the tag should stay visible.
 */
export function matchesQuery(name, query) {
  const needle = (query || "").trim().toLowerCase();
  return !needle || (name || "").toLowerCase().includes(needle);
}

/**
 * The items in display order.
 *
 * `usage` counts what actually points at a tag. It is deliberately NOT
 * `Tag.usage_count`, which is incremented only by table search in `dataedit`
 * and never by factsheets, so ordering by it would rank an unrelated quantity.
 *
 * @param {{name: string, usage: number}[]} items the tags to order.
 * @param {string} sort either "name" or "usage".
 * @return {{name: string, usage: number}[]} a new, ordered array.
 */
export function orderItems(items, sort) {
  // `numeric` so that digits inside a name sort as numbers: "run 2" before
  // "run 10", which a plain lexicographic compare gets backwards. That covers
  // alphabetical and numerical ordering with one option instead of two that
  // are each wrong half the time.
  const collator = new Intl.Collator(undefined, {
    numeric: true,
    sensitivity: "base",
  });
  const byName = (a, b) => collator.compare(a.name, b.name);
  return items
    .slice()
    .sort((a, b) => (sort === "usage" ? b.usage - a.usage || byName(a, b) : byName(a, b)));
}

/**
 * Show, hide and reorder a tag list to match one state.
 *
 * @param {HTMLElement} container the `[data-tag-list]` element.
 * @param {{query?: string, limit?: number|null, sort?: string}} state what to
 *   show.
 * @return {{total: number, matched: number, shown: number}} what it did.
 */
export function applyTagList(container, state) {
  const { query = "", limit = null, sort = "name" } = state || {};
  const items = Array.from(container.children).map((el) => ({
    el,
    name: el.getAttribute("data-tag-name") || "",
    usage: Number(el.getAttribute("data-tag-usage") || 0),
  }));

  const ordered = orderItems(items, sort);
  ordered.forEach((item) => container.appendChild(item.el));

  const searching = Boolean((query || "").trim());
  let shown = 0;
  let matched = 0;
  ordered.forEach((item) => {
    const hit = matchesQuery(item.name, query);
    if (hit) {
      matched += 1;
    }
    // A limit is a way to shorten a long list, not a way to hide something
    // the reader asked for: a search overrides it, and a tag that is already
    // selected always stays visible or the filter would be on with nothing
    // on screen to say so.
    const selected = Boolean(item.el.querySelector("input:checked"));
    const room = limit === null || searching || shown < limit;
    const visible = hit && (room || selected);
    item.el.hidden = !visible;
    if (visible) {
      shown += 1;
    }
  });

  return { total: items.length, matched, shown };
}

/**
 * Wire a tag list to its search box, sort control and expand button.
 *
 * @param {ParentNode} root the element to search, usually `document`.
 * @param {{limit?: number|null, sort?: string}} options the collapsed size and
 *   the initial ordering.
 * @return {boolean} whether a list was found to bind.
 */
export function bindTagList(root, options) {
  const container = root.querySelector("[data-tag-list]");
  if (!container) {
    return false;
  }
  const { limit = null, sort = "name" } = options || {};
  const search = root.querySelector("[data-tag-search]");
  const expand = root.querySelector("[data-tag-expand]");
  const sorter = root.querySelector("[data-tag-sort]");

  const state = { query: "", limit, sort, expanded: false };

  const render = () => {
    const counts = applyTagList(container, {
      query: state.query,
      limit: state.expanded ? null : state.limit,
      sort: state.sort,
    });
    if (expand) {
      const hiddenCount = counts.matched - counts.shown;
      expand.hidden = state.expanded || hiddenCount <= 0;
      expand.textContent = "Show all " + counts.total + " tags";
    }
    return counts;
  };

  if (search) {
    search.addEventListener("input", () => {
      state.query = search.value;
      render();
    });
  }
  if (expand) {
    expand.addEventListener("click", (event) => {
      event.preventDefault();
      state.expanded = true;
      render();
    });
  }
  if (sorter) {
    sorter.addEventListener("change", () => {
      state.sort = sorter.value;
      render();
    });
  }

  render();
  return true;
}
