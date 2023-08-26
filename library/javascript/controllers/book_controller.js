import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  static targets = ['ratings', 'updateForm', 'finishForm', 'tags'];

  async addTag(event) {
    event.preventDefault();
    const url = event.target.getAttribute('action');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(event.target)).toString()
    });

    if (response.ok) {
      const inputField = this.tagsTarget.querySelector('input[name="tags"]');
      const data = await response.json();

      for (const [_, tag] of Object.entries(data.tags)) {
        const template = document.createElement('template');
        template.innerHTML = `<span class="badge bg-secondary">
  <a href="/tag/${tag}">${tag}</a>
  <a class="remove-tag" data-tag="${tag}" data-action="book#removeTag">✖</a>
</span> `;
        this.tagsTarget.prepend(template.content);
      }

      for (const [_, tag] of Object.entries(this.tagsTarget.children)) {
        if (tag.textContent && tag.textContent.trim() === 'untagged') {
          tag.remove();
          break;
        }
      }

      inputField.value = '';
      event.target.classList.remove('show');
    }
  }

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

  async markFinished(event) {
    event.preventDefault();
    const url = this.finishFormTarget.getAttribute('action');

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this.finishFormTarget)).toString()
    });

    if (response.ok) {
      const card = document.querySelector(
        `#book-${this.element.dataset.bookId}`
      );
      const progressText = card.querySelector('.card-footer .progress-date');

      const startField = card.querySelector('.read-dates');
      const startDate = startField.querySelector('time');
      startField.textContent = 'Read ';
      startField.appendChild(startDate);
      progressText.textContent = ' – now';

      const progressBar = card.querySelector('.progress');
      progressBar.remove();
      event.target.remove();

      if (card.querySelector('.collapse.show') !== null) {
        const toggle = card.querySelector('.dropdown-toggle');
        toggle.click();
      }
    }
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

  async removeTag(event) {
    const tag = event.target.dataset.tag;
    const label = event.target.parentElement;

    const book = this.element.dataset.book;
    const token = document.querySelector('[name=csrfmiddlewaretoken]');

    if (!confirm(`Remove tag ${tag}?`)) {
      return null;
    }

    const response = await fetch(`/book/${book}/remove_tags/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': token.value
      },
      body: new URLSearchParams({ tags: String(tag) }).toString()
    });

    if (response.ok) {
      label.remove();
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
      const card = document.querySelector(
        `#book-${this.element.dataset.bookId}`
      );
      const progressBar = card.querySelector('.progress-bar');
      progressBar.style.width = `${data.percentage}%`;

      let progressText = card.querySelector('.card-footer .progress-date');
      if (
        progressText.textContent === null ||
        progressText.textContent?.length === 0
      ) {
        progressText = card.querySelector('.card-footer .read-dates');
        progressText.textContent = `${progressText.textContent}; ${data.progress_text}`;
      } else {
        progressText.textContent = `; ${data.progress_text}`;
      }

      this.updateFormTarget.querySelector('input[name="value"]').value = '';
    }

    return response;
  }
}
