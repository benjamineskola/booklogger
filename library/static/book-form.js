/* globals $ */

$(document).ready(function () {
  configureSelectFields();

  // @ts-ignore
  if (document.formTags !== null) {
    // @ts-ignore
    $('#id_tags').val(document.formTags);
    $('#id_tags').trigger('change');
  }

  for (const fieldName of [
    'acquired_date',
    'alienated_date',
    'ebook_acquired_date'
  ]) {
    configureDateFields(fieldName);
  }

  $('#card-bookauthor_set .card-footer a').on(
    'click',
    // @ts-ignore
    { template: document.bookauthor_formset_template },
    addAuthorField
  );
  $('#card-readinglistentry_set .card-footer a').on(
    'click',
    // @ts-ignore
    { template: document.listentry_formset_template },
    addListEntryField
  );

  $('#card-bookauthor_set, #card-logentry_set, #card-readinglistentry_set')
    .find('.form-check-input')
    .on('click', function (event) {
      $(this)
        .closest('.form-inline')
        .hide(1000);
    });

  for (const elementId of ['acquired', 'alienated', 'ebook_acquired']) {
    addSetDateTodayButton(elementId);
  }

  isbnFieldPasteFilter('#id_isbn, #id_ebook_isbn');
});

/** @param {JQueryEventObject} event */
function addAuthorField (event) {
  event.preventDefault();

  const parent = $('#formset-bookauthor_set');
  const totalForms = $('input[name="bookauthor_set-TOTAL_FORMS"]');
  const index = parseInt(String(totalForms.val()));

  const inlineForm = $('<div class="form-inline"></div>');
  const selectField = $(event.data.template.replace(/__prefix__/g, index)).find(
    'select'
  );

  const authorFormGroup = $('<div class="form-group"></div>');
  authorFormGroup.append(
    `<label for="id_bookauthor_set-${index}-author" class="mr-2 requiredField">Author*</label>`
  );
  const selectDiv = $('<div class="mr-2 mt-2"></div>');
  selectDiv.append(selectField);
  authorFormGroup.append(selectDiv);
  inlineForm.append(authorFormGroup);

  inlineForm.append(
    $(
      `<div class="form-group"><label for="bookauthor_set-${index}-role" class="mr-2">Role</label><div class="mr-2 mt-2"><input type="text" name="bookauthor_set-${index}-role" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
    )
  );
  inlineForm.append(
    $(
      `<div class="form-group"><label for="bookauthor_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="bookauthor_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_bookauthor_set-${index}-role"></div></div>`
    )
  );
  inlineForm.append(
    $(
      `<div class="form-group"><div class="mr-2 mt-2"><div class="form-check"><input type="checkbox" name="bookauthor_set-${index}-DELETE" class="checkboxinput form-check-input" id="id_bookauthor_set-${index}-DELETE"><label for="id_bookauthor_set-${index}-DELETE" class="form-check-label">Delete </label></div></div></div>`
    )
  );

  parent.append(inlineForm);
  totalForms.val(index + 1);

  // @ts-ignore
  selectField.select2({ theme: 'bootstrap', tags: 'true' });
  inlineForm.find('.form-check-input').on('click', function (event) {
    $(this)
      .closest('.form-inline')
      .hide(1000);
  });
}

/** @param {JQueryEventObject} event */
function addListEntryField (event) {
  event.preventDefault();

  const parent = $('#formset-readinglistentry_set');
  const totalForms = $('input[name="readinglistentry_set-TOTAL_FORMS"]');
  const index = parseInt(String(totalForms.val()));

  const inlineForm = $('<div class="form-inline"></div>');
  const selectField = $(event.data.template.replace(/__prefix__/g, index)).find(
    'select'
  );

  const authorFormGroup = $('<div class="form-group"></div>');
  authorFormGroup.append(
    `<label for="id_readinglistentry_set-${index}-reading_list}" class="mr-2 requiredField">Reading list*</label>`
  );
  const selectDiv = $('<div class="mr-2 mt-2"></div>');
  selectDiv.append(selectField);
  authorFormGroup.append(selectDiv);
  inlineForm.append(authorFormGroup);

  inlineForm.append(
    $(
      `<div class="form-group"><label for="readinglistentry_set-${index}-order" class="mr-2">Order</label><div class="mr-2 mt-2"><input type="number" name="readinglistentry_set-${index}-order" maxlength="255" class="textinput textInput form-control" id="id_readinglistentry_set-${index}-role"></div></div>`
    )
  );
  inlineForm.append(
    $(
      `<div class="form-group"><div class="mr-2 mt-2"><div class="form-check"><input type="checkbox" name="readinglistentry_set-${index}-DELETE" class="checkboxinput form-check-input" id="id_readinglistentry_set-${index}-DELETE"><label for="id_readinglistentry_set-${index}-DELETE" class="form-check-label">Delete </label></div></div></div>`
    )
  );

  parent.append(inlineForm);
  totalForms.val(index + 1);

  selectField.select2({ theme: 'bootstrap' });
  inlineForm.find('.form-check-input').on('click', function () {
    $(this)
      .closest('.form-inline')
      .hide(1000);
  });
}

/** @param {JQueryEventObject} event */
function setDateToday (event) {
  event.preventDefault();
  const elementId = event.data.elementId;

  const date = new Date();

  $('#id_' + elementId + '_date_month').val(date.getMonth() + 1);
  $('#id_' + elementId + '_date_month').trigger('change');

  $('#id_' + elementId + '_date_year').val(date.getFullYear());
  $('#id_' + elementId + '_date_year').trigger('change');

  $('#id_' + elementId + '_date_day').val(date.getDate());
  $('#id_' + elementId + '_date_day').trigger('change');
}

function configureSelectFields () {
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

/** @param {string} fieldName */
function configureDateFields (fieldName) {
  $(`#id_${fieldName}_day`).select2({ theme: 'bootstrap', width: '5em' });
  $(`#id_${fieldName}_month`).select2({ theme: 'bootstrap', width: '9em' });
  $(`#id_${fieldName}_year`).select2({
    theme: 'bootstrap',
    tags: true,
    width: '6em'
  });

  $(`#id_${fieldName}_month`)
    .parent()
    .addClass('form-row');
  $(`#id_${fieldName}_month`)
    .parent()
    .find('span')
    .each(function () {
      $(this).addClass('mr-2');
    });
}

/** @param {string} elementId */
function addSetDateTodayButton (elementId) {
  $(`#div_id_${elementId}_date`).append(
    `<a href="#" id="${elementId}_date_set_today">Set to today</a>`
  );

  $(`#${elementId}_date_set_today`).on(
    'click',
    null,
    { elementId },
    setDateToday
  );
}

/** @param {string} selector, @this {Element} */
function isbnFieldPasteFilter (selector) {
  $(selector).on('paste', function (ev) {
    ev.preventDefault();
    // @ts-ignore
    const pastedText = ev.originalEvent.clipboardData.getData('text/plain');
    const elem = $(this);
    elem.val(pastedText.replace(/\D/g, ''));
  });
  $(selector).on('input', function (ev) {
    ev.preventDefault();
    const elem = $(this);
    elem.val(String(elem.val()).replace(/\D/g, ''));
  });
}
