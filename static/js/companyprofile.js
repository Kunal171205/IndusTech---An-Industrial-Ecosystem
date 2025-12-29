
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
