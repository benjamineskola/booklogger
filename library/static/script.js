$(document).ready(function () {
  $("a.remove-tag").on("click", remove_tag);
  $("form.add-tag").on("submit", add_tag);
  $("form.update-progress").on("submit", update_progress);
  $("span.rating-star").on("click", rate_book);

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

      body.find("a.remove-tag").on("click", remove_tag);
      body.find("form.add-tag").on("submit", add_tag);
      body.find("form.update-progress").on("submit", update_progress);
      body.find("span.rating-star").on("click", rate_book);

      if (window.location.hash.split("-").pop() == year) {
        $("html, body").animate(
          {
            scrollTop: body.offset().top,
          },
          10
        );
      }
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

function add_tag(event) {
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
      form.collapse("hide");
    },
  });
}

function rate_book() {
  console.log(this);
  var value = $(this).data("rating");
  var ratings = $(this).parent();
  var book = ratings.data("book");
  var old_rating = ratings.data("rating");

  if (old_rating == value) {
    value = value - 0.5;
  } else if (old_rating == value - 0.5) {
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
        } else if (value - i == 0.5) {
          $(star).text("½");
        } else {
          $(star).text("☆");
        }
      });
    },
  });
}

function remove_tag() {
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
}

function update_progress(event) {
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
        progress_text.text(`${progress_text.text()}; ${data["progress_text"]}`);
      } else {
        progress_text.text(data["progress_text"]);
      }

      form.find('input[name="value"]').val("");
    },
  });
}

function update_scroll_position() {
  $("h2").each(function () {
    const height = $(window).height();
    var top = window.pageYOffset;
    var distance = top - $(this).offset().top;
    var hash = $(this).attr("href");
    if (Math.abs(distance) < height * 0.75) {
      if (window.location.hash != hash) {
        if (history.pushState) {
          history.pushState(null, null, hash);
        } else {
          window.location.hash = hash;
        }
      }
    } else if (0 - distance > height && hash == window.location.hash) {
      var year = hash.split("-").pop();
      if (year == "sometime") {
        var new_year = 2004;
      } else {
        var new_year = parseInt(year) + 1;
      }
      var new_hash = `#read-${new_year}`;
      if (history.pushState) {
        history.pushState(null, null, new_hash);
      } else {
        window.location.hash = new_hash;
      }
    }
  });
}
