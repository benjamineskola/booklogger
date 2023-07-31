function ProgressBar() {
  async function updateProgress(event) {
    event.preventDefault();

    const book = this.dataset.book;
    const url = this.getAttribute('action');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this)).toString()
    });

    if (response.ok) {
      const data = await response.json();
      const bookCard = document.querySelector(`#book-${book}`);
      const progressBar = bookCard.querySelector('.progress-bar');
      progressBar.style.width = `${data.percentage}%`;

      console.log(data);
      let progressText = bookCard.querySelector('.card-footer .progress-date');
      if (
        progressText.textContent === null ||
        progressText.textContent?.length === 0
      ) {
        progressText = bookCard.querySelector('.card-footer .read-dates');
        progressText.textContent = `${progressText.textContent}; ${data.progress_text}`;
      } else {
        progressText.textContent = data.progress_text;
      }

      this.querySelector('input[name="value"]').value = '';
    }

    return response;
  }

  function init(body) {
    body.querySelectorAll('form.update-progress').forEach((el) => {
      el.addEventListener('submit', (ev) => {
        void updateProgress.call(el, ev);
      });
    });
  }

  return { init };
}

export default ProgressBar;
export { ProgressBar };
