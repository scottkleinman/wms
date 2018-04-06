//
// General Helper Functions
//

function jsonifyForm(formObj) {
	/* Handles JSON form serialisation */
    var form = {};
    $.each(formObj.serializeArray(), function (i, field) {
        form[field.name] = field.value || "";
    });
    return form;
}

//
// Ajax Functions
//

function createManifest(jsonform) {
	/* Creates a new manifest
	   Input: A JSON serialisation of the form values
	   Returns: A copy of the manifest and an array of errors for display */
	manifest = JSON.stringify(jsonform, null, '  ');
	$.ajax({
		method: "POST",
		url: "/corpus/create-manifest",
		data: manifest,
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		var manifest = JSON.parse(response)['manifest'];
		var errors = JSON.parse(response)['errors'];
		if (errors != '') {
			msg = '<p>Could not save the manifest because of the following errors:</p>' + errors;
		}
		else {
			msg = '<p>Saved the following manifest:</p>' + manifest;
		}
	    bootbox.alert({
        message: msg,
        callback: function () {
            // window.location = '/corpus';
        }
	    });
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
	    bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>'+response,
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


function deleteManifest(name) {
	/* Deletes a manifest
	   Input: A name value
	   Returns: An array of errors for display */
	$.ajax({
		method: "POST",
		url: "/corpus/delete-manifest",
		data: JSON.stringify({"name": name}),
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		var errors = JSON.parse(response)['errors'];
		if (errors != '') {
			msg = '<p>Could not delete the manifest because of the following errors:</p>' + errors;
		}
		else {
			msg = '<p>The manifest for <code>' + name + '</code> was deleted.</p>';
		}
	    bootbox.alert({
        message: msg,
        callback: function () {
            window.location = '/corpus';
        }
	    });
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
	    bootbox.alert({
        message: '<p>The manifest could not be saved because of the following errors:</p>'+response,
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


function exportSearch(data) {
	/* Exports the results of a Corpus search
	   Input: Values from the search form
	   Returns: An array containing results and errors for display */
	$.ajax({
		method: "POST",
		url: "/corpus/export-search",
		data: JSON.stringify(data),
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		response = JSON.parse(response);
		if (response['errors'].length != 0) {
			result = JSON.stringify(response['errors']);
		    bootbox.alert({
	        message: '<p>Sorry, mate! You\'ve got an error!</p><p>' + result + '</p>',
	        callback: function () {
	            ("Error: " + textStatus + ": " + errorThrown);
	        }
		    });
		} else {
			window.location = '/corpus/download-export/' + response['filename'];
		}
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
	    bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


function searchCorpus(data) {
	/* Searches the Corpus
	   Input: Values from the search form
	   Returns: An array containing results and errors for display */
	$.ajax({
		method: "POST",
		url: "/corpus/search",
		data: JSON.stringify(data),
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		$('#results').empty();
		response = JSON.parse(response);
		if (response['errors'].length != 0) {
			result = response['errors'];
			var message = '';
			$.each(result, function (i, item) {
				message += '<p>' + item + '</p>';
			});
		    bootbox.alert({
		        message: message
		    });
		} else {
			result = response['response'];
			// Make the result into a string
			var out = '';
			$.each(result, function (i, item) {
				var link = '/corpus/display/' + item['name'];
				out += '<h4><a href="' + link + '">' + item['name'] + '</a></h4><br>';
				$.each(item, function (key, value) {
					value = JSON.stringify(value);
					if (key == 'content' && value.length > 200) {
						value = value.substring(0,200) + '...';
					}
			        out += '<code>'+ key +'</code>: ' + value + '<br>';
		        });
				out += '<hr>';
		    });
		    var $pagination = $('#pagination');
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
		            searchCorpus(newdata);
		            $('#scroll').click();
		        }
		    };
	        var totalPages = parseInt(response['num_pages']);
	        var currentPage = $pagination.twbsPagination('getCurrentPage');
	        $pagination.twbsPagination('destroy');
	        $pagination.twbsPagination($.extend({}, defaultOpts, {
	            startPage: currentPage,
	            totalPages: totalPages
	        }));
			$('#results').append(out);
			$('#hideSearch').html('Show Form');
			$('#exportSearchResults').show();
			$('#search-form').hide();
	        $('#results').show();
	        $('#pagination').show();
		}
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
	    bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


function sendExport(jsonform) {
	/* Sends the export options to the server
	   Input: A serialised set of form values from the export modal
	   Returns: The name of the file to download.
	   Automatically redirects to the download function. */
	$.ajax({
		method: "POST",
		url: "/corpus/send-export",
		data: JSON.stringify(jsonform),
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		filename = JSON.parse(response)['filename'];
		// $('.modal-body').html(filename);
		$('#exportModal').modal('hide');
	    // bootbox.alert({
	    //     message: filename
	    // });
	    window.location = '/corpus/download-export/' + filename;
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
		$('#exportModal').modal('hide');
	    bootbox.alert({
        message: '<p>Sorry, mate! You\'ve got an error!</p>',
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


function updateManifest(jsonform, name) {
	/* Updates the displayed manifest
	   Input: A JSON serialisation of the form values
	   Returns: A copy of the manifest and an array of errors for display */
	manifest = JSON.stringify(jsonform, null, '  ');
	$.ajax({
		method: "POST",
		url: "/corpus/update-manifest",
		data: manifest,
		contentType: 'application/json;charset=UTF-8',
	})
	.done(function(response) {
		var manifest = JSON.parse(response)['manifest'];
		var errors = JSON.parse(response)['errors'];
		if (errors != '') {
			msg = '<p>Could not update the manifest because of the following errors:</p>' + errors;
		}
		else {
			msg = '<p>Updated the following manifest:</p>' + manifest;
		}
	    bootbox.alert({
        message: msg,
        callback: function () {
            window.location = '/corpus';
        }
	    });
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
	    bootbox.alert({
        message: '<p>The manifest could not be updated because of the following errors:</p>'+response,
        callback: function () {
            ("Error: " + textStatus + ": " + errorThrown);
        }
	    });
	});
}


//
// $(document).ready() Event Handling
//

$(document).ready(function() {

	//
	// Index Page Functions
	//

	/* Handles the Display form on the index page */
	$('#go').click(function(e){
		var name = $('#display').val();
		window.location = '/corpus/display/' + name; 
	});
	$('#display').on('keypress',function(e){
	 var key = (e.keyCode || e.which);
	    if(key == 13 || key == 3){
	       $('#go').click();
	    }
	});


	//
	// Create and Display Page Functions
	//

	/* Handles the manifest preview and hide buttons */
	$('#preview').click(function(e){
		e.preventDefault();
		$('form').hide();
		$('#previewDisplay').show();
		var jsonform =  jsonifyForm($('#manifestForm'));
		$('#manifest').html(JSON.stringify(jsonform, null, '  '));
	});

	$('#hide').click(function(e){
		e.preventDefault();
		$('#previewDisplay').hide();
		$('form').show();
	});


	//
	// Create Page Functions
	//

	/* Handles form submission for record creation*/
	$($('#manifestForm')).on('submit',function(e) {
		e.preventDefault();
		if ($(this).parsley().isValid()) {
			var jsonform = jsonifyForm($('#manifestForm'));
		 	createManifest(jsonform);
		}
	});


	/* Handles the nodetype buttons for creating manifests */
	$('input[name="nodetype"]').click(function(e) {
		var val = $(this).val();
		var setting = val.toLowerCase();
		switch (true) {
			case setting == 'collection' || setting == 'rawdata' || setting == 'processeddata':
			var template = $('#' + setting + '-template').html();
			$('#manifestCard').html(template);
			break;
			case setting == 'branch':
			var template = $('#branch-template').html();
			$('#manifestCard').html(template);
			break;
			default:
			var template = $('#generic-template').html();
			$('#manifestCard').html(template);
			$('#name').val(',' + val + ',');
		}
		$('.nav-tabs a[href="#required"]').tab('show');
	});


	//
	// Display Page Functions
	//

	/* Makes the global template available to scripts for the display page*/
	var globalTemplate = $('#global-template').html();


	/* If this is the display page, use the correct form for the 
	   manifest's nodetype */
	var page_url = document.URL.split('/');
	if (page_url[page_url.length-2] == 'display') {
		template = $('#' + nodetype + '-template').html();
		$('#manifestCard').html(template).append(globalTemplate);
	}


	/* Toggles the Edit/Update button and field disabled property */
	$('#update').click(function(e){
		e.preventDefault();
		if ($('#update').html() == 'Edit') {
			$('form').find('input, textarea, select').each(function(){
				if ($(this).attr('id') != 'name' && $(this).attr('id') != 'manifest-content') {
					$(this).prop('readonly', false);
					$(this).removeClass('disabled');
				}
				if ($(this).attr('id') == 'path' && nodetype == 'collection') {
					$(this).prop('readonly', true);	
					$(this).addClass('disabled');
				}
			});
			$('#update').html('Update');
		} else {
	    	var name = $('#name').val();
		    bootbox.confirm({
		        message: 'Are you sure you wish to update the record for <code>' + name + '</code>?',
		        buttons: {
		            confirm: {label: 'Yes', className: 'btn-success'},
		            cancel: {label: 'No', className: 'btn-danger'}
		        },
		        callback: function (result) {
		        	if (result == true) {
		        		var name = $('#name').val();
		        		var path = $('#path').val();
		        		var jsonform =  jsonifyForm($('#manifestForm'));
		        		$.extend(jsonform, {'name': name});
		        		$.extend(jsonform, {'path': path});
		        		updateManifest(jsonform, name);
		        	}
		        }
		    });
		}
	});


	/* Handles the Delete button */
	$('#delete').click(function(e){
		e.preventDefault();
    	var name = $('#name').val();
	    bootbox.confirm({
	        message: 'Are you sure you wish to delete <code>' + name + '</code>?',
	        buttons: {
	            confirm: {label: 'Yes', className: 'btn-success'},
	            cancel: {label: 'No', className: 'btn-danger'}
	        },
	        callback: function (result) {
	        	if (result == true) {
	        		deleteManifest(name);
	        	}
	        }
	    });
    });


	/* Handles the Export feature */
	$('#export').click(function(e) {
		e.preventDefault();
	    $('#exportModal').modal();
	});

	/* Handles behaviour when Select All is changed */
	$('#selectall').change(function(e) {
		if ($(this).is(":checked")) {
			$('.exportchoice').prop('checked', true);
			$('#manifestonly').prop('checked', false);		
		} else {
			$('.exportchoice').prop('checked', false);
		}
	});

	/* Handles behaviour when Manifest Only is changed */
	$('#manifestonly').change(function(e) {
		if ($(this).is(":checked")) {
			$('.exportchoice').prop('checked', false);
			$('#selectall').prop('checked', false);
		}
		$(this).prop('checked', true);	
	});

	/* Serialises the export options and initiates the export */
	$('#doExport').click(function(e) {
		// Get an array of export options
		var opts = {'exportoptions': []};
		$('.exportchoice:checked').each(function() {
		   opts['exportoptions'].push(this.value); 
		});
		var jsonform = jsonifyForm($('#manifestForm'));
		$.extend(jsonform, opts);
		sendExport(jsonform);
	});


	//
	// Import Page Functions
	//

	/* Change the metadata form in import */
	$('#category').change(function() {
		var selected = $(this).val().toLowerCase();
		if (selected == 'rawdata' || selected == 'processeddata') {
			template = $('#' + selected + '-template').html();
		} else {
			template = $('#generic-template').html();
		}
		$('#metadataCard').html(template).append(globalTemplate);
	});


	/* Change the Show/Hide Metadata Button */
	$('#collapseOne').on('shown.bs.collapse', function () {
	  $('#showMetadata').text('Hide Metadata');
	});
	$('#collapseOne').on('hidden.bs.collapse', function () {
	  $('#showMetadata').text('Show Metadata');
	});


	//
	// Search Page Functions
	//

	/* Handles the Search feature */
	$('#searchCorpus').click(function(e) {
		e.preventDefault();
		data = {
			'query': $('#query').val(),
			'regex': $('#regex').is(':checked'),
			'limit': $('#limit').val(),
			'properties': $('#properties').val(),
			'page': 1
		}
		searchCorpus(data);
	});


	// /* Handles the Search Export feature */
	// $('#exportSearchResults').click(function(e) {
	// 	e.preventDefault();
	// 	// data = {
	// 	// 	'query': $('#query').val(),
	// 	// 	'regex': $('#regex').is(':checked'),
	// 	// 	'limit': $('#limit').val(),
	// 	// 	'properties': $('#properties').val(),
	// 	// 	'page': 1,
	// 	// 	'paginated': false
	// 	// }
	// 	var querystring = JSON.stringify($('#builder').queryBuilder('getMongo'), undefined, 2);
	// 	var advancedOptions = JSON.stringify(serialiseAdvancedOptions(), undefined, 2);	
	// 	data = {
	// 		'query': JSON.parse(query),
	// 		'advancedOptions': JSON.parse(advancedOptions),
	// 		'paginated': false
	// 	};
	// 	alert(JSON.stringify(data));
	// 	exportSearch(data);
	// });


	/* Toggles the search form */
	$('#hideSearch').click(function(){
		if ($('#hideSearch').html() == 'Hide Form') {
			$('#search-form').hide();
			$('#exportSearchResults').show();
			$('#results').show();	
			$('#pagination').show();		
			$('#hideSearch').html('Show Form');
		} else {
			$('#hideSearch').html('Hide Form');
			$('#exportSearchResults').hide();
			$('#results').hide();
			$('#pagination').hide();			
			$('#search-form').show();
		}
	});

	/* Handles the pagination buttons */
	$('.page-link').click(function(e){
		e.preventDefault();
		data = {
			'query': $('#query').val(),
			'regex': $('#regex').is(':checked'),
			'limit': $('#limit').val(),
			'properties': $('#properties').val(),
			'page': $(this).html()
		}
	    searchCorpus(data);
	});

}); /* End of $(document).ready() Event Handling */
