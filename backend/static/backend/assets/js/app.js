// app.js
document.addEventListener('DOMContentLoaded', () => {
    // 1. Submenu Click Toggle Logic
    const submenuTriggers = document.querySelectorAll('.submenu-trigger');

    submenuTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault(); 
            const wrapper = trigger.nextElementSibling;
            const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

            submenuTriggers.forEach(otherTrigger => {
                otherTrigger.setAttribute('aria-expanded', 'false');
                otherTrigger.nextElementSibling.classList.remove('open');
            });

            trigger.setAttribute('aria-expanded', !isExpanded);
            wrapper.classList.toggle('open', !isExpanded);
        });
    });

    // 2. TRUE URL-Based Active State Logic
    const currentPath = window.location.pathname;
    const allLinks = document.querySelectorAll('.sidebar-link:not(.submenu-trigger), .sidebar-submenu a');

    allLinks.forEach(link => {
        if (link.getAttribute('href') === '#') return;

        const linkPath = new URL(link.href, window.location.origin).pathname;

        if (currentPath === linkPath) {
            document.querySelectorAll('.active').forEach(el => el.classList.remove('active'));
            link.classList.add('active');

            const submenuWrapper = link.closest('.sidebar-submenu-wrapper');
            if (submenuWrapper) {
                submenuWrapper.classList.add('open');
                const parentTrigger = submenuWrapper.previousElementSibling;
                if (parentTrigger && parentTrigger.classList.contains('submenu-trigger')) {
                    parentTrigger.setAttribute('aria-expanded', 'true');
                    parentTrigger.classList.add('active');
                }
            }
        }
    });

    // 3. Mobile Hamburger Menu Logic
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.floating-sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (mobileBtn && sidebar && overlay) {
        // Open sidebar
        mobileBtn.addEventListener('click', () => {
            sidebar.classList.add('sidebar-open');
            overlay.classList.add('show');
        });

        // Close sidebar when clicking outside (on the overlay)
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('sidebar-open');
            overlay.classList.remove('show');
        });
    }
});