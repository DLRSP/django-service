$(document).ready(function() {
    'use strict';
    /*-----------------------------------------------------------------------------------*/
    /*	BACKGROUND IMAGE
    /*-----------------------------------------------------------------------------------*/
    $(".bg-image").css('background-image', function() {
        var bg = ('url(' + $(this).data("image-src") + ')');
        return bg;
    });

    /*-----------------------------------------------------------------------------------*/
    /*	LIGHTGALLERY
    /*-----------------------------------------------------------------------------------*/
    var $lgContainer = document.getElementById('inline-gallery-container');
    var lg = lightGallery($lgContainer, {
      container: $lgContainer,
      dynamic: true,
      hash: false,
      closable: false,
      showMaximizeIcon: true,
      download: false,
      slideShowAutoplay: true,
      slideDelay: 400,
      mode: 'lg-fade',
      appendSubHtmlTo: ".lg-item",
      plugins: [lgZoom, lgThumbnail, lgAutoplay],
      dynamicEl: $dynamicEl
    });

    setTimeout(() => {
      lg.openGallery();
    }, 500);


});