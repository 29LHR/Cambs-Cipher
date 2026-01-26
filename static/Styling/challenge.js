function toggleTips() {
        const content = document.getElementById("tips-content");
        const button = document.querySelector(".tips-toggle");
        if (content.style.display === "none" || content.style.display === "") {
          content.style.display = "block";
          button.classList.add("open");
        } else {
          content.style.display = "none";
          button.classList.remove("open");
        }
      }

      function toggleBonuses() {
        const content = document.getElementById("bonuses-content");
        const button = document.querySelector(".bonuses-toggle");
        if (content.style.display === "none" || content.style.display === "") {
          content.style.display = "block";
          button.classList.add("open");
        } else {
          content.style.display = "none";
          button.classList.remove("open");
        }
      }