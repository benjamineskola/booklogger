$(document).ready(function () {
  $('a.remove-tag').on('click', remove_tag)
  $('form.add-tag').on('submit', add_tag)
  $('form.update-progress').on('submit', update_progress)
  $('span.rating-star').on('click', rate_book)

  $('div.stats-for-year').each(function (i, e) {
    return load_stats_for_year(e)
  })
})

function load_next_page (year, url) {
  const placeholder = $('.loader')
  $.ajax({
    type: 'GET',
    url,
    success: function (data) {
      const body = $(data).find('.book.card').parent().parent().parent()
      body.insertAfter(placeholder.parent())
      placeholder.remove()

      body.find('a.remove-tag').on('click', remove_tag)
      body.find('form.add-tag').on('submit', add_tag)
      body.find('form.update-progress').on('submit', update_progress)
      body.find('span.rating-star').on('click', rate_book)

      if (window.location.hash.split('-').pop() == year) {
        $('html, body').animate(
          {
            scrollTop: body.offset().top
          },
          10
        )
      }
    },
    error: function () {
      placeholder.find('.spinner-grow').addClass('d-none')
      placeholder.find('.alert-danger').removeClass('d-none')
    }
  })
}

function load_stats_for_year (e) {
  const div = $(e)
  const year = div.data('year')

  $.ajax({
    type: 'GET',
    url: `/stats/${year}`,
    success: function (data) {
      $('.spinner-grow').show()
      div.html(data)
    },
    error: function (data) {
      div.html(`
          <div id="error-${year}" class="alert alert-danger">
            <i class="exclamation circle icon"></i>
            <div class="content">
              <div class="header">Failed to load ${year}.</div>
              <p><span class="btn btn-outline-danger">Retry?</span></p>
            </div>
          </div>
`)
      $(`#error-${year} .btn`).on('click', function () {
        div.html(`
          <div id="loading-stats-${year}" class="spinner-grow mb-4" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        `)
        return load_stats_for_year(e)
      })
    }
  })
}

function add_tag (event) {
  event.preventDefault()
  const form = $(this)
  const url = form.attr('action')

  $.ajax({
    type: 'POST',
    url,
    data: form.serialize(),
    dataType: 'json',
    success: function (data) {
      const tags_field = $(form.data('tags'))
      const input_field = form.find('input[name="tags"]')
      for (const i in data.tags) {
        new_tag = data.tags[i]
        tags_field.prepend(
          `<span class="badge badge-secondary"><a href="/tag/${new_tag}">${new_tag}</a></span> `
        )
      }
      input_field.val('')
      form.collapse('hide')
    }
  })
}

function rate_book () {
  console.log(this)
  let value = $(this).data('rating')
  const ratings = $(this).parent()
  const book = ratings.data('book')
  const old_rating = ratings.data('rating')

  if (old_rating == value) {
    value = value - 0.5
  } else if (old_rating == value - 0.5) {
    value = 0
  }

  $.ajax({
    type: 'POST',
    url: `/book/${book}/rate/`,
    data: { rating: Number(value) },
    beforeSend: function (xhr, settings) {
      xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val())
    },
    success: function (data) {
      ratings.data('rating', value)
      ratings.children().each(function (i, star) {
        if (value >= i + 1) {
          $(star).text('★')
        } else if (value - i == 0.5) {
          $(star).text('½')
        } else {
          $(star).text('☆')
        }
      })
    }
  })
}

function remove_tag () {
  const tag = $(this).data('tag')
  const label = $(this).parent()
  const book = label.parent().data('book')
  $.ajax({
    type: 'POST',
    url: `/book/${book}/remove_tags/`,
    data: { tags: tag },
    beforeSend: function (xhr, settings) {
      xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val())
      return confirm(`Remove tag ${tag}?`)
    },
    success: function (data) {
      label.remove()
    }
  })
}

function update_progress (event) {
  event.preventDefault()
  const form = $(this)
  const url = form.attr('action')
  const book = form.data('book')

  $.ajax({
    type: 'POST',
    url,
    data: form.serialize(),
    dataType: 'json',
    success: function (data) {
      const progress_bar = $(`#book-${book} .progress-bar`)
      progress_bar.css('width', `${data.percentage}%`)

      var progress_text = $(`#book-${book} .card-footer .progress-date`)
      if (progress_text.length == 0) {
        var progress_text = $(`#book-${book} .card-footer .read-dates`)
        progress_text.text(`${progress_text.text()}; ${data.progress_text}`)
      } else {
        progress_text.text(data.progress_text)
      }

      form.find('input[name="value"]').val('')
    }
  })
}

function update_scroll_position () {
  $('h2').each(function () {
    const height = $(window).height()
    const top = window.pageYOffset
    const distance = top - $(this).offset().top
    const hash = $(this).attr('href')
    if (Math.abs(distance) < height * 0.75) {
      if (window.location.hash != hash) {
        if (history.pushState) {
          history.pushState(null, null, hash)
        } else {
          window.location.hash = hash
        }
      }
    } else if (0 - distance > height && hash == window.location.hash) {
      const year = hash.split('-').pop()
      if (year == 'sometime') {
        var new_year = 2004
      } else {
        var new_year = parseInt(year) + 1
      }
      const new_hash = `#read-${new_year}`
      if (history.pushState) {
        history.pushState(null, null, new_hash)
      } else {
        window.location.hash = new_hash
      }
    }
  })
}
