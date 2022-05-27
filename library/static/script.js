/* globals $, confirm, history */

$(document).ready(function () {
  $('a.remove-tag').on('click', removeTag)
  $('form.add-tag').on('submit', addTag)
  $('form.update-progress').on('submit', updateProgress)
  $('span.rating-star').on('click', rateBook)

  $('div.stats-for-year').each(function (i, e) {
    return loadStatsForYear(e)
  })
})

/* eslint-disable-next-line camelcase, no-unused-vars */
function load_next_page (year, url) {
  const placeholder = $('.loader')
  $.ajax({
    type: 'GET',
    url,
    success: function (data) {
      const body = $(data).find('.book.card').parent().parent().parent()
      body.insertAfter(placeholder.parent())
      placeholder.remove()

      body.find('a.remove-tag').on('click', removeTag)
      body.find('form.add-tag').on('submit', addTag)
      body.find('form.update-progress').on('submit', updateProgress)
      body.find('span.rating-star').on('click', rateBook)

      if (window.location.hash.split('-').pop() === year) {
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

function loadStatsForYear (e) {
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
        return loadStatsForYear(e)
      })
    }
  })
}

function addTag (event) {
  event.preventDefault()
  const form = $(this)
  const url = form.attr('action')

  $.ajax({
    type: 'POST',
    url,
    data: form.serialize(),
    dataType: 'json',
    success: function (data) {
      const tagsField = $(form.data('tags'))
      const inputField = form.find('input[name="tags"]')
      for (const i in data.tags) {
        const newTag = data.tags[i]
        tagsField.prepend(
          `<span class="badge badge-secondary"><a href="/tag/${newTag}">${newTag}</a></span> `
        )
      }
      inputField.val('')
      form.collapse('hide')
    }
  })
}

function rateBook () {
  console.log(this)
  let value = $(this).data('rating')
  const ratings = $(this).parent()
  const book = ratings.data('book')
  const oldRating = ratings.data('rating')

  if (oldRating === value) {
    value = value - 0.5
  } else if (oldRating === value - 0.5) {
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
        } else if (value - i === 0.5) {
          $(star).text('½')
        } else {
          $(star).text('☆')
        }
      })
    }
  })
}

function removeTag () {
  const tag = $(this).data('tag')
  const label = $(this).parent()
  const book = label.parent().data('book')
  $.ajax({
    type: 'POST',
    url: `/book/${book}/remove_tag/`,
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

function updateProgress (event) {
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
      const progressBar = $(`#book-${book} .progress-bar`)
      progressBar.css('width', `${data.percentage}%`)

      let progressText = $(`#book-${book} .card-footer .progress-date`)
      if (progressText.length === 0) {
        progressText = $(`#book-${book} .card-footer .read-dates`)
        progressText.text(`${progressText.text()}; ${data.progress_text}`)
      } else {
        progressText.text(data.progress_text)
      }

      form.find('input[name="value"]').val('')
    }
  })
}

/* eslint-disable-next-line camelcase, no-unused-vars */
function update_scroll_position () {
  $('h2').each(function () {
    const height = $(window).height()
    const top = window.pageYOffset
    const distance = top - $(this).offset().top
    const hash = $(this).attr('href')
    if (Math.abs(distance) < height * 0.75) {
      if (window.location.hash !== hash) {
        if (history.pushState) {
          history.pushState(null, null, hash)
        } else {
          window.location.hash = hash
        }
      }
    } else if (0 - distance > height && hash === window.location.hash) {
      const year = hash.split('-').pop()
      let newYear
      if (year === 'sometime') {
        newYear = 2004
      } else {
        newYear = parseInt(year) + 1
      }
      const newHash = `#read-${newYear}`
      if (history.pushState) {
        history.pushState(null, null, newHash)
      } else {
        window.location.hash = newHash
      }
    }
  })
}
