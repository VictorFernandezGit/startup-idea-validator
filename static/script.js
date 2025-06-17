const btn = document.getElementById("analyze-btn");
const resultDiv = document.getElementById("result");
const loading = document.getElementById("loading");

btn.addEventListener("click", () => {
  const idea = document.getElementById("idea").value;
  resultDiv.classList.add("hidden");
  loading.classList.remove("hidden");

  fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  })
    .then(res => res.json())
    .then(data => {
      loading.classList.add("hidden");
      resultDiv.classList.remove("hidden");

      if (data.result) {
        resultDiv.innerText = data.result;
      } else {
        resultDiv.innerText = "⚠️ Error: " + (data.error || "Unknown error.");
      }
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

