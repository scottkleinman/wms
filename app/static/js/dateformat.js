(function ($) {

  $.fn.dateformat = function (settings) {
    settings = $.extend({ settingA: 'defaultA', settingB: 'defaultB' }, settings);
    var k = $(this).attr('id')
    let a = "#" + $(this).attr('id') + "_dateformat"
    let b = "#" + $(this).attr('id') + "_list"
    let d = "#" + $(this).attr('id') + "_getdatevalue"
    let p = a + " :input"
    let html = '<ol id="' + $(this).attr('id') + '_list"><li id="concatenate"><p class="datep" style="display:inline-block !important; width: 200px !important;">start date: <input id="' + $(this).attr('id') + '_ds_0" name="0" size="16" type="text" value="" class="datepicker date"></p><p class="datep" style="display:inline-block !important; width: 200px !important;">end date: <input id="' + $(this).attr('id') + '_de_0" name="0" size="16" type="text" value="" class="datepicker date "></p></li></ol><button id="add_date" type="button" class="btn btn-lg btn-outline-editorial">ADD DATE</button><button id="' + $(this).attr('id') + '_getdatevalue" type="button" class="btn btn-lg btn-outline-editorial">SUBMIT</button>'
    $(a).append(html)


    $('.datepicker').datepicker({
      dateFormat: 'yy-mm-dd', // check change
      timeFormat: 'hh:mm:ss',
      constrainInput: false
    }).on('change', function () {
      if (moment($(this).val()).isValid()) {
        document.getElementById($(this).attr('id')).setAttribute('class', 'is-valid form-control datepicker date')
      } else if ($(this).val() == '') {
        document.getElementById($(this).attr('id')).setAttribute('class', 'datepicker date')
      } else {
        document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
      }
    })

    var counter = 0

    function dict(name, id, value) {
      this.name = name
      this.id = id
      this.value = value
    }

    $('#add_date').on('click', function () {
      counter = counter + 1
      let elem = '<li id="concatenate"><label class="col-form-label" for="ds_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">start date: <input id="' + $(this).attr('id') + '_ds_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date"></p><label class="col-form-label" for="de_' + counter + '"></label><p class="datep" style="display:inline-block !important; width: 200px !important;">end date: <input id="' + $(this).attr('id') + '_de_' + counter + '" name="' + counter + '" size="16" type="text" value="" class="datepicker date "></p><button type="button" class="remove_date btn btn-lg btn-outline-editorial">-</button></li>'

      console.log(b)
      $(b).append(elem)
      $('.datepicker').datepicker({
        dateFormat: 'yy-mm-dd', // check change
        timeFormat: 'hh:mm:ss',
        constrainInput: false
      }).on('change', function () {
        if (moment($(this).val()).isValid()) {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-valid form-control datepicker date')
        } else if ($(this).val() == '') {
          document.getElementById($(this).attr('id')).setAttribute('class', 'datepicker date')
        } else {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
        }
      })
      return false // prevent form submission
    })

    $('ol').on('click', '.remove_date', function () {
      $(this).parent().remove()
      return false
    })


    $(d).click(function () {
      var map = []
      var alerterror = 0
      $(p).map(function () {
        console.log($(this).parents("li").index() + " " + $(this).val())
        var date = new dict($(this).attr('name'), $(this).parents("li").index(), $(this).val())
        if (moment(date.value).isValid() || date.value == '') {
          map.push(date)
        } else {
          document.getElementById($(this).attr('id')).setAttribute('class', 'is-invalid form-control datepicker date')
          if (alerterror < 1) {
            bootbox.alert('please re-enter the correct format. Valid formats are YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS')
          }
          date.value = 'invalid_format'
          map.push(date)
          alerterror++
        }
      })
      var s = ''
      let t = 0
      for (var i = 1; i < map.length; i++) {
        switch (true) {
          case (map[i].value == ""):
            if (map[i].id != map[i - 1].id) {
              t = 1
            }
            s = s + ""
            break
          case (map[i].value != ""):
            if (map[i].name != map[i - 1].name) {
              s = s + "\r\n" + map[i].value
            }
            else {
              if (map[i].id != map[i - 1].id || t == 1) {
                s = s + "\r\n" + map[i].value
              }
              else {
                s = s + "," + map[i].value
              }
            }
            break
        }
      }
      s = map[0].value + s
      document.getElementById(k).value = s
    })
  };//end of plugin function
})(jQuery);
