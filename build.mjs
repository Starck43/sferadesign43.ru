#!/usr/bin/env node

import * as esbuild from 'esbuild';
import {sassPlugin} from 'esbuild-sass-plugin';
import postcss from 'postcss';
import autoprefixer from 'autoprefixer';
import postcssImport from 'postcss-import';
import {glob} from 'glob';
import path from 'path';
import {fileURLToPath} from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isWatch = process.argv.indexOf('--watch') !== -1;
const isDev = process.argv.indexOf('--dev') !== -1;

// 📁 Пути
const SRC_DIR = path.join(__dirname, 'src');
const DEST_DIR = path.join(__dirname, 'static');

const SRC_JS_DIR = path.join(SRC_DIR, 'js');
const SRC_SASS_DIR = path.join(SRC_DIR, 'sass');
const DEST_JS_DIR = path.join(DEST_DIR, 'js');
const DEST_CSS_DIR = path.join(DEST_DIR, 'css');

console.log('📦 Building project...');
console.log('Mode:', isDev ? 'Development' : 'Production');
console.log('Watch:', isWatch ? 'Enabled' : 'Disabled');

// ---------------------
// 🔍 Поиск JS файлов
// ---------------------
const jsFiles = glob.sync(path.join(SRC_JS_DIR, '*.js'), {
    ignore: [path.join(SRC_JS_DIR, 'components', '**')],
});

const jsEntryPoints = jsFiles.reduce((acc, file) => {
    const name = path.basename(file, '.js');
    acc[name] = file;
    return acc;
}, {});

// ---------------------
// 🔍 Поиск SASS файлов
// ---------------------
const sassFiles = glob.sync(path.join(SRC_SASS_DIR, '*.{sass,scss}'), {
    ignore: [path.join(SRC_SASS_DIR, '_*.{sass,scss}')],
});

const sassEntryPoints = sassFiles.reduce((acc, file) => {
    const name = path.basename(file).replace(/\.(sass|scss)$/, '');
    acc[name] = file;
    return acc;
}, {});

console.log('\nJS Entry Points:', Object.keys(jsEntryPoints));
console.log('SASS Entry Points:', Object.keys(sassEntryPoints));

// ---------------------
// ⚙️ JS CONFIG
// ---------------------
const jsConfig = {
    entryPoints: jsEntryPoints,
    bundle: true,
    minify: !isDev,
    sourcemap: isDev,
    target: ['es2020'],
    format: 'iife',
    outdir: DEST_JS_DIR,
    entryNames: '[name].min',
    loader: {
        '.js': 'js',
    },
    metafile: true, // <--- нужно для анализа CSS после сборки
    logLevel: 'info',
};

// ---------------------
// ⚙️ SASS CONFIG
// ---------------------
const sassConfig = {
    entryPoints: sassEntryPoints,
    bundle: true,
    minify: !isDev,
    sourcemap: isDev,
    outdir: DEST_CSS_DIR,
    entryNames: '[name].min',
    loader: {
        '.sass': 'css',
        '.scss': 'css',
    },
    logLevel: 'info',
    external: ['../fonts/*', '../images/*'],
    plugins: [
        sassPlugin({
            async transform(source) {
                const {css} = await postcss([
                    postcssImport,
                    autoprefixer({
                        grid: true,
                        overrideBrowserslist: ['last 3 versions'],
                    }),
                ]).process(source, {from: undefined});
                return css;
            },
        }),
    ],
};

