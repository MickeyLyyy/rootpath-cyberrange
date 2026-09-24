document.addEventListener("DOMContentLoaded", function () {
  try {
    var nav = document.querySelector(".navbar-nav");
    if (!nav) return;
    if (document.querySelector('a[href="/plugins/rootpath/dashboard"]')) return;
    var li = document.createElement("li"); li.className = "nav-item";
    var a = document.createElement("a");
    a.className = "nav-link"; a.href = "/plugins/rootpath/dashboard"; a.textContent = "Dashboard";
    li.appendChild(a); nav.appendChild(li);
  } catch (e) {}
});
