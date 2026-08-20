const navButtons = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');

function showPage(pageId) {
  navButtons.forEach((button) => {
    const isActive = button.dataset.page === pageId;
    button.classList.toggle('active', isActive);
  });

  pages.forEach((page) => {
    const isVisible = page.id === `${pageId}-page`;
    page.classList.toggle('hidden', !isVisible);
    page.classList.toggle('active', isVisible);
  });
}

navButtons.forEach((button) => {
  button.addEventListener('click', () => showPage(button.dataset.page));
});
