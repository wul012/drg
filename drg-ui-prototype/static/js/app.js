document.addEventListener('DOMContentLoaded', () => {
    const flashes = Array.from(document.querySelectorAll('.flash'));
    if (flashes.length > 0) {
        window.setTimeout(() => {
            flashes.forEach((item) => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(-4px)';
                item.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                window.setTimeout(() => item.remove(), 250);
            });
        }, 2600);
    }
});
