// The component catalogue's own behaviour (base/templates/styleguide/index.html).
//
// - Writes into each token cell the value the page computes for that token, so
//   the table shows this instance's values, not the defaults it was built with.
// - Copies an entry's source to the clipboard.

const root = getComputedStyle(document.documentElement);
for (const cell of document.querySelectorAll("[data-token]")) {
  cell.textContent = root.getPropertyValue(cell.dataset.token).trim() || "(unset)";
}

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const source = document.getElementById(button.dataset.copy).textContent;
    try {
      await navigator.clipboard.writeText(source);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select the source to copy it";
    }
  });
}
