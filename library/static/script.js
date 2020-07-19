$(document).ready(function () {
  $(".form-addtag").each(function (i, form) {
    $(form).submit(function (event) {
      event.preventDefault();
      var form = $(this);
      var url = form.attr("action");

      $.ajax({
        type: "POST",
        url: url,
        data: form.serialize(),
        success: function (data) {
          var tags_field = $(form.data("tags"));
          var input_field = form.find('input[name="tags"]');
          var new_tags = input_field.val().split(",");
          for (var i in new_tags) {
            new_tag = new_tags[i].trim();
            tags_field.prepend(
              '<a href="/tag/' +
                new_tag +
                '" class="ui label">' +
                new_tag +
                "</a> "
            );
          }
          input_field.val("");
        },
      });
    });
  });
});
