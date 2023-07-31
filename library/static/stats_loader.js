function StatsLoader() {
  async function loadStatsForYear(element) {
    const year = element.dataset.year;

    const response = await fetch(`/stats/${year}`);
    if (response.ok) {
      const spinner = element.querySelector('.spinner-grow');
      spinner.style.display = '';
      element.innerHTML = await response.text();
    } else {
      element.innerHTML = `
        <div id="error-${year}" class="alert alert-danger">
          <i class="exclamation circle icon"></i>
          <div class="content">
            <div class="header">Failed to load ${year}.</div>
            <p><span class="btn btn-outline-danger">Retry?</span></p>
          </div>
        </div>`;

      element
        .querySelector(`#error-${year} .btn`)
        ?.addEventListener('click', () => {
          element.innerHTML = `
            <div id="loading-stats-${year}" class="spinner-grow mb-4" role="status">
              <span class="sr-only">Loading...</span>
            </div>`;
          void loadStatsForYear(element);
        });
    }
  }

  function init() {
    document.querySelectorAll('div.stats-for-year').forEach((el) => {
      void loadStatsForYear(el);
    });
  }

  return { init };
}

export default StatsLoader;
export { StatsLoader };
