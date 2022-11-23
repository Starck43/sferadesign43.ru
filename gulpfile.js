/*
 * Gulpfile.js
 * Version: 2.0.0
 * Author: S.Shabalin
 */

var gulp 		 = require('gulp'),
	sass 		 = require('gulp-sass')(require('sass')),   // Подключаем SASS
	browserSync  = require('browser-sync').create(), // Подключаем Browser Sync
	concat       = require('gulp-concat'), // Подключаем gulp-concat (для слияния файлов)
	uglify       = require('gulp-uglify-es').default, // Подключаем плагин для сжатия JS
	ttf2woff2 	 = require('gulp-ttf2woff2'),
//	jsRequires   = require('gulp-resolve-dependencies'), // Подключаем пакет для импортирования скриптов через //@requires *.js
	include		 = require('gulp-include'), // импорт скриптов через //=require filename.js
	postcss      = require("gulp-postcss"),
	combineCSS   = require('gulp-group-css-media-queries'),  // Объединяет все @media
	cssImport    = require('postcss-import'),   // Подключаем пакет для импортирования кода css, прописанного через @import '*.css'
	cleanCSS     = require('gulp-clean-css'), // Подключаем пакет для минификации CSS с объединением одинаковых медиа запросов
	sourcemaps   = require('gulp-sourcemaps'), // Подключаем пакет sourcemaps для нахождения исходных стилей и скриптов в режиме dev-tool браузера
	rename       = require('gulp-rename'), // Подключаем библиотеку для переименования файлов
	//imgCompress  = require('imagemin-jpeg-recompress'), // Подключаем библиотеку для работы с изображениями
	autoprefixer = require('gulp-autoprefixer');// Подключаем библиотеку для автоматического добавления префиксов

var path = {
		src: 'src/', // Здесь хранятся исходные данные
		static: 'static/', // Путь до стилей, шрифтов, иконок
		html: 'templates/' // Путь до шаблонов
	}
var site = {
		http: 'localhost:7000' // здесь нужно указать адрес рабочего сайта, удаленного или локального
}


function styles() { // таск 'styles' обработает все файлы *.sass, вложенные в любые подпапки
	return gulp.src([path.src+'sass/**/*.+(sass|scss)'])
	//.pipe(sourcemaps.init()) //инициализируем soucemap
	.pipe(sass({ outputStyle: 'expanded' })) //  Опция { outputStyle: 'expanded' } развертывает все унификации
	.pipe(autoprefixer({
		grid: true,
		overrideBrowserslist: ['last 3 versions']
	})) // Создаем префиксы
	.pipe(combineCSS()) //Объединяем медиа запросы
	.pipe(postcss([ cssImport ])) // Импортируем стили, прописанные через команду @import в начале файла
	//.pipe(sourcemaps.init())
	.pipe(sass({
		outputStyle: 'compressed',
	}).on('error', sass.logError))
	//.pipe(sourcemaps.write()) //пропишем sourcemap
	//.pipe(concat('main.min.css')) // Объединяем все найденные файлы в один
	.pipe(rename({suffix: '.min'})) // Добавляем суффикс .min
	.pipe(gulp.dest(path.static+'css')) // Выгружаем результат в папку static::/css
	.pipe(browserSync.stream()) // Обновляем CSS на странице при изменении
};


// Скрипт компиляции скриптов
function scripts() {
	return gulp.src([path.src+'js/*.js'])
//	.pipe(sourcemaps.init()) // Инициализируем sourcemap
	.pipe(include()) //подключаем импортирование скриптов
//	.pipe(concat('custom.min.js')) // Объединяем в один файл
//	.pipe(uglify()) // Сжимаем JS файл
	.pipe(rename({suffix: '.min'})) // Добавляем суффикс .min
//	.pipe(sourcemaps.write()) // Пропишем карты
	.pipe(gulp.dest(path.static+'js')) // Выгружаем в папку dest::/js
	.pipe(browserSync.stream()) // Обновляем CSS на странице при изменении
};

function html() {
	return gulp.src([path.html+'**/*.html'])
	.pipe(browserSync.stream()) // Обновляем CSS на странице при изменении
};


// Скрипт сжатия стилей
function css_compress() {
	return gulp.src(path.static+'css/*.css') // Сжимаем библиотеки
	.pipe(cleanCSS({level:1})) // Сжимаем CSS файл
	//.pipe(rename({suffix: '.min'})) // Добавляем суффикс .min
	.pipe(gulp.dest(path.static+'css'))
};

// Скрипт сжатия скриптов
function scripts_compress() {
	return gulp.src(path.static+'js/*.js') // Сжимаем библиотеки
	.pipe(uglify()) // Сжимаем JS файл
	.pipe(gulp.dest(path.static+'js'))
};

//  Скрипт конвертации шрифтов TIFF в папке src/fonts в WOFF2 в папку static/fonts
function ttf_to_woff2() {
	return gulp.src(path.src+'fonts/*.ttf') // Сжимаем библиотеки
	.pipe(ttf2woff2())
	.pipe(gulp.dest(path.static+'fonts/'))
};

// Скрипт синхронизации контента в браузере
function browsersync() { // Создаем таск browser-sync
	browserSync.init({ // Определяем параметры сервера.
		//server: { baseDir: path.html },  // Нельзя подключать одновремено с proxy
		host: site.http,
		proxy: site.http,
		tunnel: false, tunnel: 'sd43', // Demonstration page: http://projectname.localtunnel.me
		notify: false, // Отключаем уведомления
		online: false, // false - work offline without internet connection
		open: false, // open browser on start
	})
};

// Deploy - выгрузка файлов на хостинг
function deploy() {
	return gulp.src(path.static+'')
	.pipe(rsync({
		root: path.static,
		hostname: 'username@sferadesign.ru',
		destination: 'sferadesign.ru/public_html/',
		//include: ['*.htaccess'], // Included files
		exclude: ['**/Thumbs.db', '**/*.DS_Store'], // Excluded files
		recursive: true,
		archive: true,
		silent: false,
		compress: true
	}))
};


// Скрипт слежения за изменениями файлов при сохранении.
function watch() { //таск слежения изменений в sass,css,html,php,js.
	gulp.watch([path.src +'sass/**/*.sass', path.src+'css/*.css'], styles); // Наблюдение за sass файлами в папке с исходниками sass и css
	gulp.watch([path.src +'js/**/*.js'], scripts); // Наблюдение за JS файлами
	gulp.watch([path.html+'**/*.html'], html); // Наблюдение за HTML файлами в папке templates
};

// Экспорт скриптов для публичного доступа (через командную строку в том числе)
exports.browsersync = browsersync;
exports.styles = styles;
exports.scripts = scripts;
exports.css_compress = css_compress;
exports.scripts_compress = scripts_compress;
exports.ttf_to_woff2 = ttf_to_woff2;


//Дефолтный таск для параллельного запуска необходимых процессов при запуске
exports.default = gulp.series(
	gulp.parallel(styles, scripts),
	gulp.parallel(browsersync, watch)
);
