import { ProgressBar } from './progress_bar.js';
import { RateBook } from './rate_book.js';
import { TagBook } from './tag_book.js';

function InfiniteScroll (): any {
  function loadNextPage (year: string, url: string): void {
    const placeholder = document.querySelector('.loader')!;
    fetch(url)
      .then(async response => {
        if (!response.ok) {
          throw new Error();
        }
        return await response.text();
      })
      .then(data => {
        const elem = document.createElement('div');
        elem.innerHTML = data.trim();
        const body = elem.querySelector('main')!;
        placeholder.parentElement?.insertAdjacentElement('afterend', body);
        placeholder.remove();

        const progressBar = ProgressBar();
        progressBar.init(body);
        const rateBook = RateBook();
        rateBook.init(body);
        const tagBook = TagBook();
        tagBook.init(body);

        if (year !== 'sometime') {
          let nextYear = year;
          if (Number(year) > 2010) {
            nextYear = String(Number(year) - 1);
          } else if (year === '2010') {
            nextYear = '2007';
          } else if (year === '2007') {
            nextYear = '2004';
          } else if (year === '2004') {
            nextYear = 'sometime';
          }
          const nextUrl = url.replace(year, String(nextYear));
          loadNextPage(nextYear, nextUrl);
        }
      })
      .catch(() => {
        (placeholder.querySelector(
          '.spinner-grow'
        ) as HTMLElement).style.display = 'none';
        (placeholder.querySelector(
          '.alert-danger'
        ) as HTMLElement).style.display = '';
      });
  }

  return { loadNextPage };
}

export default InfiniteScroll;
export { InfiniteScroll };
