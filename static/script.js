let selectedMode = "general"; // default

document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedMode = btn.dataset.mode;

    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  });
});

document.getElementById("analyze-btn").addEventListener("click", () => {
  const idea = document.getElementById("idea").value;
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  resultDiv.classList.add("hidden");
  loading.classList.remove("hidden");

  fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea, mode: selectedMode }),
  })
    .then(res => res.json())
    .then(data => {
      loading.classList.add("hidden");
      resultDiv.classList.remove("hidden");

      resultDiv.innerText = data.result || "Error: " + data.error;
    });
});

particlesJS("particles-js", {
  particles: {
    number: { value: 60 },
    color: { value: "#38bdf8" },
    size: { value: 3 },
    line_linked: {
      enable: true,
      color: "#38bdf8",
      opacity: 0.3,
    },
    move: {
      enable: true,
      speed: 1,
    },
  },
  interactivity: {
    detect_on: "canvas",
    events: {
      onhover: { enable: true, mode: "repulse" },
    },
  },
});

