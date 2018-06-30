// Configure the PySiQ server or use Flask for testing
var queueServer = 'http://localhost:8081'
queueServer = 'http://127.0.0.1:5000/tasks'

//
// General Helper Functions
//

function jsonifyForm () {
  // Handles JSON form serialisation
  var form = {}
  $.each($('form').serializeArray(), function (i, field) {
    form[field.name] = field.value || ''
  })
  return form
}

// Check Status
function checkStatus (task) {
  // Send the GET request to server
  if (task.status !== 'FINISHED' && task.status !== 'FAILED') {
    $.ajax({
      type: 'GET',
      url: queueServer + '/api/status/' + task.task_id,
      success: function (response) {
        console.log(response)
        response = JSON.parse(response)
        if (response.success) {
          var status = response.status
          if (status === 'FINISHED' || status === 'FAILED') {
            getResult(task)
          }
          $('#task-' + task.task_id).html(response.status)
          $('#taskResult-' + task.task_id).html(response.result)
          $('#task-' + task.task_id).removeClass().addClass('label label-info')
        } else {
          $('#task-' + task.task_id).html(response.status)
          $('#taskResult-' + task.task_id).html('UNKNOWN')
          $('#task-' + task.task_id).removeClass().addClass('label label-warning')
        }
      },
      contentType: 'application/json'
    })
  }
}

// Get Result
function getResult (task) {
  // Send the GET request to server
  $.ajax({
    type: 'GET',
    url: queueServer + '/api/result/' + task.task_id,
    success: function (response) {
      response = JSON.parse(response)
      if (response.success) {
        task.result = response.result
      } else {
        task.status = 'UNABLE TO GET RESULT'
      }
      sessionStorage.tasks = JSON.stringify(tasks)
    },
    contentType: 'application/json'
  })
}

// Add New Task
function addNewTask () {
  // Get the form vals
  var formVals = jsonifyForm()
  // Send the POST request to server
  $.ajax({
    type: 'POST',
    url: queueServer + '/api/enqueue',
    data: JSON.stringify(formVals),
    success: function (response) {
      response = JSON.parse(response)
      if (response.success) {
        tasks.push({
          task_id: response.id,
          task_name: formVals['task_name'],
          depend: [],
          incompatible: [],
          status: response.status,
          result: response.result
        })
        sessionStorage.tasks = JSON.stringify(tasks)
        var row = '<tr id="' + response.id + '" class="taskrow">'
        row += '<td>' + formVals['task_name'] + '</td>'
        row += '<td id="task-' + response.id + '">' + response.id + '</td>'
        row += '<td><span id="task-task.task_id" class="label label-primary">' + response.status + '</span></td>'
        row += '<td><span id="taskResult-task.task_id" class="label label-primary">' + response.result + '</span></td>'
        row += '<td><button type="button" data-delete="' + response.id + '" class="btn btn-sm btn-outline-editorial pull-right remove" title="Remove Task"><i class="fa fa-trash"></i></button></td>'
        row += '</tr>'
        $('#queueTable > tbody').append(row)
        bootbox.alert('New task was succesfully enqueued!')
      } else {
        bootbox.alert('Oops! Something went wrong when trying to enqueue your new task!')
      }
    },
    contentType: 'application/json'
  })
}

// Clear Tasks
function clearTasks () {
  tasks = []
  sessionStorage.tasks = JSON.stringify(tasks)
}

// Launch the interval
setInterval(function () {
  for (var i in tasks) {
    checkStatus(tasks[i])
  }
}, 2000)

$(document).ready(function () {
  // Add New Task
  $('#queuetask').click(function (e) {
    e.preventDefault()
    addNewTask()
  })

  // Clear Tasks
  $('#clear').click(function (e) {
    e.preventDefault()
    clearTasks()
    $('.taskrow').remove()
  })
})

// Remove a Task
$(document).on('click', '.remove', function () {
  const removeId = $(this).attr('data-delete')
  tasks.splice($.inArray(removeId, tasks), 1)
  sessionStorage.tasks = JSON.stringify(tasks)
  $('#' + removeId).remove()
})
