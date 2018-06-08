/* This code has not yet been converted from Angular */

var queue_server = "http://localhost:8081";
  var app = angular.module("myTasksList", []);
  app.controller("myCtrl", function($scope) {
    var tasks = JSON.parse(sessionStorage.tasks || "[]");
    $scope.tasks = [];
    for (var i in tasks) {
      $scope.tasks.push(tasks[i]);
    }
    $scope.checkStatus = function(task) {
      // Send the GET request to server
      if (task.status !== "FINISHED" && task.status !== "FAILED") {
        $.ajax({
          type: "GET",
          url: queue_server + "/api/status/" + task.task_id,
          success: function(response) {
            if (response.success) {
              task.status = response.status;
              if (task.status === "FINISHED" || task.status === "FAILED") {
                $scope.getResult(task);
              }
            } else {
              task.status = "UNKNOWN";
            }
            $scope.$apply();
          },
          contentType: 'application/json'
        });
      }
    };
    $scope.getResult = function(task) {
      // Send the GET request to server
      $.ajax({
        type: "GET",
        url: queue_server + "/api/result/" + task.task_id,
        success: function(response) {
          if (response.success) {
            task.result = response.result;
          } else {
            task.status = "UNABLE TO GET THE RESULT.";
          }
          sessionStorage.tasks = JSON.stringify($scope.tasks);
          $scope.$apply();
        },
        contentType: 'application/json'
      });
    };
    $scope.addNewTask = function(task_name, n_seconds, task_result, depend, incompatible) {
      // Send the POST request to server
      $.ajax({
        type: "POST",
        url: queue_server + "/api/enqueue",
        data: JSON.stringify({
          fn: 'foo',
          args: [n_seconds, task_result],
          depend: [],
          incompatible: []
        }),
        success: function(response) {
          if (response.success) {
            $scope.tasks.push({
              task_id: response.task_id,
              task_name: task_name,
              depend: depend,
              incompatible: incompatible,
              status: "UNKNOWN",
              result: "-"
            })
            $scope.$apply();
            sessionStorage.tasks = JSON.stringify($scope.tasks);
            alert("New task was succesfully enqueued!");
          } else {
            alert("Oops! Something went wrong when trying to enqueue your new task!");
          }
        },
        contentType: 'application/json'
      });
    }
    $scope.clearTasks = function() {
      $scope.tasks = [];
      sessionStorage.tasks = JSON.stringify($scope.tasks);
    }
    //Launch the intervar
    setInterval(function() {
      for (var i in $scope.tasks) {
        $scope.checkStatus($scope.tasks[i])
      }
    }, 2000);
  });