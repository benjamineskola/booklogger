function TagBook() {
  async function addTag(event) {
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
      body: new URLSearchParams(new FormData(this)).toString()
    });

    if (response.ok) {
      const tagsField = this.closest('.tags');
      const inputField = this.querySelector('input[name="tags"]');
      const data = await response.json();

      if (tagsField !== null) {
        for (const [_, tag] of Object.entries(data.tags)) {
          const template = document.createElement('template');
          template.innerHTML = `<span class="badge bg-secondary"><a href="/tag/${tag}">${tag}</a></span> `;
          tagsField.prepend(template.content);
        }

        for (const [_, tag] of Object.entries(tagsField.children)) {
          if (tag.textContent && tag.textContent.trim() === 'untagged') {
            tag.remove();
            break;
          }
        }
      }
      if (inputField !== null) {
        inputField.value = '';
      }
      this.classList.remove('show');
    }

    return response;
  }

  function init(body) {
    body.querySelectorAll('a.remove-tag').forEach((el) => {
      el.addEventListener('click', () => {
        void removeTag.call(el);
      });
    });

    body.querySelectorAll('form.add-tag').forEach((el) => {
      el.addEventListener('submit', (ev) => {
        void addTag.call(el, ev);
      });
    });
  }

  async function removeTag() {
    const tag = this.dataset.tag;
    const label = this.parentElement;

    if (tag === null || label === null || label.parentElement === null) {
      return null;
    }

    const book = label.parentElement.dataset.book;
    const token = document.querySelector('[name=csrfmiddlewaretoken]');

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
