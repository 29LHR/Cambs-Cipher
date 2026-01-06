(function () {
        const btn = document.querySelector(".menu-toggle");
        const nav = document.getElementById("primary-nav");
        if (!btn || !nav) return;

        const closeMenu = () => {
          btn.setAttribute("aria-expanded", "false");
          nav.classList.remove("open");
        };

        const openMenu = () => {
          btn.setAttribute("aria-expanded", "true");
          nav.classList.add("open");
        };

        btn.addEventListener("click", () => {
          const expanded = btn.getAttribute("aria-expanded") === "true";
          if (expanded) {
            closeMenu();
          } else {
            openMenu();
          }
        });

        // Close the menu when a link is clicked (useful on mobile)
        nav.addEventListener("click", (e) => {
          const target = e.target;
          if (target && target.tagName === "A") {
            closeMenu();
          }
        });

        // Close on Escape key
        document.addEventListener("keydown", (e) => {
          if (e.key === "Escape") closeMenu();
        });
      })();