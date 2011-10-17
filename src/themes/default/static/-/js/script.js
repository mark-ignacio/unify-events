var sluggify = function(s) {return s.toLowerCase().replace(/\s/g, '-').replace(/[^A-Za-z-]/, '');}
var Webcom   = {};

/*
 * Dynamically add items to formsets.
 * From: http://stackoverflow.com/questions/501719/dynamically-adding-a-form-to-a-django-formset-with-ajax
 *
 */
function extend_formset(selector, type) {
	var newElement = $(selector).clone(true);
	var total = $('#id_' + type + '-TOTAL_FORMS').val();
	newElement.find(':input').each(function() {
		var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
		var id = 'id_' + name;
			$(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
	});
	newElement.find('label').each(function() {
		var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
			$(this).attr('for', newFor);
	});
	total++;
	$('#id_' + type + '-TOTAL_FORMS').val(total);
	$(selector).after(newElement);
}


/**
 * Handles various actions and behaviours for the variety of calendar widgets
 * througout the application
 **/
Webcom.calendarWidget = function($){
	$('.calendar-widget .month-controls a').live('click', function(){
 		var url    = $(this).attr('href');
		var parent = $(this).parents('.calendar-widget');
		$.ajax(url, {
			'success' : function(data){
				var replace = $(data);
				parent.replaceWith(replace);
			}
		});
		return false;
	});
	
	$('.calendar-widget .day a').live('click', function(){
		var elements_to_update = ['.subscribe-widget', '#left-column'];
		var url = $(this).attr('href');
		$.ajax(url, {
			'success' : function (data){
				var result = $(data);
				$.each(elements_to_update, function(){
					var find    = this.valueOf();
					var element = result.find(find);
					$(find).replaceWith(element);
				});
				
				var title = '';
				try{
					title = data.match(/<title>([^<]*)<\/title>/)[1];
				}catch(e){}
				history.pushState({}, title, url);
			}
		});
		
		return false;
	});
	
	
	var close_expanded_calendar = function(){
		var widget = $('.expanded-calendar-container .calendar-widget');
		$('.expanded-calendar-container').remove();
		$('.expanded-calendar-placeholder').replaceWith(widget);
	};
	
	$('.calendar-widget .expand').live('click', function(){
		var widget    = $(this).parents('.calendar-widget');
		var container = $('<div class="expanded-calendar-container"></div>');
		widget.replaceWith($('<div class="expanded-calendar-placeholder"></div>'));
		container.append(widget);
		$('body').append(container);
		
		$(document).keydown(function(e){
			//Escape
			if (e.keyCode == 27){
				close_expanded_calendar();
			}
			//Left
			if (e.keyCode == 37){
				$('.calendar-widget .month-controls .last-month a').click();
			}
			//Right
			if (e.keyCode == 39){
				$('.calendar-widget .month-controls .next-month a').click();
			}
		});
	});
	
	$('.expanded-calendar-container .calendar-widget .day a').live('click', function(){
		close_expanded_calendar();
	});
};


$().ready(function(){
	Webcom.calendarWidget($);
});