import { Controller } from '@hotwired/stimulus';

export default class extends Controller {
  connect() {
    document
      ?.querySelector('#card-bookauthor_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        this.addAuthorField(ev, document.bookauthor_formset_template);
      });

    document
      ?.querySelector('#card-readinglistentry_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        this.addListEntryField(ev, document.listentry_formset_template);
      });

    for (const elementId of ['acquired', 'alienated', 'ebook_acquired']) {
      this.addSetDateTodayButton(elementId);
    }
    this.isbnFieldPasteFilter('#id_isbn');
    this.isbnFieldPasteFilter('#id_ebook_isbn');

    const deleteButton = document.querySelector(
      `.form-check-input[name$="DELETE"]`
    );
    deleteButton.addEventListener('click', function (event) {
      deleteButton.closest('.form-inline').style.display = 'none';
    });

    if (document.formTags !== null) {
      const el = document.querySelector('#id_tags');
      el.value = document.formTags;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
  addAuthorField(event, template) {
    event.preventDefault();

    const parent = document.querySelector('#formset-bookauthor_set');
    const totalForms = document.querySelector(
      'input[name="bookauthor_set-TOTAL_FORMS"]'
    );
    const index = totalForms?.value;

    const inlineForm = this.createElements('<div class="form-inline"></div>');
    const selectForm = this.createElements(
      template.replace(/__prefix__/g, index)
    );
    const selectField = selectForm.querySelector('select');

    const authorFormGroup = this.createElements(
      '<div class="form-group"></div>'
    );
    authorFormGroup.append(
      this.createElements(
        `<label for="id_bookauthor_set-${index}-author" class="mr-2 requiredField">Author*</label>`
      )
    );
    const selectDiv = this.createElements('<div class="mr-2 mt-2"></div>');
    selectDiv.append(selectField);
    authorFormGroup.append(selectDiv);
    inlineForm.append(authorFormGroup);

    inlineForm.append(
      this.createElements(
        `<div class="form-group"><label for="bookauthor_set-${index}-role" class="mr-2">Role</label><div class="mr-2 mt-2"><input type="text" name="bookauthor_set-${index}-role" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      this.createElements(
        `<div class="form-group"><label for="bookauthor_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="bookauthor_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      this.createElements(
        `<div class="form-group"><div class="mr-2 mt-2"><div class="form-check"><input type="checkbox" name="bookauthor_set-${index}-DELETE" class="checkboxinput form-check-input" id="id_bookauthor_set-${index}-DELETE"><label for="id_bookauthor_set-${index}-DELETE" class="form-check-label">Delete </label></div></div></div>`
      )
    );

    parent.append(inlineForm);
    totalForms.value = String(parseInt(index) + 1);

    $(selectField).select2({ theme: 'bootstrap', tags: true });
    const checkbox = inlineForm.querySelector('.form-check-input');
    checkbox.addEventListener('click', function (event) {
      const form = checkbox.closest('.form-inline');
      form.style.display = 'none';
    });
  }

  addListEntryField(event, template) {
    event.preventDefault();

    const parent = document.querySelector('#formset-readinglistentry_set');
    const totalForms = document.querySelector(
      'input[name="readinglistentry_set-TOTAL_FORMS"]'
    );
    const index = totalForms.value;

    const inlineForm = this.createElements('<div class="form-inline"></div>');

    const selectForm = this.createElements(
      template.replace(/__prefix__/g, index)
    );
    const selectField = selectForm.querySelector('select');

    const authorFormGroup = this.createElements(
      '<div class="form-group"></div>'
    );
    authorFormGroup.append(
      `<label for="id_readinglistentry_set-${index}-reading_list}" class="mr-2 requiredField">Reading list*</label>`
    );
    const selectDiv = this.createElements('<div class="mr-2 mt-2"></div>');
    selectDiv.append(selectField);
    authorFormGroup.append(selectDiv);
    inlineForm.append(authorFormGroup);

    inlineForm.append(
      this.createElements(
        `<div class="form-group"><label for="readinglistentry_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="readinglistentry_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_readinglistentry_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      this.createElements(
        `<div class="form-group"><div class="mr-2 mt-2"><div class="form-check"><input type="checkbox" name="readinglistentry_set-${index}-DELETE" class="checkboxinput form-check-input" id="id_readinglistentry_set-${index}-DELETE"><label for="id_readinglistentry_set-${index}-DELETE" class="form-check-label">Delete </label></div></div></div>`
      )
    );

    parent.append(inlineForm);
    totalForms.value = index + 1;

    $(selectField).select2({ theme: 'bootstrap' });
    const checkbox = inlineForm.querySelector('.form-check-input');
    checkbox.addEventListener('click', function (event) {
      const form = checkbox.closest('.form-inline');
      form.style.display = 'none';
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
