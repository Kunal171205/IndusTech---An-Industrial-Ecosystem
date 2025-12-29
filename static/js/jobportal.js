const filterBtn = document.getElementById("filterToggle");
const filterPanel = document.getElementById("filterPanel");
const filterIcon = document.getElementById("filterIcon");

filterBtn.addEventListener("click", () => {
  filterPanel.classList.toggle("open");
  filterIcon.classList.toggle("rotate");
});
const jobCards = document.querySelectorAll(".job-card");
const categoryChips = document.querySelectorAll("[data-category]");
const distanceChips = document.querySelectorAll("[data-distance]");

let selectedCategories = new Set();
let selectedDistances = new Set();

/* CATEGORY MULTI SELECT */
categoryChips.forEach(chip => {
  chip.addEventListener("click", () => {
    chip.classList.toggle("active");

    const category = chip.dataset.category;
    chip.classList.contains("active")
      ? selectedCategories.add(category)
      : selectedCategories.delete(category);

    applyFilters();
  });
});

/* DISTANCE MULTI SELECT */
distanceChips.forEach(chip => {
  chip.addEventListener("click", () => {
    chip.classList.toggle("active");

    const distance = Number(chip.dataset.distance);
    chip.classList.contains("active")
      ? selectedDistances.add(distance)
      : selectedDistances.delete(distance);

    applyFilters();
  });
});

/* APPLY FILTERS */
function applyFilters() {
  jobCards.forEach(card => {
    const jobCategory = card.dataset.category;
    const jobDistance = Number(card.dataset.distance);

    const categoryMatch =
      selectedCategories.size === 0 ||
      selectedCategories.has(jobCategory);

    const distanceMatch =
      selectedDistances.size === 0 ||
      [...selectedDistances].some(d => jobDistance <= d);

    if (categoryMatch && distanceMatch) {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  });

  updateJobCount();
}

/* UPDATE JOB COUNT */
function updateJobCount() {
  const visibleJobs = [...jobCards].filter(
    card => card.style.display !== "none"
  );
  document.querySelector(".jobs-header h3").innerText =
    `${visibleJobs.length} Jobs Found`;
}

/* INITIAL LOAD */
applyFilters();

document.getElementById("clearFilters").addEventListener("click", () => {
    selectedCategories.clear();
    selectedDistances.clear();
  
    document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    applyFilters();
  });
  