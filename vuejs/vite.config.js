import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';
import path from 'path';
import inject from '@rollup/plugin-inject';
import { visualizer } from 'rollup-plugin-visualizer';

// 環境変数をチェック
const report = process.env.VITE_REPORT === 'true';


export default defineConfig(({ mode }) => ({
  base: '/',
  define: {
    'process.env': {
      ...process.env,
      NODE_ENV: mode === 'development' ? 'development' : 'production',
    },
  },
  plugins: [
    vue(),
    inject({
      'cash': 'cash-dom',
      'Popper': ['@popperjs/core', 'default'],
    }),
    // 環境変数がtrueの場合にのみvisualizerプラグインを追加
    report && visualizer({ open: true, filename: 'dist/report.html' })
  ].filter(Boolean), // falseをフィルターするためにBooleanコンストラクタを使用
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8080,
    watch: {
      usePolling: true,
    },
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    }
  },
  build: {
    outDir: mode === 'production' ? 'dist-prod' : 'dist-dev',
    commonjsOptions: { transformMixedEsModules: true },
    rollupOptions: {
      output: {
        entryFileNames: `[name].[hash].js`,
        chunkFileNames: `[name].[hash].js`,
        assetFileNames: `[name].[hash].[ext]`
      },
      manualChunks(id) {
        if (id.includes('node_modules')) {
          return 'vendor';
        }
      },
    },
  },
}));