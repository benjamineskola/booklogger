function TagBook () {
  async function addTag (this: HTMLFormElement, event: Event) {
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
      const tagsField = $(this.dataset.tags!);
      const inputField: HTMLInputElement = this.querySelector(
        'input[name="tags"]'
      )!;
      const data = await response.json();

      for (const i in data.tags) {
        const newTag = data.tags[i];
        tagsField.prepend(
          `<span class="badge badge-secondary"><a href="/tag/${newTag}">${newTag}</a></span> `
        );
      }
      inputField.value = '';
      this.style.display = 'none';
    }
  }

  function init (body: HTMLElement) {
    body.querySelectorAll('a.remove-tag').forEach(el => {
      el.addEventListener('click', removeTag);
    });

    body.querySelectorAll('form.add-tag').forEach(el => {
      el.addEventListener('submit', addTag);
    });
  }

  async function removeTag (this: HTMLElement) {
    const tag = this.dataset.tag;
    const label = this.parentElement!;
    const book = label.parentElement!.dataset['book'];
    const token: HTMLInputElement = document.querySelector(
      '[name=csrfmiddlewaretoken]'
    )!;

    if (!confirm(`Remove tag ${tag}?`)) {
      return false;
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

  return { init };
}

export default TagBook;
export { TagBook };
