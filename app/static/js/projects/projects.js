//
// General Helper Functions
//

function jsonifyForm () {
  /* Handles JSON form serialisation */
  var form = {}
  $.each($('form').serializeArray(), function (i, field) {
    form[field.name] = field.value || ''
  })
  return form
}

function validateQuery (requiredFields) {
  // Remove previous error messages
  $('.has-error').find('.rule-actions > .error-message').remove()

  // Serialise and validate the form values
  var formvals = jsonifyForm()

  // Make sure a query has been entered, then submit the query
  if (formvals['db-query'] === '') {
    bootbox.alert('Please enter a query.')
    return false
  } else {
    // Make sure all required fields are present
    var valid = true
    var invalid = []
    $.each(requiredFields, function (index, value) {
      if (formvals[value] === '') {
        valid = false
        invalid.push(value)
      }
    })
    if (valid === false) {
      var msg = '<p>Please enter values for the following fields:</p>'
      msg += '<ul>'
      $.each(invalid, function (index, value) {
        msg += '<li>' + value + '</li>'
      })
      msg += '</ul>'
      bootbox.alert(msg)
      return false
    } else {
      return formvals
    }
  }
}

//
// $(document).ready()
//

$(document).ready(function () {
  // When the Export button is clicked, validate and create a querystring
  $('#export').click(function (e) {
    e.preventDefault()
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery([])
    if (formvals !== false) {
      exportProject(formvals)
    }
  })

  // When the Get Query button is clicked, validate and create a querystring
  $('.dropdown-item').click(function () {
    var btnId = $(this).attr('id').replace('-btn', '')
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery([])
    if (formvals !== false) {
      launchJupyter(btnId, formvals)
    }
  })

  function exportProject (formvals) {
    /* Sends the information needed to save the results of the 
    query to a zip archive.
    Input: The values from the search form
    Returns: An array containing results and errors for display
    */
    var data = {
      'data': formvals
    }
    $.ajax({
      method: 'POST',
      url: '/projects/export-project',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        response = JSON.parse(response)
        if (response['errors'].length > 0) {
          var msg = '<p>The following errors occurred:</p><ul>'
          $.each(response['errors'], function (index, value) {
            msg += '<li>' + value + '</li>'
          })
          msg += '</ul>'
          bootbox.alert({
            message: msg
          })
        } else {
          window.location = '/projects/download-export/' + response['filename']
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p>',
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  }

  function downloadExport (filename) {
    /* Sends the filename to the back end export response method.
    */
    window.location = '/projects/download-export' + filename
  }

  function launchJupyter (btnId, formvals) {
    /* Sends the information needed to launch a Jupyter notebook
    Input: The notebook to launch and the values from the search form
    Returns: An array containing results and errors for display
    */
    var data = {
      'notebook': btnId,
      'data': formvals
    }
    $.ajax({
      method: 'POST',
      url: '/projects/launch-jupyter',
      data: JSON.stringify(data),
      contentType: 'application/json;charset=UTF-8'
    })
      .done(function (response) {
        if (response === 'error') {
          bootbox.alert({
            message: '<p>Unknown Error: A Jupyter notebook could not be launched. Make sure you have a Jupyter server running.</p>'
          })
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        bootbox.alert({
          message: '<p>Sorry, mate! You\'ve got an error!</p>',
          callback: function () {
            return 'Error: ' + textStatus + ': ' + errorThrown
          }
        })
      })
  }
})

/* Toggles the Edit/Update button and field disabled property */
$('#update').click(function (e) {
  e.preventDefault()
  // if ($('#update').html() === 'Edit') {
  if (!$(this).hasClass('editable')) {
    $('form').find('input, textarea, select').each(function () {
      if ($(this).attr('id') !== 'name') {
        $(this).prop('readonly', false)
        $(this).removeClass('disabled')
      }
      if ($(this).attr('id') === 'metapath') {
        $(this).prop('readonly', true)
        $(this).addClass('disabled')
      }
    })
    // $('#update').html('Update')
    $(this).addClass('editable')
    $('#update').html('<i class="fa fa-save"></i>')
  } else {
    var name = $('#name').val()
    bootbox.confirm({
      message: 'Are you sure you wish to update the record for <code>' + name + '</code>?',
      buttons: {
        confirm: {label: 'Yes', className: 'btn-success'},
        cancel: {label: 'No', className: 'btn-danger'}
      },
      callback: function (result) {
        if (result === true) {
          var name = $('#name').val()
          var path = $('#path').val()
          var jsonform = jsonifyForm($('#manifestForm'))
          $.extend(jsonform, {'name': name})
          $.extend(jsonform, {'path': path})
          updateManifest(jsonform, name)
        }
      }
    })
  }
})

function updateManifest (jsonform, name) {
  /* Updates the displayed manifest
  Input: A JSON serialisation of the form values
  Returns: A copy of the manifest and an array of errors for display */
  var manifest = JSON.stringify(jsonform, null, '  ')
  $.ajax({
    method: 'POST',
    url: '/projects/update-manifest',
    data: manifest,
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var manifest = JSON.parse(response)['manifest']
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not update the manifest because of the following errors:</p>' + errors
      } else {
        msg = '<p>Updated the following manifest:</p>' + manifest
      }
      $(this).removeClass('editable')
      $('#update').html('<i class="fa fa-pencil"></i>')
      bootbox.alert({
        message: msg,
        callback: function () {
          //window.location = '/projects'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be updated because of the following errors:</p>'+response,
        callback: function () {
          $(this).removeClass('editable')
          $('#update').html('<i class="fa fa-pencil"></i>')
          return 'Error: ' + textStatus + ': ' + errorThrown
        }
      })
    })
}

/* Handles the manifest preview and hide buttons */
$('#preview').click(function (e) {
  e.preventDefault()
  $('form').hide()
  $('#previewDisplay').show()
  var jsonform = jsonifyForm($('#manifestForm'))
  $('#manifest').html(JSON.stringify(jsonform, null, '  '))
})

$('#hide').click(function (e) {
  e.preventDefault()
  $('#previewDisplay').hide()
  $('form').show()
})

/* Handles the Delete button */
$('#delete').click(function (e) {
  e.preventDefault()
  var name = $('#name').val()
  var metapath = $('#metapath').val()
  bootbox.confirm({
    message: 'Are you sure you wish to delete <code>' + name + '</code>?',
    buttons: {
      confirm: {label: 'Yes', className: 'btn-success'},
      cancel: {label: 'No', className: 'btn-danger'}
    },
    callback: function (result) {
      if (result === true) {
        deleteManifest(name, metapath)
      }
    }
  })
})

function deleteManifest (name, metapath) {
  /* Deletes a manifest
  Input: A name value
  Returns: An array of errors for display */
  $.ajax({
    method: 'POST',
    url: '/projects/delete-manifest',
    data: JSON.stringify({'name': name, 'metapath': metapath}),
    contentType: 'application/json;charset=UTF-8'
  })
    .done(function (response) {
      var errors = JSON.parse(response)['errors']
      if (errors !== '') {
        var msg = '<p>Could not delete the manifest because of the following errors:</p>' + errors;
      } else {
        msg = '<p>The manifest for <code>' + name + '</code> was deleted.</p>'
      }
      bootbox.alert({
        message: msg,
        callback: function () {
          window.location = '/projects'
        }
      })
    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>',
        callback: function () {
          return 'Error: ' + textStatus + ': ' + errorThrown
        }
      })
    })
}
