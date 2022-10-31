import { ProgressBar } from './progress_bar.js';
import { RateBook } from './rate_book.js';
import { TagBook } from './tag_book.js';

function InfiniteScroll (): any {
  async function loadNextPage (year: string, url: string): Promise<void> {
    const placeholder = document.querySelector('.loader')!;
    const response = await fetch(url);

    if (response.ok) {
      const data = await response.text();
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
        void loadNextPage(nextYear, nextUrl);
      }
    } else {
      (placeholder.querySelector(
        '.spinner-grow'
      ) as HTMLElement).style.display = 'none';
      (placeholder.querySelector(
        '.alert-danger'
      ) as HTMLElement).style.display = '';
    }
  }

  function updateScrollPosition (this: HTMLElement): void {
    Array.from(document.querySelectorAll('h2')).forEach(function (el) {
      const height = window.innerHeight;

      const top = window.pageYOffset;
      const offsetTop =
        el.getBoundingClientRect().top +
        top -
        document.documentElement.clientTop;
      const distance = top - offsetTop;

      const hash = el.getAttribute('href');

      if (Math.abs(distance) < height * 0.75) {
        if (window.location.hash !== hash) {
          if (history.pushState !== undefined) {
            history.pushState(null, '', hash);
          } else if (typeof hash !== 'undefined' && hash !== null) {
            window.location.hash = hash;
          }
        }
      } else if (-distance > height && hash === window.location.hash) {
        const year = hash.split('-').pop();
        let newYear;
        if (year === 'sometime') {
          newYear = 2004;
        } else {
          newYear = parseInt(String(year)) + 1;
        }
        const newHash = `#read-${newYear}`;
        if (history.pushState !== undefined) {
          history.pushState(null, '', newHash);
        } else {
          window.location.hash = newHash;
        }
      }
    });
  }

  return { loadNextPage, updateScrollPosition };
}

export default InfiniteScroll;
export { InfiniteScroll };
