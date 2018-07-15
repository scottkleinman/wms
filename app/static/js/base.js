/* Helper functions for the processing icon */
function showProcessing () {
  $('#processingIcon').show()
}
function hideProcessing () {
  $('#processingIcon').delay(500).hide(50)
}

/* Scripts loaded by base.html */
$(document).ready(function () {
  // Disable search field
  $('#search').submit(function (e) {
    e.preventDefault()
    alert('Search functionality has not yet been enabled.')
  })
  // Handle scroll to top
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      $('#scroll').fadeIn()
    } else {
      $('#scroll').fadeOut()
    }
  })
  $('#scroll').click(function () {
    $('html, body').animate({ scrollTop: 0 }, 600)
    return false
  })
})
