document.addEventListener("DOMContentLoaded", loadUsers);

async function loadUsers() {
  const res = await fetch("/users");
  const data = await res.json();
  const users = data.users;
  const tbody = document.querySelector("#user-table tbody");
  tbody.innerHTML = "";

  users.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${u.username}</td>
      <td>${u.role}</td>
      <td>${u.entity || "-"}</td>
      <td>${u.status || "unknown"}</td>
      <td>
        ${u.status !== "approved" ? `<button class="btn btn-sm btn-success" onclick="approveUser('${u.id}')">Approve</button>` : ""}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function approveUser(id) {
  const res = await fetch(`/approve_user/${id}`, {
    method: "POST"
  });
  if (res.ok) {
    loadUsers();
  } else {
    alert("Failed to approve user");
  }
}
