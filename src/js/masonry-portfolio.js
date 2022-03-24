
//= ../../node_modules/imagesloaded/imagesloaded.pkgd.js
//= ../../node_modules/isotope-layout/dist/isotope.pkgd.js
//= ../../node_modules/infinite-scroll/dist/infinite-scroll.pkgd.js

document.addEventListener("DOMContentLoaded", function() {

	const searchContainer = null;
	//= components/_init.js
	//= components/_lazyLoad.js
	//= components/_ajax.js
	//= components/_alert.js
	//= components/_sendMessage.js

	lazyloadInit();

	var container = document.querySelector('.portfolio-container');
	var grid;

	imagesLoaded( container, function() {
  		// init Isotope after all images have loaded
		grid = new Isotope( container, {
			itemSelector: '.grid-item',
			columnWidth: '.grid-sizer',
			percentPosition: true,
			//columnWidth: 450,
			//isFitWidth: true
			// nicer reveal transition
			visibleStyle: { transform: 'translateY(0)', opacity: 1 },
			hiddenStyle: { transform: 'translateY(100px)', opacity: 0 },
		});
		container.classList.remove('loading')
	});


	let infScroll = new InfiniteScroll( container, {
		path: '.pagination__next',
		append: '.grid-item',
		status: '.page-load-status',
		hideNav: '.pagination',
		outlayer: grid,
		history: false,
	});

	infScroll.imagesLoaded = imagesLoaded;


	// bind filter button click
	var filtersElem = document.querySelector('.filters-group');
	filtersElem.addEventListener( 'click', function( event ) {
		// only work with buttons
		if ( !matchesSelector( event.target, 'button' ) ) return;

		var filterValue = event.target.getAttribute('data-filter');
		grid.arrange({ filter: filterValue });
	});

	// change is-checked class on buttons
	var buttonGroups = document.querySelectorAll('.button-group');
	for ( var i=0, len = buttonGroups.length; i < len; i++ ) {
		var buttonGroup = buttonGroups[i];
		radioButtonGroup( buttonGroup );
	}

	function radioButtonGroup( buttonGroup ) {
		buttonGroup.addEventListener( 'click', function( e ) {
			// only work with buttons
			if ( !matchesSelector( e.target, 'button' ) ) return;

			filtersElem.querySelector('.is-checked').classList.remove('is-checked');
			e.target.classList.add('is-checked');
		});
	}


});