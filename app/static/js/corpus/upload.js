//
// Dropzone implementation for uploading files in Import
//

/* Get the previe template and remove it from the DOM */
var previewNode = document.querySelector("#template");
previewNode.id = "";
var previewTemplate = previewNode.parentNode.innerHTML;
previewNode.parentNode.removeChild(previewNode);

/* Initiate the dropzone in the document body */
var myDropzone = new Dropzone(document.body, {
  url: "/corpus/upload",
  acceptedFiles: '.json, .zip',
  thumbnailWidth: 80,
  thumbnailHeight: 80,
  parallelUploads: 20,
  previewTemplate: previewTemplate,
  autoQueue: false, // Make sure the files aren't queued until manually added
  previewsContainer: "#previews", // Define the container to display the previews
  clickable: ".fileinput-button" // Define the element that should be used as click trigger to select files.
});

/* When an individual file is added, add the start button */
myDropzone.on("addedfile", function(file) {
  file.previewElement.querySelector(".start").onclick = function() {
    myDropzone.enqueueFile(file);
  };
});

/* When the delete button is clicked, remove the file.
   Dropzone removes the file from the UI; the ajax removes
   it from server and deletes its database entry, if any. */
myDropzone.on("removedfile", function(file) {
  var form = jsonifyForm($('#metadataForm'));
  $.extend(form, {"filename": file.name});
  $.ajax({
    method: "POST",
    url: "/corpus/remove-file",
    data: JSON.stringify(form),
    contentType: 'application/json;charset=UTF-8',
  })
  .done(function(response) {
    console.log(JSON.parse(response)['response']);
  });
});

/* Update the total progress bar */
myDropzone.on("totaluploadprogress", function(progress) {
  var bar = document.querySelector("#total-progress .progress-bar");
  bar.style.width = progress + "%";
});

/* Show the total progress bar when uploading starts */
myDropzone.on("sending", function(file) {
  document.querySelector("#total-progress").style.opacity = "1";
  /* And disable the start button */
  file.previewElement.querySelector(".start").setAttribute("disabled", "disabled");
});

/* Hide the total progress bar when nothing's uploading anymore */
myDropzone.on("queuecomplete", function(progress) {
  document.querySelector("#total-progress").style.opacity = "0";
  var form = jsonifyForm($('#metadataForm'));
  $.ajax({
    method: "POST",
    url: "/corpus/save-upload",
    data: JSON.stringify(form),
    contentType: 'application/json;charset=UTF-8',
  })
  .done(function(response) {
    response = JSON.parse(response);
    if (response['errors']) {
      //alert(JSON.stringify(response['errors']));
      var error_files = []
      $.each(response['errors'], function(index, value) {
        value = value.replace('The <code>name</code> <strong>', '')
        value = value.replace('</strong> already exists in the database.', '')
        value += '.json'
        error_files.push(value);
      });
      $('[data-dz-name]').each(function() {
        if($.inArray($(this).html(), error_files) !== -1) {
          $(this).next().html('The file could not be imported because a manifest with the same <code>name</code> already exists in the database.');
        }
      });
      msg = '<p>The import contained one or more errors. See the individual files below for details.</p>';
      bootbox.alert({
        message: msg + '<p>' + JSON.stringify(error_files) + '</p>'
      });  
    } else {
      bootbox.alert({
        message: '<p>The data was imported successfully.</p>'
      });  
    }
  });
  $('#cancelAll').html('<i class="fa fa-trash"></i> <span>Delete all</span>');
});

/* Setup the buttons for all transfers.
   The "add files" button doesn't need to be setup because the config
   `clickable` has already been specified. */
document.querySelector("#actions .start").onclick = function() {
  myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED));
};
document.querySelector("#actions .cancel").onclick = function() {
  myDropzone.removeAllFiles(true);
  $('#cancelAll').html('<i class="fa fa-ban"></i> <span>Cancel upload</span>');
};