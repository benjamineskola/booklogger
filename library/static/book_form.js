function BookForm() {
  function init() {
    document
      ?.querySelector('#card-bookauthor_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        addAuthorField(ev, document.bookauthor_formset_template);
      });

    document
      ?.querySelector('#card-readinglistentry_set .card-footer a')
      ?.addEventListener('click', (ev) => {
        addListEntryField(ev, document.listentry_formset_template);
      });

    for (const elementId of ['acquired', 'alienated', 'ebook_acquired']) {
      addSetDateTodayButton(elementId);
    }

    for (const fieldName of [
      'acquired_date',
      'alienated_date',
      'ebook_acquired_date'
    ]) {
      configureDateFields(fieldName);
    }

    configureSelectFields();

    isbnFieldPasteFilter('#id_isbn');
    isbnFieldPasteFilter('#id_ebook_isbn');

    for (const selector of ['bookauthor', 'logentry', 'readinglistentry']) {
      const input = document.querySelector(
        `#card-${selector}_set .form-check-input`
      );
      input.addEventListener('click', function (event) {
        input.closest('.form-inline').style.display = 'none';
      });
    }

    if (document.formTags !== null) {
      const el = document.querySelector('#id_tags');
      el.value = document.formTags;
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  function addAuthorField(event, template) {
    event.preventDefault();

    const parent = document.querySelector('#formset-bookauthor_set');
    const totalForms = document.querySelector(
      'input[name="bookauthor_set-TOTAL_FORMS"]'
    );
    const index = totalForms?.value;

    const inlineForm = createElements('<div class="form-inline"></div>');
    const selectForm = createElements(template.replace(/__prefix__/g, index));
    const selectField = selectForm.querySelector('select');

    const authorFormGroup = createElements('<div class="form-group"></div>');
    authorFormGroup.append(
      createElements(
        `<label for="id_bookauthor_set-${index}-author" class="mr-2 requiredField">Author*</label>`
      )
    );
    const selectDiv = createElements('<div class="mr-2 mt-2"></div>');
    selectDiv.append(selectField);
    authorFormGroup.append(selectDiv);
    inlineForm.append(authorFormGroup);

    inlineForm.append(
      createElements(
        `<div class="form-group"><label for="bookauthor_set-${index}-role" class="mr-2">Role</label><div class="mr-2 mt-2"><input type="text" name="bookauthor_set-${index}-role" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      createElements(
        `<div class="form-group"><label for="bookauthor_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="bookauthor_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      createElements(
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

  function addListEntryField(event, template) {
    event.preventDefault();

    const parent = document.querySelector('#formset-readinglistentry_set');
    const totalForms = document.querySelector(
      'input[name="readinglistentry_set-TOTAL_FORMS"]'
    );
    const index = totalForms.value;

    const inlineForm = createElements('<div class="form-inline"></div>');

    const selectForm = createElements(template.replace(/__prefix__/g, index));
    const selectField = selectForm.querySelector('select');

    const authorFormGroup = createElements('<div class="form-group"></div>');
    authorFormGroup.append(
      `<label for="id_readinglistentry_set-${index}-reading_list}" class="mr-2 requiredField">Reading list*</label>`
    );
    const selectDiv = createElements('<div class="mr-2 mt-2"></div>');
    selectDiv.append(selectField);
    authorFormGroup.append(selectDiv);
    inlineForm.append(authorFormGroup);

    inlineForm.append(
      createElements(
        `<div class="form-group"><label for="readinglistentry_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="readinglistentry_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_readinglistentry_set-${index}-role"></div></div>`
      )
    );
    inlineForm.append(
      createElements(
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

  function addSetDateTodayButton(elementId) {
    const template = document.createElement('template');
    template.innerHTML = `<a href="#" id="${elementId}_date_set_today">Set to today</a>`;

    document
      .querySelector(`#div_id_${elementId}_date`)
      ?.append(template.content.children[0]);

    document
      .querySelector(`#${elementId}_date_set_today`)
      ?.addEventListener('click', (ev) => {
        setDateToday(ev, elementId);
      });
  }

  function configureDateFields(fieldName) {
    $(`#id_${fieldName}_day`).select2({ theme: 'bootstrap', width: '5em' });
    $(`#id_${fieldName}_month`).select2({ theme: 'bootstrap', width: '9em' });
    $(`#id_${fieldName}_year`).select2({
      theme: 'bootstrap',
      tags: true,
      width: '6em'
    });

    $(`#id_${fieldName}_month`).parent().addClass('form-row');
    $(`#id_${fieldName}_month`)
      .parent()
      .find('span')
      .each(function () {
        $(this).addClass('mr-2');
      });
  }

  function configureSelectFields() {
    $('select').select2({ theme: 'bootstrap' });
    $(
      '#id_first_author, #id_publisher, #id_series, #formset-bookauthor_set select'
    ).select2({
      theme: 'bootstrap',
      tags: true
    });
    $('#id_tags').select2({
      theme: 'bootstrap',
      tags: true,
      tokenSeparators: [',']
    });
  }

  function createElements(html) {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.children[0];
  }

  function isbnFieldPasteFilter(selector) {
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

  function setDateToday(event, elementId) {
    event.preventDefault();

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

  return { init };
}

export default BookForm;
export { BookForm };
