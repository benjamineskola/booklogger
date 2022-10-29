function RateBook (): any {
  async function rateBook (this: HTMLElement): Promise<Response> {
    let value = Number(this.dataset.rating);
    const ratings = this.parentElement!;
    const book = ratings.dataset.book!;
    const oldRating = Number(ratings.dataset.rating);

    if (oldRating === value) {
      value = value - 0.5;
    } else if (oldRating === value - 0.5) {
      value = 0;
    }

    const token: HTMLInputElement = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )!;

    displayRating(ratings, value);
    const response = await fetch(`/book/${book}/rate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': token.value
      },
      body: `rating=${value}`
    });

    if (!response.ok) {
      displayRating(ratings, oldRating);
    }

    return response;
  }

  function displayRating (parent: HTMLElement, value: number): void {
    parent.dataset.rating = String(value);
    Array.from(parent.children).forEach(function (star, i) {
      if (value >= i + 1) {
        star.textContent = '★';
      } else if (value - i === 0.5) {
        star.textContent = '½';
      } else {
        star.textContent = '☆';
      }
    });
  }

  function init (body: HTMLElement): any {
    body.querySelectorAll('span.rating-star').forEach(el => {
      // eslint-disable-next-line @typescript-eslint/no-misused-promises
      el.addEventListener('click', rateBook);
    });
  }

  return { init };
}

export default RateBook;
export { RateBook };
