document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".btn, .service-card").forEach(el => {
        el.addEventListener("mouseover", () => {
            el.style.transform = "scale(1.1)";
        });
        el.addEventListener("mouseleave", () => {
            el.style.transform = "scale(1)";
        });
    });
});
