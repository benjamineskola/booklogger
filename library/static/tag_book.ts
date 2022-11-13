function TagBook(): any {
  async function addTag(this: HTMLFormElement, event: Event): Promise<any> {
    event.preventDefault();
    const url = this.getAttribute('action')!;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(new FormData(this) as any).toString()
    });

    if (response.ok) {
      const tagsField = this.querySelector(this.dataset.tags!)!;
      const inputField: HTMLInputElement =
        this.querySelector('input[name="tags"]')!;
      const data = await response.json();

      for (const i in data.tags) {
        const newTag: string = data.tags[i];
        tagsField.prepend(
          `<span class="badge bg-secondary"><a href="/tag/${newTag}">${newTag}</a></span> `
        );
      }
      inputField.value = '';
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

  async function removeTag(this: HTMLElement): Promise<any> {
    const tag = this.dataset.tag!;
    const label = this.parentElement!;
    const book = label.parentElement!.dataset.book!;
    const token: HTMLInputElement = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )!;

    if (!confirm(`Remove tag ${tag}?`)) {
      return;
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
