const filterBtn = document.getElementById("filterToggle");
const filterGrid = document.querySelector(".filter-grid");
const filterIcon = document.getElementById("filterIcon");

filterBtn.addEventListener("click", () => {
  filterGrid.classList.toggle("open");
  filterIcon.classList.toggle("rotate");
});


// APPLY FILTERS
function applyFilters() {
  const params = new URLSearchParams();

  const category = document.getElementById("categoryFilter")?.value;
  const distance = document.getElementById("distanceFilter")?.value;
  const city = document.getElementById("cityFilter")?.value;
  const shift = document.getElementById("shiftFilter")?.value;
  const salary = document.getElementById("salaryFilter")?.value;
  const openings = document.getElementById("openingFilter")?.value;

  if (category) params.append("category", category);
  if (distance) params.append("distance", distance);
  if (city) params.append("city", city);
  if (shift) params.append("shift", shift);
  if (salary && salary !== "Any") params.append("salary", salary);
  if (openings && openings !== "Any") params.append("openings", openings);

  window.location.href = `/jobportal?${params.toString()}`;
}

document
  .getElementById("applyFiltersBtn")
  ?.addEventListener("click", applyFilters);

  document
  .getElementById("applyFiltersBtn")
  ?.addEventListener("click", () => {
    applyFilters();
    filterGrid.classList.remove("open");
    filterIcon.classList.remove("rotate");
  });

// CLEAR FILTERS
document.querySelector(".clear-btn")?.addEventListener("click", () => {
  window.location.href = "/jobportal";
});
