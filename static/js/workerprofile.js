 /* Education pop up */
 function openEduModal() {
    document.getElementById("educationModal").style.display = "flex";
  }
  
  function closeEduModal() {
    document.getElementById("educationModal").style.display = "none";
  }
  
  document.getElementById("educationForm").addEventListener("submit", function(e) {
    e.preventDefault();
  
    const formData = new FormData(this);
  
    fetch("/worker/add-education", {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Education added successfully");
        location.reload();
      } else {
        alert("Failed to add education");
      }
    });
  });
  

/* Certificate pop up */

  function openCertModal() {
    document.getElementById("certModal").style.display = "flex";
  }
  function closeCertModal() {
    document.getElementById("certModal").style.display = "none";
  }
  
/* Experiencce pop up*/
  function openExpModal() {
    document.getElementById("experienceModal").style.display = "flex";
  }
  
  function closeExpModal() {
    document.getElementById("experienceModal").style.display = "none";
  }
  
  // Disable end date if currently working
  document.getElementById("currentlyWorking").addEventListener("change", function () {
    const endDate = document.querySelector('input[name="end_date"]');
    endDate.disabled = this.checked;
    if (this.checked) endDate.value = "";
  });
  
  // Submit experience
  document.getElementById("experienceForm").addEventListener("submit", function (e) {
    e.preventDefault();
  
    const formData = new FormData(this);
  
    fetch("/worker/add-experience", {
      method: "POST",
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Work experience added successfully");
        location.reload();
      } else {
        alert(data.message || "Failed to add experience");
      }
    });
  });
  
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
        
            fetch("/worker/update-profile", {
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
       
        /* worker documents section */
            function scrollToKYC() {
              const section = document.getElementById("kyc-section");
            
              fetch("/worker/start-kyc");
              
              section.style.display = "block";
              section.style.opacity = 0;
            
              section.scrollIntoView({ behavior: "smooth" });
            
              let opacity = 0;
              const fadeIn = setInterval(() => {
                opacity += 0.05;
                section.style.opacity = opacity;
                if (opacity >= 1) clearInterval(fadeIn);
              }, 20);
            }
           

              function showChangeForm(id) {
                const form = document.getElementById(id);
                if (!form) return;
              
                // Toggle visibility
                form.style.display = (form.style.display === "flex") ? "none" : "flex";
              }
              
                function toggleProfileEdit(editMode) {
                  document.getElementById("profile-view").style.display =
                    editMode ? "none" : "block";
                  document.getElementById("profile-edit").style.display =
                    editMode ? "block" : "none";
                }
            
        
                function enableEdit() {
                  toggleFields(true);
                }
              
                function cancelEdit() {
                  toggleFields(false);
                }
              
                function toggleFields(editMode) {
                  document.querySelectorAll(".view-field").forEach(el => {
                    el.style.display = editMode ? "none" : "inline";
                  });
              
                  document.querySelectorAll(".edit-field").forEach(el => {
                    el.style.display = editMode ? "inline-block" : "none";
                  });
              
                  document.getElementById("editBtn").style.display =
                    editMode ? "none" : "inline-block";
                  document.getElementById("saveBtn").style.display =
                    editMode ? "inline-block" : "none";
                  document.getElementById("cancelBtn").style.display =
                    editMode ? "inline-block" : "none";
                }
              
                function saveProfile() {
                  fetch("/worker/update-profile", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                      "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                      username: document.getElementById("e-username").value,
                      email: document.getElementById("e-email").value,
                      phone_no: document.getElementById("e-phone").value
                    })
                  })
                  .then(res => res.json())
                  .then(data => {
                    console.log("Server response:", data);
                    if (data.success) {
                      document.getElementById("v-username").innerText = data.username;
                      document.getElementById("v-email").innerText = data.email;
                      document.getElementById("v-phone").innerText = data.phone_no;
        
                      toggleFields(false);
                    } else {
                      alert(data.message || "Update failed");
                   }
                  })
                  .catch(err => {
                    console.error("Fetch error:", err);
                    alert("Server error");
                  });
                }


                function editApplication(id, skill, location) {
                  document.getElementById("application_id").value = id;
                  document.getElementById("applicant_skill").value = skill;
                  document.getElementById("applicant_location").value = location;
                  document.getElementById("editApplicationModal").style.display = "flex";
                }
                
                function closeAppModal() {
                  document.getElementById("editApplicationModal").style.display = "none";
                }
                