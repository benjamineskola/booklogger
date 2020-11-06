$(document).ready(function () {
  $(".form-addtag").submit(function (event) {
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
            '<span class="ui label"><a href="/tag/' +
              new_tag +
              '">' +
              new_tag +
              "</a></span> "
          );
        }
        input_field.val("");
      },
    });
  });

  $(".form.update-progress").submit(function (event) {
    event.preventDefault();
    var form = $(this);
    var url = form.attr("action");

    $.ajax({
      type: "POST",
      url: url,
      data: form.serialize(),
      dataType: "json",
      success: function (data) {
        var progress_bar = $("#book-" + form.data("book") + " .bar");
        progress_bar.css("width", data["percentage"] + "%");

        var progress_text = $(
          "#book-" + form.data("book") + " .extra.content .progress-date"
        );
        if (progress_text.length == 0) {
          var progress_text = $(
            "#book-" + form.data("book") + " .extra.content .read-dates"
          );
          progress_text.text(
            progress_text.text() + "; " + data["progress_text"]
          );
        } else {
          progress_text.text(data["progress_text"]);
        }

        form.find('input[name="value"]').val("");
      },
    });
  });

  $(".ui.rating").rating({
    clearable: true,
    onRate: function (value) {
      $.ajax({
        type: "POST",
        url: "/book/" + $(this).data("book") + "/rate/",
        data: "rating=" + Number(value),
        dataType: "json",
        beforeSend: function (xhr, settings) {
          xhr.setRequestHeader(
            "X-CSRFToken",
            $("[name=csrfmiddlewaretoken]").val()
          );
        },
      });
    },
  });
  $(".ui.accordion").accordion();
  $("#navbar .ui.dropdown").dropdown();

  $("a.remove-tag").click(function () {
    var tag = $(this).data("tag");
    var label = $(this).parent();
    var book = label.parent().parent().parent().data("book");
    $.ajax({
      type: "POST",
      url: "/book/" + book + "/remove_tags/",
      data: { tags: tag },
      beforeSend: function (xhr, settings) {
        xhr.setRequestHeader(
          "X-CSRFToken",
          $("[name=csrfmiddlewaretoken]").val()
        );
        return confirm("Remove tag " + tag + "?");
      },
      success: function (data) {
        label.remove();
      },
    });
  });
});

function load_next_page(year, url) {
  $(".loader").visibility({
    onTopVisible: function (calculations) {
      var placeholder = $(this);
      $.ajax({
        type: "GET",
        url: url,
        success: function (data) {
          var body = $(data).find(".two.doubling.cards").parent();
          placeholder.html(body);
          placeholder.attr("class", "");
        },
        error: function () {
          placeholder.find(".message").addClass("hidden");
          placeholder.find(".error.message").removeClass("hidden");
        },
      });
    },
  });
}
