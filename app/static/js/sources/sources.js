//
// General Helper Functions
//

function jsonifyForm () {
  /* Handles JSON form serialisation */
  var form = {}
  $.each($('form *').not('.datepicker').serializeArray(), function (i, field) {
    form[field.name] = field.value || ''
  })
  return form
}

//
// Ajax Functions
//

function createManifest (jsonform) {
  /* Creates a new manifest
	   Input: A JSON serialisation of the form values
	   Returns: A copy of the manifest and an array of errors for display */
  manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/sources/create-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors != '') {
        msg = '<p>Could not save the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>Saved the following manifest:</p>' + manifest
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function deleteManifest (name, metapath) {
  /* Deletes a manifest
	   Input: A name value
	   Returns: An array of errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/delete-manifest',
    data: JSON.stringify({ 'name': name, 'metapath': metapath }),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var errors = JSON.parse(response)['errors']
      if (errors != '') {
        msg = '<p>Could not delete the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>The manifest for <code>' + name + '</code> was deleted.</p>'
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function exportSourceManifest () {
  /* Exports a single source manifest from the Display page.
	   Input: Values from the search form
	   Returns: An array containing results and errors for display */

  filename = $('#name').val() + '.json'
  $.ajax({
    method: 'POST',
    url: '/sources/export-manifest',
    data: JSON.stringify({ 'name': $('#name').val() }),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      response = JSON.parse(response)
      if (response['errors'].length != 0) {
        result = JSON.stringify(response['errors'])
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>',
          callback: function () {
            ('Error: ' + textStatus + ': ' + errorThrown)
          }
        })
      } else {
        window.location = '/sources/download-export/' + filename
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function exportSearch (data) {
  /* Exports the results of a Sources search
	   Input: Values from the search form
	   Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/export-search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      response = JSON.parse(response)
      if (response['errors'].length != 0) {
        result = JSON.stringify(response['errors'])
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>',
          callback: function () {
            ('Error: ' + textStatus + ': ' + errorThrown)
          }
        })
      } else {
        window.location = '/sources/download-export/' + response['filename']
      }
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function searchSources (data) {
  /* Searches the Sources database
		Input: Values from the search form
		Returns: An array containing results and errors for display */
  $.ajax({
    method: 'POST',
    url: '/sources/search',
    data: JSON.stringify(data),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      $('#results').empty()
      response = JSON.parse(response)
      if (response['errors'].length != 0) {
        result = response['errors']
      } else {
        result = response['response']
      }
      // Make the result into a string
      var out = ''
      $.each(result, function (i, item) {
        var link = '/sources/display/' + item['name']
        out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>'
        $.each(item, function (key, value) {
          value = JSON.stringify(value)
          out += '<code>' + key + '</code>: ' + value + '<br>'
        })
        out += '<hr>'
      })
      var $pagination = $('#pagination')
      var defaultOpts = {
        visiblePages: 5,
        initiateStartPageClick: false,
        onPageClick: function (event, page) {
          var newdata = {
            'query': $('#query').val(),
            'regex': $('#regex').is(':checked'),
            'limit': $('#limit').val(),
            'properties': $('#properties').val(),
            'page': page
          }
          searchPubs(newdata)
          $('#scroll').click()
        }
      }
      var totalPages = parseInt(response['num_pages'])
      var currentPage = $pagination.twbsPagination('getCurrentPage')
      $pagination.twbsPagination('destroy')
      $pagination.twbsPagination($.extend({}, defaultOpts, {
        startPage: currentPage,
        totalPages: totalPages
      }))
      $('#results').append(out)
      $('#hideSearch').html('Show Form')
      $('#exportSearchResults').show()
      $('#search-form').hide()
      $('#results').show()
      $('#pagination').show()
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function updateManifest (jsonform, name) {
  /* Updates the displayed manifest
	   Input: A JSON serialisation of the form values
	   Returns: A copy of the manifest and an array of errors for display */
  manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/sources/update-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors != '') {
        msg = '<p>Could not update the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>Updated the following manifest:</p>' + manifest
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/sources'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be updated because of the following errors:</p>' + response,
        callback: function () {
          ('Error: ' + textStatus + ': ' + errorThrown)
        }
      })
    })
}

function cleanup () {
  var newform = jsonifyForm()
  for (var key in newform) {
    if (newform[key] == '') delete newform[key]
  }
  return newform
}
//
// $(document).ready() Event Handling
//

$(document).ready(function () {
  //
  // Index Page Functions
  //

  /* Handles the Display form */
  $('#go').click(function (e) {
    var name = $('#display').val()
    window.location = '/sources/display/' + name
  })
  $('#display').on('keypress', function (e) {
    var key = (e.keyCode || e.which)
    if (key == 13 || key == 3) {
      $('#go').click()
    }
  })

  //
  // Create and Display Page Functions
  //

  /* Handles the manifest preview and hide buttons */
  $('#preview').click(function (e) {
    e.preventDefault()
    $('form').hide()
    $('#previewDisplay').show()
    var jsonform = cleanup()

    $('#manifest').html(JSON.stringify(jsonform
      , null
      , '  '))
  })

  $('#hide').click(function (e) {
    e.preventDefault()
    $('#previewDisplay').hide()
    $('form').show()
  })

  //
  // Create Page Functions
  //

  /* Handles form submission for record creation */
  $('form').on('submit', function (e) {
    e.preventDefault()
    if ($(this).parsley().isValid()) {
      var jsonform = jsonifyForm()
      createManifest(jsonform)
    }
  })

  /* datepicker functions */
  $('.datepicker').datepicker({
    dateFormat: 'yy-mm-dd', // check change
    timeFormat: 'hh:mm:ss',
    constrainInput: false
  })

  var counter = 0

  function dict (name, id, value) {
    this.name = name
    this.id = id
    this.value = value
  }

  $('#add_date').on('click', function () {
    counter = counter + 1
    var elem = '<li id="concatenate"><p class="datep">start date: <input name="' + counter + '" size="16" type="text" value="" class="datepicker date"></p><p class="datep">end date: <input name="' + counter + '" size="16" type="text" value="" class="datepicker date"></p><button type="button" class="remove_date btn btn-lg btn-outline-editorial">-</button></li>'
    $('ol').append(elem)
    $('.datepicker').datepicker({
      dateFormat: 'yy-mm-dd', // check change
      timeFormat: 'hh:mm:ss',
      constrainInput: false
    })
    return false // prevent form submission
  })

  $('ol').on('click', '.remove_date', function () {
    $(this).parent().remove()
    return false
  })

  $('#getdatevalue').click(function () {
    var map = []
    $('.date').map(function () {
      var date = new dict($(this).attr('name'), $(this).parent().index(), $(this).val())
      map.push(date)
    })
    var s = ''
    for (var i = 1; i < map.length; i++) {
      if (map[i].name != map[i - 1].name) {
        if (map[i].value != '') {
          s = s + '/r/n' + map[i].value
        } else {
          s = s + ''
        }
      } else {
        if (map[i].value != '') {
          if (map[i].id == 1 && map[i].name == '0' && map[i - 1].value == '') {
            s = s + map[i].value
          } else {
            if (map[i].id == 1 && map[i - 1].value == '') {
              s = s + '/r/n' + map[i].value
            } else {
              s = s + ',' + map[i].value
            }
          }
        } else {
          s = s + ''
        }
      }
    }
    s = map[0].value + s
    document.getElementById('date').value = s
  })

  //
  // Display Page Functions
  //

  /* Toggles the Edit/Update button and field disabled property */
  $('#update').click(function (e) {
    e.preventDefault()
    if ($('#update').html() == 'Edit') {
      $('form').find('input, textarea, select').each(function () {
        if ($(this).attr('id') != 'name') {
          $(this).prop('readonly', false)
          $(this).removeClass('disabled')
        }
      })
      $('#update').html('Update')
    } else {
      var name = $('#name').val()
      bootbox.confirm({
        message: 'Are you sure you wish to update the record for <code>' + name + '</code>?',
        buttons: {
          confirm: { label: 'Yes', className: 'btn-success' },
          cancel: { label: 'No', className: 'btn-danger' }
        },
        callback: function (result) {
          if (result == true) {
            name = $('#name').val()
            var jsonform = jsonifyForm()
            $.extend(jsonform, { 'name': name })
            updateManifest(jsonform, name)
          }
        }
      })
    }
  })

  /* Handles the Delete button */
  $('#delete').click(function (e) {
    e.preventDefault()
    var name = $('#name').val()
    var metapath = $('#metapath').val()
    bootbox.confirm({
      message: 'Are you sure you wish to delete <code>' + name + '</code>?',
      buttons: {
        confirm: { label: 'Yes', className: 'btn-success' },
        cancel: { label: 'No', className: 'btn-danger' }
      },
      callback: function (result) {
        if (result == true) {
          deleteManifest(name, metapath)
        }
      }
    })
  })

  /* Handles the Export feature */
  $('#export').click(function (e) {
    e.preventDefault()
    exportSourceManifest()
  })

  //
  // Search Page Functions
  //

  /* Handles the Search feature */
  $('#searchSources').click(function (e) {
    e.preventDefault()
    data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': 1
    }
    searchSources(data)
  })

  /* Handles the Search Export feature */
  $('#exportSearchResults').click(function (e) {
    e.preventDefault()
    data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': 1,
      'paginated': false
    }
    exportSearch(data)
  })

  /* Toggles the search form */
  $('#hideSearch').click(function () {
    if ($('#hideSearch').html() == 'Hide Form') {
      $('#search-form').hide()
      $('#exportSearchResults').show()
      $('#results').show()
      $('#pagination').show()
      $('#hideSearch').html('Show Form')
    } else {
      $('#hideSearch').html('Hide Form')
      $('#exportSearchResults').hide()
      $('#results').hide()
      $('#pagination').hide()
      $('#search-form').show()
    }
  })

  /* Handles the pagination buttons */
  $('.page-link').click(function (e) {
    e.preventDefault()
    data = {
      'query': $('#query').val(),
      'regex': $('#regex').is(':checked'),
      'limit': $('#limit').val(),
      'properties': $('#properties').val(),
      'page': $(this).html()
    }
    searchSources(data)
  })
}) /* End of $(document).ready() Event Handling */
