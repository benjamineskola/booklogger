$(document).ready(function () {
  $(".form-addtag").submit(function (event) {
    event.preventDefault();
    var form = $(this);
    var url = form.attr("action");

    $.ajax({
      type: "POST",
      url: url,
      data: form.serialize(),
      dataType: "json",
      success: function (data) {
        var tags_field = $(form.data("tags"));
        var input_field = form.find('input[name="tags"]');
        for (var i in data.tags) {
          new_tag = data.tags[i];
          tags_field.prepend(
            `<span class="badge badge-secondary"><a href="/tag/${new_tag}">${new_tag}</a></span> `
          );
        }
        input_field.val("");
      },
    });
  });

  $("form.update-progress").submit(function (event) {
    event.preventDefault();
    var form = $(this);
    var url = form.attr("action");
    var book = form.data("book");

    $.ajax({
      type: "POST",
      url: url,
      data: form.serialize(),
      dataType: "json",
      success: function (data) {
        var progress_bar = $(`#book-${book} .progress-bar`);
        progress_bar.css("width", `${data["percentage"]}%`);

        var progress_text = $(`#book-${book} .card-footer .progress-date`);
        if (progress_text.length == 0) {
          var progress_text = $(`#book-${book} .card-footer .read-dates`);
          progress_text.text(
            `${progress_text.text()}; ${data["progress_text"]}`
          );
        } else {
          progress_text.text(data["progress_text"]);
        }

        form.find('input[name="value"]').val("");
      },
    });
  });

  $(".rating-star").on("click", function () {
    var value = $(this).data("rating");
    var ratings = $(this).parent();
    var book = ratings.data("book");
    var old_rating = ratings.data("rating");

    if (old_rating == value) {
      value = 0;
    }

    $.ajax({
      type: "POST",
      url: `/book/${book}/rate/`,
      data: { rating: Number(value) },
      beforeSend: function (xhr, settings) {
        xhr.setRequestHeader(
          "X-CSRFToken",
          $("[name=csrfmiddlewaretoken]").val()
        );
      },
      success: function (data) {
        ratings.data("rating", value);
        ratings.children().each(function (i, star) {
          if (value >= i + 1) {
            $(star).text("★");
          } else {
            $(star).text("☆");
          }
        });
      },
    });
  });

  $("a.remove-tag").click(function () {
    var tag = $(this).data("tag");
    var label = $(this).parent();
    var book = label.parent().data("book");
    $.ajax({
      type: "POST",
      url: `/book/${book}/remove_tags/`,
      data: { tags: tag },
      beforeSend: function (xhr, settings) {
        xhr.setRequestHeader(
          "X-CSRFToken",
          $("[name=csrfmiddlewaretoken]").val()
        );
        return confirm(`Remove tag ${tag}?`);
      },
      success: function (data) {
        label.remove();
      },
    });
  });

  document.years_loading = 0;
  $("div.stats-for-year").each(function (i, e) {
    if (typeof document.years_loading === undefined) {
      document.years_loading = {};
    }
    document.years_loading += 1;

    return load_stats_for_year(i, e, true);
  });
});

function load_next_page(year, url) {
  var placeholder = $(".loader");
  $.ajax({
    type: "GET",
    url: url,
    success: function (data) {
      var body = $(data).find(".book.card").parent().parent().parent();
      body.insertAfter(placeholder.parent());
      placeholder.remove();
    },
    error: function () {
      placeholder.find(".spinner-grow").addClass("d-none");
      placeholder.find(".alert-danger").removeClass("d-none");
    },
  });
}

function load_stats_for_year(i, e, update_counts) {
  var year = $(e).data("year");

  $.ajax({
    type: "GET",
    url: `/stats/${year}`,
    success: function (data) {
      $(e).html(data);

      if (update_counts) {
        document.years_loading -= 1;

        if (document.years_loading === 0) {
          $("#loading-stats").remove();
        }
      }
    },
    error: function (data) {
      $(e).html(`
          <hr>
          <div id="error-${year}" class="alert alert-danger">
            <i class="exclamation circle icon"></i>
            <div class="content">
              <div class="header">Failed to load ${year}.</div>
              <p><span class="btn btn-outline-danger">Retry?</span></p>
            </div>
          </div>
`);
      $(`#error-${year} .button`).on("click", function () {
        return load_stats_for_year(0, e, false);
      });

      if (update_counts) {
        document.years_loading -= 1;

        if (document.years_loading === 0) {
          $("#loading-stats").remove();
        }
      }
    },
  });
}
