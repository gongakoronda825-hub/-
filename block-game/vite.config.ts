import { defineConfig } from 'vite';

export default defineConfig({
  // 実機確認は `npm run dev` (= vite --host) でPCのLAN IPを開く。
  base: './',
  server: { host: true },
  build: {
    target: 'es2020',
    // three.js を含むので 500kB の警告は出るのが正常。
    chunkSizeWarningLimit: 800,
    // build-single.js が1ファイルに束ねられるよう、出力を分割しない。
    rollupOptions: {
      output: {
        codeSplitting: false,
        entryFileNames: 'assets/bundle.js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
});
