/* globals $ */

$(document).ready(function () {
  // @ts-ignore
  if (document.formTags !== null) {
    // @ts-ignore
    $('#id_tags').val(document.formTags);
    $('#id_tags').trigger('change');
  }

  $('#card-bookauthor_set, #card-logentry_set, #card-readinglistentry_set')
    .find('.form-check-input')
    .on('click', function (event) {
      $(this).closest('.form-inline').hide(1000);
    });
});
