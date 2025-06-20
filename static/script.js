let selectedMode = "general"; // default

document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    selectedMode = btn.dataset.mode;

    document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  });
});

// Fetch and display saved ideas
function loadIdeas() {
  fetch('/ideas')
    .then(res => res.json())
    .then(data => {
      if (data.ideas) {
        const list = document.getElementById('ideas-list');
        if (!list) return;
        list.innerHTML = '';
        data.ideas.forEach(idea => {
          const li = document.createElement('li');
          // Container for text and delete button
          const textSpan = document.createElement('span');
          textSpan.textContent = idea.content.length > 40 ? idea.content.slice(0, 40) + '...' : idea.content;
          textSpan.title = idea.content;
          textSpan.style.cursor = 'pointer';
          textSpan.addEventListener('click', () => {
            document.getElementById('idea').value = idea.content;
          });

          // Delete button
          const delBtn = document.createElement('button');
          delBtn.textContent = '🗑️';
          delBtn.title = 'Delete idea';
          delBtn.style.marginLeft = '0.5rem';
          delBtn.style.background = 'none';
          delBtn.style.border = 'none';
          delBtn.style.color = '#e2e8f0';
          delBtn.style.cursor = 'pointer';
          delBtn.style.fontSize = '1rem';
          delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Delete this idea?')) {
              fetch(`/delete_idea/${idea.id}`, { method: 'DELETE' })
                .then(res => res.json())
                .then(data => {
                  if (data.success) loadIdeas();
                });
            }
          });

          li.appendChild(textSpan);
          li.appendChild(delBtn);
          list.appendChild(li);
        });
      }
    });
}

// Save idea after analysis
function saveIdea(content) {
  fetch('/save_idea', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      loadIdeas();
    }
  });
}

// On page load, fetch ideas
window.addEventListener('DOMContentLoaded', loadIdeas);

document.getElementById("analyze-btn").addEventListener("click", () => {
  const idea = document.getElementById("idea").value;
  const resultDiv = document.getElementById("result");
  const loading = document.getElementById("loading");

  resultDiv.classList.add("hidden");
  loading.classList.remove("hidden");

  fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({idea,mode:selectedMode})
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      alert(data.error === 'out_of_credits'
        ? "You're out of credits!"
        : "You must be logged in.");
      return;
    }
  
    loading.classList.add("hidden");
    resultDiv.classList.remove("hidden");
    resultDiv.innerHTML = data.result;
    loadIdeas();
  })

  .catch(err => {
    console.error("Error:", err);
    loading.classList.add("hidden");
    resultDiv.classList.remove("hidden");
    resultDiv.innerHTML = "Something went wrong.";
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

