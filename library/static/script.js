/* globals $, confirm, history */

$(document).ready(function () {
  $('a.remove-tag').on('click', removeTag);
  $('form.add-tag').on('submit', addTag);
  $('form.update-progress').on('submit', updateProgress);
  $('span.rating-star').on('click', rateBook);

  $('div.stats-for-year').each(function (i, e) {
    return loadStatsForYear(e);
  });
});

/**
 * @param {string} year
 * @param {string} url
 */
// eslint-disable-next-line no-unused-vars
function loadNextPage (year, url) {
  const placeholder = $('.loader');
  $.ajax({
    type: 'GET',
    url,
    success: function (data) {
      const body = $(data)
        .find('.book.card')
        .closest('body');
      body.insertAfter(placeholder.parent());
      placeholder.remove();

      body.find('a.remove-tag').on('click', removeTag);
      body.find('form.add-tag').on('submit', addTag);
      body.find('form.update-progress').on('submit', updateProgress);
      body.find('span.rating-star').on('click', rateBook);

      if (window.location.hash.split('-').pop() === year) {
        const offset = body.offset();
        if (typeof offset !== 'undefined') {
          $('html, body').animate(
            {
              scrollTop: offset.top
            },
            10
          );
        }
      }
    },
    error: function () {
      placeholder.find('.spinner-grow').addClass('d-none');
      placeholder.find('.alert-danger').removeClass('d-none');
    }
  });
}

/** @param {Element} element */
function loadStatsForYear (element) {
  const div = $(element);
  const year = div.data('year');

  $.ajax({
    type: 'GET',
    url: `/stats/${year}`,
    success: function (data) {
      $('.spinner-grow').show();
      div.html(data);
    },
    error: function () {
      div.html(`
          <div id="error-${year}" class="alert alert-danger">
            <i class="exclamation circle icon"></i>
            <div class="content">
              <div class="header">Failed to load ${year}.</div>
              <p><span class="btn btn-outline-danger">Retry?</span></p>
            </div>
          </div>
`);
      $(`#error-${year} .btn`).on('click', function () {
        div.html(`
          <div id="loading-stats-${year}" class="spinner-grow mb-4" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        `);
        return loadStatsForYear(element);
      });
    }
  });
}

/** @this Element, @param {Event} event */
function addTag (event) {
  event.preventDefault();
  const form = $(this);
  const url = form.attr('action');

  $.ajax({
    type: 'POST',
    url,
    data: form.serialize(),
    dataType: 'json',
    success: function (data) {
      const tagsField = $(form.data('tags'));
      const inputField = form.find('input[name="tags"]');
      for (const i in data.tags) {
        const newTag = data.tags[i];
        tagsField.prepend(
          `<span class="badge badge-secondary"><a href="/tag/${newTag}">${newTag}</a></span> `
        );
      }
      inputField.val('');
      // @ts-ignore
      form.collapse('hide');
    }
  });
}

/** @this Element  */
function rateBook () {
  let value = $(this).data('rating');
  const ratings = $(this).parent();
  const book = ratings.data('book');
  const oldRating = ratings.data('rating');

  if (oldRating === value) {
    value = value - 0.5;
  } else if (oldRating === value - 0.5) {
    value = 0;
  }

  $.ajax({
    type: 'POST',
    url: `/book/${book}/rate/`,
    data: { rating: Number(value) },
    beforeSend: function (xhr) {
      xhr.setRequestHeader(
        'X-CSRFToken',
        String($('[name=csrfmiddlewaretoken]').val())
      );
    },
    success: function () {
      ratings.data('rating', value);
      ratings.children().each(function (i, star) {
        if (value >= i + 1) {
          $(star).text('★');
        } else if (value - i === 0.5) {
          $(star).text('½');
        } else {
          $(star).text('☆');
        }
      });
    }
  });
}

/** @this Element */
function removeTag () {
  const tag = $(this).data('tag');
  const label = $(this).parent();
  const book = label.parent().data('book');
  $.ajax({
    type: 'POST',
    url: `/book/${book}/remove_tags/`,
    data: { tags: tag },
    beforeSend: function (xhr) {
      xhr.setRequestHeader(
        'X-CSRFToken',
        String($('[name=csrfmiddlewaretoken]').val())
      );
      if (!confirm(`Remove tag ${tag}?`)) {
        return false;
      }
    },
    success: function () {
      label.remove();
    }
  });
}

/** @this Element, @param {Event} event */
function updateProgress (event) {
  event.preventDefault();
  const form = $(this);
  const url = form.attr('action');
  const book = form.data('book');

  $.ajax({
    type: 'POST',
    url,
    data: form.serialize(),
    dataType: 'json',
    success: function (data) {
      const progressBar = $(`#book-${book} .progress-bar`);
      progressBar.css('width', `${data.percentage}%`);

      let progressText = $(`#book-${book} .card-footer .progress-date`);
      if (progressText.length === 0) {
        progressText = $(`#book-${book} .card-footer .read-dates`);
        progressText.text(`${progressText.text()}; ${data.progress_text}`);
      } else {
        progressText.text(data.progress_text);
      }

      form.find('input[name="value"]').val('');
    }
  });
}

// eslint-disable-next-line no-unused-vars
function updateScrollPosition () {
  $('h2').each(function () {
    const height = $(window).height();
    if (typeof height === 'undefined') {
      return;
    }

    const top = window.pageYOffset;
    const offset = $(this).offset();
    if (typeof offset === 'undefined') {
      return;
    }

    const distance = top - offset.top;
    const hash = $(this).attr('href');

    if (Math.abs(distance) < height * 0.75) {
      if (window.location.hash !== hash) {
        if (history.pushState) {
          history.pushState(null, '', hash);
        } else if (typeof hash !== 'undefined') {
          window.location.hash = hash;
        }
      }
    } else if (-distance > height && hash === window.location.hash) {
      const year = hash.split('-').pop();
      let newYear;
      if (year === 'sometime') {
        newYear = 2004;
      } else {
        newYear = parseInt(String(year)) + 1;
      }
      const newHash = `#read-${newYear}`;
      if (history.pushState) {
        history.pushState(null, '', newHash);
      } else {
        window.location.hash = newHash;
      }
    }
  });
}
