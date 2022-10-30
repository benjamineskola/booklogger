function StatsLoader (): any {
  function loadStatsForYear (element: HTMLElement): void {
    const year: string = element.dataset.year!;

    fetch(`/stats/${year}`)
      .then(response => {
        const spinner: HTMLElement = element.querySelector('.spinner-grow')!;
        spinner.style.display = '';

        if (response.ok) {
          response
            .text()
            .then(html => {
              element.innerHTML = html;
            })
            .catch(err => {
              console.log(err);
            });
        } else {
          throw new Error();
        }
      })
      .catch(() => {
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
          ?.addEventListener('click', function () {
            element.innerHTML = `
              <div id="loading-stats-${year}" class="spinner-grow mb-4" role="status">
                <span class="sr-only">Loading...</span>
              </div>`;
            return loadStatsForYear(element);
          });
      });
  }

  function init (): any {
    document.querySelectorAll('div.stats-for-year').forEach(el => {
      loadStatsForYear(el as HTMLElement);
    });
  }

  return { init };
}

export default StatsLoader;
export { StatsLoader };
