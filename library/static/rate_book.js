function RateBook () {
  /** @this HTMLElement  */
  async function rateBook () {
    let value = Number(this.dataset.rating);
    const ratings = this.parentElement;

    if (!ratings) {
      return;
    }

    const book = ratings.dataset.book;
    const oldRating = Number(ratings.dataset.rating);

    if (oldRating === value) {
      value = value - 0.5;
    } else if (oldRating === value - 0.5) {
      value = 0;
    }

    /** @type HTMLInputElement | null */
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!token) {
      return;
    }

    const response = await fetch(`/book/${book}/rate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': token.value
      },
      body: `rating=${Number(value)}`
    });

    if (response.ok) {
      ratings.dataset.rating = String(value);
      Array.from(ratings.children).forEach(function (star, i) {
        if (value >= i + 1) {
          star.textContent = '★';
        } else if (value - i === 0.5) {
          star.textContent = '½';
        } else {
          star.textContent = '☆';
        }
      });
    }
  }

  /** @param {HTMLElement} body */
  function init (body) {
    body.querySelectorAll('span.rating-star').forEach(el => {
      el.addEventListener('click', rateBook);
    });
  }

  return {
    init
  };
}

export default RateBook;
export { RateBook };
