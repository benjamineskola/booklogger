function ProgressBar(): any {
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

      console.log(data);
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
        progressText.textContent = data.progress_text;
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
  }

  return { init };
}

export default ProgressBar;
export { ProgressBar };
