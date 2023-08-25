import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  static targets = ['ratings', 'updateForm'];

  displayRating(value) {
    this.ratingsTarget.dataset.rating = String(value);
    Array.from(this.ratingsTarget.children).forEach(function (star, i) {
      if (value >= i + 1) {
        star.textContent = '★';
      } else if (value - i === 0.5) {
        star.textContent = '½';
      } else {
        star.textContent = '☆';
      }
    });
  }

  async rate(event) {
    let value = Number(event.target.dataset.rating);
    const oldRating = Number(this.ratingsTarget.dataset.rating);

    if (oldRating === value) {
      value = value - 0.5;
    } else if (oldRating === value - 0.5) {
      value = 0;
    }

    const token = document.querySelector('[name=csrfmiddlewaretoken]');

    this.displayRating(value);
    const response = await fetch(`/book/${this.element.dataset.book}/rate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': token.value
      },
      body: `rating=${value}`
    });

    if (!response.ok) {
      this.displayRating(oldRating);
    }
  }

  async updateProgress(event) {
    event.preventDefault();

    const url = this.updateFormTarget.getAttribute('action');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this.updateFormTarget)).toString()
    });

    if (response.ok) {
      const data = await response.json();
      const progressBar = this.element.querySelector('.progress-bar');
      progressBar.style.width = `${data.percentage}%`;

      let progressText = this.element.querySelector(
        '.card-footer .progress-date'
      );
      if (
        progressText.textContent === null ||
        progressText.textContent?.length === 0
      ) {
        progressText = this.element.querySelector('.card-footer .read-dates');
        progressText.textContent = `${progressText.textContent}; ${data.progress_text}`;
      } else {
        progressText.textContent = `; ${data.progress_text}`;
      }

      this.updateFormTarget.querySelector('input[name="value"]').value = '';
    }

    return response;
  }
}
