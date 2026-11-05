const form = document.getElementById("order-form");
const statusEl = document.getElementById("form-status");

document.querySelectorAll("[data-product]").forEach((button) => {
  button.addEventListener("click", () => {
    const value = button.getAttribute("data-product");
    const input = form.querySelector(`input[name="product"][value="${value}"]`);
    if (input) input.checked = true;
  });
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const name = data.get("name");
  const contact = data.get("contact");
  const product = data.get("product");
  const notes = data.get("notes") || "None";
  const body = [
    `Name: ${name}`,
    `Contact: ${contact}`,
    `Product: ${product}`,
    `Notes: ${notes}`,
  ].join("\n");

  window.location.href = `mailto:orders@ahsbroker.com?subject=${encodeURIComponent(
    `AHS Broker order: ${product}`
  )}&body=${encodeURIComponent(body)}`;

  statusEl.hidden = false;
  statusEl.textContent =
    "Your email app should open with the order details. If it does not, message us with the same info.";
});
