import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  static targets = ['ratings'];

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
}
