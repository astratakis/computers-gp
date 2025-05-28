document.addEventListener("DOMContentLoaded", function () {
  const logoutBtn = document.getElementById("logout-btn");

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async function (event) {
      event.preventDefault(); // Prevent the default link behavior

      try {
        const response = await fetch("/logout", {
          method: "POST",
          credentials: "same-origin", // Ensures cookies are sent with the request
        });

        // Check if the response triggers a redirect.
        if (response.redirected) {
          window.location.href = response.url; // Redirect to the login page after logout
        }
      } catch (error) {
        console.error("Error during logout:", error);
      }
    });
  } else {
    console.warn("Logout button not found in the document.");
  }
});
