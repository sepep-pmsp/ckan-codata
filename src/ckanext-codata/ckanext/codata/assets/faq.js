ckan.module('codata-module', function($, _) {
    return {
      initialize: function() {
        // Hide all accordion-content elements initially
        this.el.find('.accordion-content').hide();
  
        // Bind click event on each accordion header
        this.el.find('.accordion-header').on('click', function() {
          var $header = $(this);
          // Toggle active class on header for styling (optional)
          $header.toggleClass('active');
          // Toggle the visibility of the next .accordion-content element
          $header.next('.accordion-content').slideToggle(200);
        });
      }
    };
  });
  