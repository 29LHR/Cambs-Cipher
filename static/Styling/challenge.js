(function () {
  function toggleContent(contentId, button) {
    const content = document.getElementById(contentId);
    if (!content || !button) return;

    const isOpen = content.style.display === "block" || content.classList.contains("open");
    if (!isOpen) {
      content.style.display = "block";
      button.classList.add("open");
      content.classList.add("open");
    } else {
      content.style.display = "none";
      button.classList.remove("open");
      content.classList.remove("open");
    }
  }

  // Attach event listeners when DOM is ready
  document.addEventListener("DOMContentLoaded", function () {
    const tipsButton = document.querySelector(".tips-toggle");
    const bonusesButton = document.querySelector(".bonuses-toggle");
    const tipsSection = document.querySelector(".tips-section");
    const bonusesSection = document.querySelector(".bonuses-section");

    if (tipsButton) {
      tipsButton.addEventListener("click", function (e) {
        e.stopPropagation(); // prevent the document click handler from immediately closing it
        toggleContent("tips-content", tipsButton);
      });
    }

    if (bonusesButton) {
      bonusesButton.addEventListener("click", function (e) {
        e.stopPropagation();
        toggleContent("bonuses-content", bonusesButton);
      });
    }

    // Close dropdowns when clicking outside
    document.addEventListener("click", function (e) {
      const tipsContent = document.getElementById("tips-content");
      const bonusesContent = document.getElementById("bonuses-content");

      if (tipsContent && tipsButton && !(e.target.closest && e.target.closest(".tips-section"))) {
        tipsContent.style.display = "none";
        tipsButton.classList.remove("open");
      }

      if (bonusesContent && bonusesButton && !(e.target.closest && e.target.closest(".bonuses-section"))) {
        bonusesContent.style.display = "none";
        bonusesButton.classList.remove("open");
      }
    });

    // Close on Escape key
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        const tipsContent = document.getElementById("tips-content");
        const bonusesContent = document.getElementById("bonuses-content");
        if (tipsContent) {
          tipsContent.style.display = "none";
          if (tipsButton) tipsButton.classList.remove("open");
        }
        if (bonusesContent) {
          bonusesContent.style.display = "none";
          if (bonusesButton) bonusesButton.classList.remove("open");
        }
      }
    });
  });
})();