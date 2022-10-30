/* globals $, confirm, history */

$(document).ready(function () {
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

      // TODO
      // const rateBook = new RateBook()
      // rateBook.init(body)

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
