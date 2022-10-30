/* globals $, confirm, history */

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
