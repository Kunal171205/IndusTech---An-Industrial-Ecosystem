
  /* Profit edit pop-up*/
function openEditModal() {
    document.getElementById("editProfileModal").style.display = "flex";
}

function closeEditModal() {
    document.getElementById("editProfileModal").style.display = "none";
}

document.getElementById("editProfileForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    // 🔍 DEBUG — MUST SHOW languages
    console.log("FORM DATA:");
    for (let pair of formData.entries()) {
    console.log(pair[0], pair[1]);
    }

    fetch("/company/update-profile", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Profile updated successfully");
            location.reload();
        } else {
            alert(data.message || "Update failed");
        }
    });
});


  /* Profit contact info edit pop-up*/
  function openContEditModal() {
    document.getElementById("editContProfileModal").style.display = "flex";
}

function closeContEditModal() {
    document.getElementById("editContProfileModal").style.display = "none";
}

document.getElementById("editContProfileForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    // 🔍 DEBUG — MUST SHOW languages
    console.log("FORM DATA:");
    for (let pair of formData.entries()) {
    console.log(pair[0], pair[1]);
    }

    fetch("/company/update-contact", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Profile updated successfully");
            location.reload();
        } else {
            alert(data.message || "Update failed");
        }
    });
});


/* ================= JOB MODAL ================= */

function openJobModal() {
    document.getElementById("jobModal").style.display = "flex";
    document.getElementById("jobModalTitle").innerText = "Post a Job";
    document.querySelector("#jobModal form").reset();
  }
  
  function closeJobModal() {
    document.getElementById("jobModal").style.display = "none";
  }
  
  function toggleOtherJob() {
    const v = document.getElementById("job_type").value;
    document.getElementById("job_type_other").style.display =
      v === "Other" ? "block" : "none";
  }
  
  function toggleOtherShift() {
    const v = document.getElementById("shift").value;
    document.getElementById("shift_other").style.display =
      v === "Other" ? "block" : "none";
  }
  
  function editJob(
    id,
    title,
    jobType,
    city,
    location,
    shift,
    startTime,
    endTime,
    salary,
    openings,
    contact,
    description
  ) {
    document.getElementById("jobModalTitle").innerText = "Edit Job";
  
    document.getElementById("job_id").value = id;
    document.getElementById("job_title").value = title;
    document.getElementById("job_type").value = jobType;
    document.getElementById("city").value = city;
    document.getElementById("specific_location").value = location;
    document.getElementById("shift").value = shift;
    document.getElementById("job_start_time").value = startTime;
    document.getElementById("job_end_time").value = endTime;
    document.getElementById("salary").value = salary;
    document.getElementById("job_opening_no").value = openings;
    document.getElementById("job_contact").value = contact;
    document.getElementById("description").value = description;
  
    document.getElementById("jobModal").style.display = "flex";
  }
  

  /* Profit Trade item form edit pop-up*/
function openTradeEditModal() {
    document.getElementById("editTradeProfileModal").style.display = "flex";
}

function closeTradeEditModal() {
    document.getElementById("editTradeProfileModal").style.display = "none";
}

document.getElementById("editTradeProfileForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    // 🔍 DEBUG — MUST SHOW languages
    console.log("FORM DATA:");
    for (let pair of formData.entries()) {
    console.log(pair[0], pair[1]);
    }

    fetch("/company/additem", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Product Added successfully");
            location.reload();
        } else {
            alert(data.message || "Update failed");
        }
    });
});
