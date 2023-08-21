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

  async function updateProgress(
    this: HTMLFormElement,
    event: Event
  ): Promise<any> {
    event.preventDefault();

    const book = this.dataset.book!;
    const url = this.getAttribute('action')!;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this) as any).toString()
    });

    if (response.ok) {
      const data = await response.json();
      const bookCard = document.querySelector(`#book-${book}`)!;
      const progressBar: HTMLElement = bookCard.querySelector('.progress-bar')!;
      progressBar.style.width = `${data.percentage as string}%`;

      let progressText: HTMLElement = bookCard.querySelector(
        '.card-footer .progress-date'
      )!;
      if (
        progressText.textContent === null ||
        progressText.textContent?.length === 0
      ) {
        progressText = bookCard.querySelector('.card-footer .read-dates')!;
        progressText.textContent = `${progressText.textContent!}; ${
          data.progress_text as string
        }`;
      } else {
        progressText.textContent = `; ${data.progress_text}`;
      }

      (this.querySelector('input[name="value"]') as HTMLInputElement).value =
        '';
    }

    return response;
  }

  function init(body: HTMLElement): void {
    body.querySelectorAll('form.update-progress').forEach((el) => {
      el.addEventListener('submit', (ev) => {
        void updateProgress.call(el as HTMLFormElement, ev);
      });
    });
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
