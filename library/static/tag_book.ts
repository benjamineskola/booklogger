function TagBook(): Record<string, Function> {
  async function addTag(
    this: HTMLFormElement,
    event: Event
  ): Promise<Response | null> {
    event.preventDefault();
    const url = this.getAttribute('action');

    if (url === null) {
      return null;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(
        new FormData(this) as unknown as URLSearchParams
      ).toString()
    });

    if (response.ok) {
      const tagsField = this.closest('.tags');
      const inputField: HTMLInputElement | null =
        this.querySelector('input[name="tags"]');
      const data = await response.json();

      if (tagsField !== null) {
        for (const [_, tag] of Object.entries(data.tags)) {
          const template = document.createElement('template');
          template.innerHTML = `<span class="badge bg-secondary"><a href="/tag/${tag}">${tag}</a></span> `;
          tagsField.prepend(template.content);
        }
      }
      if (inputField !== null) {
        inputField.value = '';
      }
      this.style.display = 'none';
    }

    return response;
  }

  function init(body: HTMLElement): void {
    body.querySelectorAll('a.remove-tag').forEach((el) => {
      el.addEventListener('click', () => {
        void removeTag.call(el as HTMLElement);
      });
    });

    body.querySelectorAll('form.add-tag').forEach((el) => {
      el.addEventListener('submit', (ev) => {
        void addTag.call(el as HTMLFormElement, ev);
      });
    });
  }

  async function removeTag(this: HTMLElement): Promise<Response | null> {
    const tag = this.dataset.tag;
    const label = this.parentElement;

    if (tag === null || label === null || label.parentElement === null) {
      return null;
    }

    const book = label.parentElement.dataset.book;
    const token: HTMLInputElement | null = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    );

    if (book === undefined || token === null) {
      return null;
    }

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

    return response;
  }

  return { init };
}

export default TagBook;
export { TagBook };
