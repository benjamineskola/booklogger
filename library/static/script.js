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

  $(".form.update-progress").each(function (i, form) {
    $(form).submit(function (event) {
      event.preventDefault();
      var form = $(this);
      var url = form.attr("action");

      $.ajax({
        type: "POST",
        url: url,
        data: form.serialize(),
        success: function (data) {
          var progress_type = "";
          form
            .find('input[name="progress_type"]:radio')
            .each(function (i, elem) {
              if (elem.checked) {
                progress_type = $(elem).val();
                return;
              }
            });
          var progress_field = form.find('input[name="value"]');
          var progress = progress_field.val();

          var percentage = 0;
          if (progress_type == "percentage") {
            var percentage = progress;
          } else {
            var percentage =
              (progress / parseInt(form.data("page-count"))) * 100;
          }

          var progress_bar = $("#book-" + form.data("book") + " .bar");
          progress_bar.css("width", percentage + "%");

          var progress_text = $(
            "#book-" + form.data("book") + " .extra.content .progress-date"
          );
          var d = new Date();
          var progress_message =
            Math.round(percentage) + "% on " + d.toLocaleDateString();
          if (progress_text.length == 0) {
            var progress_text = $(
              "#book-" + form.data("book") + " .extra.content .read-dates"
            );
            progress_text.text(progress_text.text() + "; " + progress_message);
          } else {
            progress_text.text(progress_message);
          }

          progress_field.val("");
        },
      });
    });
  });
});
