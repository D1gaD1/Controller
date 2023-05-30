var sidebar = document.getElementById("sidebar");
var toggleSidebarButton = document.getElementById("toggle-sidebar");

toggleSidebarButton.addEventListener("click", function () {
  if (sidebar.classList.contains("show")) {
      sidebar.classList.remove("show");
  } else {
      sidebar.classList.add("show");
  }
});

function toggleElement(id) {
  const element = document.getElementById(id);
  if (element.style.maxHeight) {
      element.style.maxHeight = null;
  } else {
      element.style.maxHeight = element.scrollHeight + "px";
  }
}

document.getElementById('login').addEventListener('click', function() {
  toggleElement('login-window');
});

document.getElementById('controller').addEventListener('click', function() {
  toggleElement('controller-window');
});

document.getElementById('logs').addEventListener('click', function() {
  toggleElement('logs-window');
});
