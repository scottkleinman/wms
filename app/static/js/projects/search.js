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

$(document).ready(function () {
  var schema = [
    {
      'id': 'contributors',
      'label': 'contributors',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'content',
      'label': 'content',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'created',
      'label': 'created',
      'type': 'date',
      'validation': {
        'callback': function (value, rule) {
          var d = moment(value, 'YYYY-MM-DD', true).isValid()
          var dt = moment(value, 'YYYY-MM-DDTHH:mm:ss', true).isValid()
          if (d === true || dt === true) {
            return true
          } else {
            return ['<code>{0}</code> is not a valid date format. Please use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:mm:ss</code>.', value]
          }
        }
      }
    },
    {
      'id': 'description',
      'label': 'description',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'id',
      'label': 'id',
      'type': 'string',
      'size': 30
    },
    {
      'id': '_id',
      'label': '_id',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'image',
      'label': 'image',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'keywords',
      'label': 'keywords',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'label',
      'label': 'label',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'metapath',
      'label': 'metapath',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'name',
      'label': 'name',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'namespace',
      'label': 'namespace',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'licenses',
      'label': 'licenses',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'notes',
      'label': 'notes',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'resources',
      'label': 'resources',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'shortTitle',
      'label': 'shortTitle',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'title',
      'label': 'title',
      'type': 'string',
      'size': 30
    },
    {
      'id': 'updated',
      'label': 'updated',
      'type': 'date',
      'validation': {
        'callback': function (value, rule) {
          var d = moment(value, 'YYYY-MM-DD', true).isValid()
          var dt = moment(value, 'YYYY-MM-DDTHH:mm:ss', true).isValid()
          if (d === true || dt === true) {
            return true
          } else {
            return ['<code>{0}</code> is not a valid date format. Please use <code>YYYY-MM-DD</code> or <code>YYYY-MM-DDTHH:mm:ss</code>.', value]
          }
        }
      }
    },
    {
      'id': 'version',
      'label': 'version',
      'type': 'string',
      'size': 30
    }
  ]

  // Query Builder options
  var options = {
    allow_empty: true,
    filters: schema,
    default_filter: 'name',
    icons: {
      add_group: 'fa fa-plus-square',
      add_rule: 'fa fa-plus-circle',
      remove_group: 'fa fa-minus-square',
      remove_rule: 'fa fa-minus-circle',
      error: 'fa fa-exclamation-triangle'
    }
  }

  // Instantiate the Query Builder
  $('#builder').queryBuilder(options)

  // Update the query textarea when the query builder changes
  $('#builder').change(function () {
    var outputQueryString = JSON.stringify($('#builder').queryBuilder('getMongo'))
    $('#db-query').html(outputQueryString)
  })

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
  // When the Test Query button is clicked, validate and create a querystring
  $('#test-query').click(function (e) {
    e.preventDefault()
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery()
    if (formvals !== false) {
      $.ajax({
        method: 'POST',
        url: '/projects/test-query',
        data: JSON.stringify(formvals),
        contentType: 'application/json;charset=UTF-8',
      })
        .done(function (response) {
          bootbox.alert(response)
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

  // When the Get Query button is clicked, validate and create a querystring
  $('.dropdown-item').click(function () {
    var btnId = $(this).attr('id').replace('-btn', '')
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery([])
    if (formvals !== false) {
      launchJupyter(btnId, formvals)
    }
  })

  // When the Export button is clicked, validate and create a querystring
  $('#export').click(function (e) {
    e.preventDefault()
    // var requiredFields = ['name', 'metapath', 'namespace', 'title', 'contributors', 'created', 'db-query']
    var formvals = validateQuery([])
    if (formvals !== false) {
      exportProject(formvals)
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
