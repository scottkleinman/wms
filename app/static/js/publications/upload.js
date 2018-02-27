/* Publications */
$(function () {
   // do photo uploads
   $('#fileupload').fileupload({
       dataType: 'json',
       enctype: 'multipart/form-data',
       add: function (e, data) {
           var picker = $(this).data('link');
           $(picker).children('span').html('check');
           data.submit();
           /*
           data.context = $('<button/>').text('Upload')
               .appendTo(document.body)
               .click(function () {
                   data.context = $('<p/>').text('Uploading...').replaceAll($(this));
                   data.submit();
                   });
            */
       },
       beforeSend: function () {
           $('#progress').show();
       },
       done: function (e, data) {
       	   $('#progress').html('<p>Importing...</p>');
       	   var filenames = data.result;
	   	    bootbox.alert({
	        message: function () {
	           var msg = '';
	           $.each(filenames, function (index, file) {
	           	  if (file.errors.length == 0) {
	           	   msg += '<p>Successfully imported manifests from <code>' + file.name + '</code></p>';
	           	  } else {
	           	   msg += msg += '<p>Could not import manifests from <code>' + file.name + '</code> because of the following errors:</p>';
				   $.each(file.errors, function (i, error) {
					   msg +="<li>"+error+"</li>";      
				   });
	   	           msg += '</ul>';	           	   
	           	  }
	           });
	           return msg;
	        },
	        callback: function () {
	            window.location = '/publications';
	        }
		    });
           $('#progress').hide();
       },
       fail: function () {alert('The upload failed. We\'re not sure why.');},
       progressall: function (e, data) {
           var progress = parseInt(data.loaded / data.total * 100, 10);
           $('#progress .bar').css(
               'width',
               progress + '%'
           );
       }   
	});
});
