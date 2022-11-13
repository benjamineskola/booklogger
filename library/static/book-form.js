/* globals $ */

$(document).ready(function () {
  configureSelectFields();

  // @ts-ignore
  if (document.formTags !== null) {
    // @ts-ignore
    $('#id_tags').val(document.formTags);
    $('#id_tags').trigger('change');
  }

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

});

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
