#!/usr/bin/env node
// Membangun extension Mind+ V2 "Robot LFM X1" memakai builder resmi DFRobot.
//
//   git clone https://gitee.com/mind-plus/mindplus-ext2-builder.git   (sekali saja, di luar repo ini)
//   cd mindplus-ext2-builder && npm install                            (sekali saja)
//   node <repo>/mindplus-ext/build.js <folder mindplus-ext2-builder>
//
// Yang dilakukan:
// 1. isi folder extension/ milik builder diganti dengan mindplus-ext/lfm-x1/
// 2. library C++ disalin dari firmware/lib/LineFollower ke extension/public/libraries/LineFollower
//    (satu sumber kode: library yang sama dipakai PlatformIO dan Mind+)
// 3. `npm run build` di builder
// 4. hasil build disalin ke mindplus-ext/build/<nama>; muat config.json di sana lewat
//    Mind+ V2 > Pengaturan > Opsi lanjutan > Mode pengembang, lalu Ekstensi > Muat ekstensi uji.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const builder = process.argv[2];
if (!builder || !fs.existsSync(path.join(builder, 'webpack.config.js'))) {
    console.error('Pakai: node build.js <folder mindplus-ext2-builder>');
    process.exit(1);
}

const here = __dirname;
const source = path.join(here, 'lfm-x1');
const library = path.join(here, '..', 'firmware', 'lib', 'LineFollower');
const target = path.join(builder, 'extension');

fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(source, target, { recursive: true });

const libTarget = path.join(target, 'public', 'libraries', 'LineFollower');
fs.mkdirSync(libTarget, { recursive: true });
fs.copyFileSync(path.join(library, 'library.properties'), path.join(libTarget, 'library.properties'));
fs.cpSync(path.join(library, 'src'), path.join(libTarget, 'src'), { recursive: true });

// webpack 4 di Node 17+ butuh penyedia OpenSSL lama
const env = Object.assign({}, process.env);
const major = parseInt(process.versions.node.split('.')[0], 10);
if (major >= 17 && !(env.NODE_OPTIONS || '').includes('openssl-legacy-provider')) {
    env.NODE_OPTIONS = `${env.NODE_OPTIONS || ''} --openssl-legacy-provider`.trim();
}
execSync('npm run build', { cwd: builder, stdio: 'inherit', env });

const config = JSON.parse(fs.readFileSync(path.join(source, 'public', 'config.json'), 'utf8'));
const name = `ext-${config.author}-${config.id}@${config.version}`;
const built = path.join(builder, 'build', name);
const out = path.join(here, 'build', name);
fs.rmSync(out, { recursive: true, force: true });
fs.cpSync(built, out, { recursive: true });
console.log(`\nSelesai: ${out}`);
console.log('Muat file config.json di folder itu lewat "Muat ekstensi uji" di Mind+ V2 (mode pengembang).');