// ---------------------
// 🧠 ПОСЛЕ СБОРКИ JS
// ---------------------
async function moveGeneratedCssFromJs(result) {
    if (!result.metafile) return;

    const outputs = Object.keys(result.metafile.outputs).filter(file =>
        file.endsWith('.css') || file.endsWith('.css.map')
    );

    function processFile(srcPath, destPath, fileType) {
        fs.mkdirSync(path.dirname(destPath), {recursive: true});

        if (fs.existsSync(destPath)) {
            fs.unlinkSync(destPath);
        }
        fs.renameSync(srcPath, destPath);

        const stats = fs.statSync(destPath);
        const size = (stats.size / 1024).toFixed(1);
        const relativePath = path.relative(__dirname, destPath);
        const padding = ' '.repeat(Math.max(42 - relativePath.length, 1));
        const formattedPath = `\x1b[37m${path.dirname(relativePath)}/${'\x1b[0m'}\x1b[1m${path.basename(relativePath)}\x1b[0m`;

        return {stats, size, relativePath, padding, formattedPath};
    }

    function logResult(formattedPath, padding, size, message, icon = '📦') {
        console.log(`${icon} ${formattedPath}${padding}\x1b[36m${size}kb\x1b[0m (${message})`);
    }

    function isEmptyFile(filePath) {
        const stats = fs.statSync(filePath);
        if (stats.size === 0) {
            fs.unlinkSync(filePath);
            console.log(`🧹 Removed empty: ${path.relative(__dirname, filePath)}`);
            return true;
        }
        return false;
    }

    // Обрабатываем CSS файлы
    for (const cssPath of outputs.filter(file => file.endsWith('.css'))) {
        const srcPath = path.resolve(cssPath);
        const fileName = path.basename(srcPath);
        const baseName = fileName.replace('.min.css', '');
        const destPath = path.join(DEST_CSS_DIR, fileName);

        // Пропускаем пустые CSS
        if (isEmptyFile(srcPath)) continue;

        const hasSassCounterpart = sassEntryPoints.hasOwnProperty(baseName);

        // Если целевой файл уже существует И есть SASS файл - объединяем
        if (fs.existsSync(destPath) && hasSassCounterpart) {
            const existingCss = fs.readFileSync(destPath, 'utf8');
            const newCss = fs.readFileSync(srcPath, 'utf8');
            const mergedCss = `${existingCss.trim()}\n\n${newCss.trim()}\n`;
            fs.writeFileSync(destPath, mergedCss, 'utf8');
            fs.unlinkSync(srcPath);

            const {size, formattedPath, padding} = processFile(destPath, destPath, 'css');
            logResult(formattedPath, padding, size, 'merged imports css + sass', '🪄');
        } else {
            // Просто перемещаем/заменяем файл
            const action = fs.existsSync(destPath) ? "replaced" : "moved";
            const {size, formattedPath, padding} = processFile(srcPath, destPath, 'css');
            const reason = hasSassCounterpart ? "no existing file" : "no sass counterpart";
            logResult(formattedPath, padding, size, `${action} imports css - ${reason}`);
        }
    }

    // Обрабатываем MAP файлы
    for (const mapPath of outputs.filter(file => file.endsWith('.css.map'))) {
        const srcPath = path.resolve(mapPath);
        const fileName = path.basename(srcPath);
        const destPath = path.join(DEST_CSS_DIR, fileName);

        const {size, formattedPath, padding} = processFile(srcPath, destPath, 'map');
        logResult(formattedPath, padding, size, 'sourcemap', '🗺️');
    }
}

// ---------------------
// 🚀 BUILD
// ---------------------
async function build() {
    try {
        // Сначала SASS - создаем базовые стили
        if (isWatch) {
            const sassContext = await esbuild.context(sassConfig);
            await sassContext.watch();
            console.log('👀 Watching SASS files for changes...');
        } else {
            await esbuild.build(sassConfig);
            console.log('✅ SASS build complete');
        }

        // Потом JS - добавляем стили из импортов к существующим SASS стилям
        if (isWatch) {
            const jsContext = await esbuild.context(jsConfig);
            await jsContext.watch();
            console.log('👀 Watching JS files for changes...');
        } else {
            const jsResult = await esbuild.build(jsConfig);
            console.log('✅ JavaScript build complete\n');
            await moveGeneratedCssFromJs(jsResult);
        }


        if (isWatch) {
            console.log('\n👀 Watching for changes... Press Ctrl+C to stop');
        } else {
            console.log('\n✅ Build completed successfully!');
        }
    } catch (error) {
        console.error('❌ Build failed:', error);
        process.exit(1);
    }
}

build();
