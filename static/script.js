const API_BASE = "";

const form = document.getElementById("license-form");
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const license = {
      license_name: form.license_name.value,
      price: form.price.value,
      validity: form.validity.value,
      expiration_date: form.expiration_date.value,
    };

    const res = await fetch(`${API_BASE}/license`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(license),
    });

    if (res.ok) {
      loadLicenses();
      form.reset();
      showAlert("License added successfully!", "success");
    } else {
      const error = await res.json();
      showAlert(error.error || "Failed to add license", "danger");
    }
  });
}

// Load licenses only if the table exists
if (document.querySelector("#license-table")) {
  loadLicenses();
}
function showAlert(message, type = "info") {
  const container = document.createElement("div");
  container.className = `alert alert-${type} alert-dismissible fade show mt-3`;
  container.role = "alert";
  container.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.querySelector(".container").prepend(container);
  setTimeout(() => {
    container.classList.remove("show");
    container.classList.add("hide");
  }, 5000);
}

async function loadLicenses() {
  const res = await fetch(`${API_BASE}/licenses`);
  const licenses = await res.json();
  const tbody = document.querySelector("#license-table tbody");
  tbody.innerHTML = "";

  const today = new Date().toISOString().split("T")[0];

  licenses.forEach((l) => {
    const isExpired = l.expiration_date < today;
    const badge = isExpired
      ? `<span class="badge bg-danger ms-2">Expired</span>`
      : "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${l.license_name}</td>
      <td>${l.price}</td>
      <td>${l.validity}</td>
      <td>${l.expiration_date} ${badge}</td>
      <td class="text-center">
        <button class="btn btn-sm btn-outline-danger" onclick="deleteLicense('${l.id}')">
          <i class="bi bi-trash"></i> Delete
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function deleteLicense(id) {
  if (!confirm("Are you sure you want to delete this license?")) return;

  const res = await fetch(`${API_BASE}/license/${id}`, {
    method: "DELETE",
  });

  if (res.ok) {
    loadLicenses();
    showAlert("License deleted successfully", "warning");
  } else {
    alert("Delete failed");
  }
}


