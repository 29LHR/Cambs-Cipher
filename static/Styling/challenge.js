(function () {
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

  // Attach event listeners when DOM is ready
  document.addEventListener("DOMContentLoaded", function () {
    const tipsButton = document.querySelector(".tips-toggle");
    const bonusesButton = document.querySelector(".bonuses-toggle");

    if (tipsButton) {
      tipsButton.addEventListener("click", toggleTips);
    }

    if (bonusesButton) {
      bonusesButton.addEventListener("click", toggleBonuses);
    }

    // Close dropdowns when clicking outside
    document.addEventListener("click", function (e) {
      const tipsContent = document.getElementById("tips-content");
      const bonusesContent = document.getElementById("bonuses-content");

      if (tipsButton && tipsContent && !e.target.closest(".tips-section")) {
        tipsContent.style.display = "none";
        tipsButton.classList.remove("open");
      }

      if (bonusesButton && bonusesContent && !e.target.closest(".tips-section")) {
        bonusesContent.style.display = "none";
        bonusesButton.classList.remove("open");
      }
    });
  });
})();