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

// Store the last full output text for export
let lastFullOutputText = '';

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
    // Render structured result as cards with star rating
    const result = data.result;
    if (result && typeof result === 'object' && !Array.isArray(result) && Object.keys(result).length > 1) {
      console.log('GPT result:', result);
      let html = '';
      // Star rating
      if (result.rating) {
        const stars = '★'.repeat(result.rating) + '☆'.repeat(5 - result.rating);
        html += `<div style="font-size:2rem; color:#facc15; margin-bottom:1rem; text-align:center;">${stars}</div>`;
      }
      // Card sections
      const sections = [
        { key: 'summary', label: 'Summary' },
        { key: 'target_audience', label: 'Target Audience' },
        { key: 'value_proposition', label: 'Value Proposition' },
        { key: 'pros_cons', label: 'Pros & Cons' },
        { key: 'competitor_review', label: 'Competitor Review' },
        { key: 'swot', label: 'SWOT Analysis' }
      ];
      html += '<div style="display:flex; flex-wrap:wrap; gap:1rem;">';
      sections.forEach(section => {
        if (result[section.key]) {
          let value = result[section.key];
          if (typeof value === 'object' && value !== null) {
            // Render object as a list
            let listHtml = '<ul style="padding-left:1.2em;">';
            for (const [k, v] of Object.entries(value)) {
              if (Array.isArray(v)) {
                listHtml += `<li><strong>${k[0].toUpperCase() + k.slice(1)}:</strong><ul>`;
                v.forEach(item => {
                  listHtml += `<li>${item}</li>`;
                });
                listHtml += '</ul></li>';
              } else {
                listHtml += `<li><strong>${k[0].toUpperCase() + k.slice(1)}:</strong> ${v}</li>`;
              }
            }
            listHtml += '</ul>';
            value = listHtml;
          }
          html += `<div class="output-card" style="flex:1 1 320px; min-width:260px; max-width:100%;">`
            + `<h3 style='margin-top:0; margin-bottom:0.5rem; color:#38bdf8;'>${section.label}</h3>`
            + `<div>${value}</div>`
            + `</div>`;
        }
      });
      // Startup Path cards (separate for costs and tech stack)
      function renderObjectAsList(obj) {
        let html = '<ul style="padding-left:1.2em;">';
        for (const [k, v] of Object.entries(obj)) {
          if (typeof v === 'object' && v !== null) {
            html += `<li><strong>${k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${renderObjectAsList(v)}</li>`;
          } else {
            html += `<li><strong>${k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong> ${v}</li>`;
          }
        }
        html += '</ul>';
        return html;
      }
      if (result.startup_costs) {
        let startupCostsHtml = '';
        if (typeof result.startup_costs === 'object' && result.startup_costs !== null) {
          if (result.startup_costs.breakdown) {
            startupCostsHtml += renderObjectAsList(result.startup_costs.breakdown);
          }
          if (result.startup_costs.description) {
            startupCostsHtml += `<div style='margin-top:0.5em;'>${result.startup_costs.description}</div>`;
          }
        } else {
          startupCostsHtml = result.startup_costs;
        }
        html += `<div class=\"output-card\" style=\"flex:1 1 320px; min-width:320px; max-width:100%; position:relative;\">
          <h3 style='margin-top:0; margin-bottom:0.5rem; color:#38bdf8;'>Startup Costs</h3>
          <div>${startupCostsHtml || '<span style=\'color:#94a3b8;\'>No data available.</span>'}</div>
        </div>`;
      }
      if (result.tech_stack) {
        let techStackHtml = '';
        if (typeof result.tech_stack === 'object' && result.tech_stack !== null) {
          techStackHtml += renderObjectAsList(result.tech_stack);
        } else {
          techStackHtml = result.tech_stack;
        }
        html += `<div class=\"output-card\" style=\"flex:1 1 320px; min-width:320px; max-width:100%; position:relative;\">
          <h3 style='margin-top:0; margin-bottom:0.5rem; color:#38bdf8;'>Tech Stack</h3>
          <div><span id='tech-stack-text'>${techStackHtml}</span></div>
        </div>`;
      }
      html += '</div>';
      resultDiv.innerHTML = html;
      // Add expand/collapse logic
      const toggle = document.getElementById('startup-path-toggle');
      const content = document.getElementById('startup-path-content');
      const arrow = document.getElementById('startup-path-arrow');
      if (toggle && content && arrow) {
        toggle.addEventListener('click', () => {
          if (content.style.display === 'none') {
            content.style.display = '';
            arrow.innerHTML = '&#9660;';
          } else {
            content.style.display = 'none';
            arrow.innerHTML = '&#9654;';
          }
        });
      }
    } else if (result && result.raw) {
      resultDiv.innerHTML = `<div class="output-card">${result.raw}</div>`;
    } else {
      resultDiv.innerHTML = `<div class="output-card">${result}</div>`;
    }
    // Update credits display
    if (typeof data.remaining_credits !== 'undefined') {
      const creditsSpan = document.querySelector('.text-gray-300');
      if (creditsSpan) {
        creditsSpan.textContent = `Credits: ${data.remaining_credits}`;
      }
    }
    loadIdeas();

    // Save the full output text for export
    if (data && data.result) {
      if (data.result.raw) {
        lastFullOutputText = data.result.raw;
      } else if (typeof data.result === 'object') {
        // Convert the structured result to a readable text
        let text = '';
        if (data.result.summary) text += 'Summary:\n' + data.result.summary + '\n\n';
        if (data.result.target_audience) text += 'Target Audience:\n' + data.result.target_audience + '\n\n';
        if (data.result.value_proposition) text += 'Value Proposition:\n' + data.result.value_proposition + '\n\n';
        if (data.result.pros_cons) {
          text += 'Pros & Cons:\n';
          for (const [k, v] of Object.entries(data.result.pros_cons)) {
            if (Array.isArray(v)) {
              text += k.charAt(0).toUpperCase() + k.slice(1) + ':\n';
              v.forEach(item => { text += '- ' + item + '\n'; });
            } else {
              text += k.charAt(0).toUpperCase() + k.slice(1) + ': ' + v + '\n';
            }
          }
          text += '\n';
        }
        if (data.result.competitor_review) text += 'Competitor Review:\n' + data.result.competitor_review + '\n\n';
        if (data.result.swot) {
          text += 'SWOT Analysis:\n';
          for (const [k, v] of Object.entries(data.result.swot)) {
            if (Array.isArray(v)) {
              text += k.charAt(0).toUpperCase() + k.slice(1) + ':\n';
              v.forEach(item => { text += '- ' + item + '\n'; });
            } else {
              text += k.charAt(0).toUpperCase() + k.slice(1) + ': ' + v + '\n';
            }
          }
          text += '\n';
        }
        if (data.result.rating) text += 'Rating: ' + data.result.rating + ' / 5\n';
        lastFullOutputText = text;
      } else {
        lastFullOutputText = data.result;
      }
    }
  })

  .catch(err => {
    console.error("Error:", err);
    loading.classList.add("hidden");
    resultDiv.classList.remove("hidden");
    resultDiv.innerHTML = "Something went wrong.";
  });
});

// Add export PDF logic
if (window.jsPDF === undefined) {
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
  script.onload = () => { window.jsPDF = window.jspdf.jsPDF; };
  document.head.appendChild(script);
}
document.getElementById('export-pdf-btn').addEventListener('click', function() {
  if (!lastFullOutputText) {
    alert('No analysis to export.');
    return;
  }
  if (!window.jsPDF) {
    alert('PDF library not loaded yet. Please try again in a moment.');
    return;
  }
  const doc = new window.jsPDF();
  const lines = doc.splitTextToSize(lastFullOutputText, 180);
  doc.text(lines, 10, 10);
  doc.save('startup-idea-analysis.pdf');
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

