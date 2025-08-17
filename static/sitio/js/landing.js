// Mobile menu toggle
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const navMenu = document.getElementById("navMenu");

mobileMenuBtn?.addEventListener("click", () => {
  navMenu.classList.toggle("active");
  const icon = mobileMenuBtn.querySelector("i");
  icon.classList.toggle("fa-bars");
  icon.classList.toggle("fa-times");
});

// Smooth scrolling for internal anchors
document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const href = a.getAttribute("href");
    if (!href || href === "#") return;
    const target = document.querySelector(href);
    if (!target) return;
    e.preventDefault();
    const headerHeight = document.querySelector(".header").offsetHeight;
    const top = target.offsetTop - headerHeight;
    window.scrollTo({ top, behavior: "smooth" });
    navMenu.classList.remove("active");
    const icon = mobileMenuBtn?.querySelector("i");
    if (icon) {
      icon.classList.add("fa-bars");
      icon.classList.remove("fa-times");
    }
  });
});

// Header blur on scroll
window.addEventListener("scroll", () => {
  const header = document.querySelector(".header");
  if (window.scrollY > 100) {
    header.style.background = "rgba(255,255,255,0.95)";
    header.style.backdropFilter = "blur(10px)";
  } else {
    header.style.background = "#fff";
    header.style.backdropFilter = "none";
  }
});

// Stats animation
const statsSection = document.querySelector(".stats");
if (statsSection && "IntersectionObserver" in window) {
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const nums = entry.target.querySelectorAll(".stat-item h3");
        nums.forEach((stat) => {
          const finalText = stat.textContent;
          const isPct = finalText.includes("%");
          const isPlus = finalText.includes("+");
          const number = parseInt(finalText.replace(/[+%,]/g, "")) || 0;
          let current = 0;
          const step = Math.max(1, Math.floor(number / 50));
          const timer = setInterval(() => {
            current += step;
            if (current >= number) {
              current = number;
              clearInterval(timer);
            }
            let display = String(current);
            if (isPlus) display = "+" + display;
            if (isPct) display += "%";
            stat.textContent = display;
          }, 20);
        });
        obs.unobserve(entry.target);
      });
    },
    { threshold: 0.5, rootMargin: "0px 0px -100px 0px" }
  );
  obs.observe(statsSection);
}
