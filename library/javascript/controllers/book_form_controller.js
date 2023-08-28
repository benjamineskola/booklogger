import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  connect() {
    document
      ?.querySelector('#card-bookauthor_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        this.addInlineForm(
          ev,
          document.bookauthor_formset_template,
          'bookauthor_set'
        );
      });

    document
      ?.querySelector('#card-readinglistentry_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        this.addInlineForm(
          ev,
          document.listentry_formset_template,
          'readinglistentry_set'
        );
      });

    for (const elementId of ['acquired', 'alienated', 'ebook_acquired']) {
      this.addSetDateTodayButton(elementId);
    }

    this.isbnFieldPasteFilter('#id_isbn');
    this.isbnFieldPasteFilter('#id_ebook_isbn');

    document
      .querySelectorAll('input[type="checkbox"][name$="DELETE"]')
      .forEach((deleteButton) => {
        deleteButton.addEventListener('click', this.removeInlineForm);
      });

    $('select').select2({ theme: 'bootstrap' });
    $('#id_tags').select2({ theme: 'bootstrap', tags: true });

    if (document.formTags !== null) {
      const el = document.querySelector('#id_tags');
      el.value = document.formTags;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  addInlineForm(event, template, identifier) {
    event.preventDefault();

    const parent = document.querySelector(`#formset-${identifier}`);
    const totalForms = document.querySelector(
      `input[name="${identifier}-TOTAL_FORMS"]`
    );
    const index = Number(totalForms.value);

    const inlineForm = this.createElements(
      `<div class="inline-form">${template.replace(/__prefix__/g, index)}</div>`
    );
    parent.append(inlineForm);
    totalForms.value = index + 1;

    inlineForm
      .querySelectorAll('input[type="checkbox"][name$="DELETE"]')
      .forEach((deleteButton) => {
        deleteButton.addEventListener('click', this.removeInlineForm);
      });

    inlineForm
      .querySelectorAll('input[type="text"], input[type="number"]')
      .forEach((inputField) => {
        inputField.classList.add('form-control');
      });
    inlineForm.querySelectorAll('select').forEach((selectField) => {
      $(selectField).select2({ theme: 'bootstrap', tags: true });
    });
  }

  addSetDateTodayButton(elementId) {
    const template = document.createElement('template');
    template.innerHTML = `<a href="#" id="${elementId}_date_set_today" data-action="book-form#setDateToday" data-book-form-element-id-param="${elementId}">Set to today</a>`;

    document
      .querySelector(`#div_id_${elementId}_date`)
      ?.append(template.content.children[0]);
  }

  createElements(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.children[0];
  }

  isbnFieldPasteFilter(selector) {
    const element = document.querySelector(selector);
    element.addEventListener('paste', function (ev) {
      ev.preventDefault();
      const pastedText = ev.clipboardData?.getData('text/plain');
      this.value = pastedText?.replace(/\D/g, '') ?? '';
    });

    element.addEventListener('input', function (ev) {
      ev.preventDefault();
      this.value = this.value.replace(/\D/g, '');
    });
  }

  removeInlineForm(event) {
    event.target.closest('.inline-form').remove();
  }

  setDateToday(event) {
    event.preventDefault();
    const elementId = event.params.elementId;

    const date = new Date();

    const monthField = document.querySelector(`#id_${elementId}_date_month`);
    monthField.value = String(date.getMonth() + 1);
    monthField.dispatchEvent(new Event('change', { bubbles: true }));

    const yearField = document.querySelector(`#id_${elementId}_date_year`);
    yearField.value = String(date.getFullYear());
    yearField.dispatchEvent(new Event('change', { bubbles: true }));

    const dayField = document.querySelector(`#id_${elementId}_date_day`);
    dayField.value = String(date.getDate());
    dayField.dispatchEvent(new Event('change', { bubbles: true }));
  }
}
