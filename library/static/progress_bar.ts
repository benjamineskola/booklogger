function ProgressBar(): any {
  async function markFinished(
    this: HTMLFormElement,
    event: Event
  ): Promise<any> {
    event.preventDefault();
    const book = this.dataset.book!;
    const url = this.getAttribute('action')!;
    console.log(book, url);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this) as any).toString()
    });

    if (response.ok) {
      const bookCard = document.querySelector(`#book-${book}`)!;
      const progressText: HTMLElement = bookCard.querySelector(
        '.card-footer .progress-date'
      )!;

      const startField = bookCard.querySelector('.read-dates')!;
      const startDate = startField.querySelector('time')!;
      console.log(startDate);
      startField.textContent = 'Read ';
      startField.appendChild(startDate);
      progressText.textContent = ' – now';

      const progressBar = bookCard.querySelector('.progress')!;
      progressBar.remove();
      this.remove();
      const toggle: HTMLElement = bookCard.querySelector('.dropdown-toggle')!;
      toggle.click();
    }
  }

  function init(body: HTMLElement): void {
    body.querySelectorAll('form.finish').forEach((el) => {
      el.addEventListener('submit', (ev) => {
        void markFinished.call(el as HTMLFormElement, ev);
      });
    });
  }

  return { init };
}

export default ProgressBar;
export { ProgressBar };
