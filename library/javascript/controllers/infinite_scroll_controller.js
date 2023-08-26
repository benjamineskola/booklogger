import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  static values = {
    url: String,
    year: Number
  };

  async connect() {
    const year = this.yearValue;
    const url = this.urlValue;
    const response = await fetch(url);

    if (response.ok) {
      const data = await response.text();
      const elem = document.createElement('div');
      elem.innerHTML = data.trim();
      const body = elem.querySelector('main');
      this.element.parentElement?.insertAdjacentElement('afterend', body);
      this.element.remove();

      if (document.updateScrollPosition === undefined) {
        document.addEventListener('scroll', this.updateScrollPosition);
        document.updateScrollPosition = true;
      }
    } else {
      this.element.querySelector('.spinner-grow').classList.add('d-none');
      this.element.querySelector('.alert-danger').classList.remove('d-none');
    }
  }

  updateScrollPosition(event) {
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
}
