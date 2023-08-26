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
    } else {
      this.element.querySelector('.spinner-grow').classList.add('d-none');
      this.element.querySelector('.alert-danger').classList.remove('d-none');
    }
  }
}
