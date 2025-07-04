import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd());
  return {
    // 设置scss的api类型为modern-compiler
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    },
    
    plugins: [
      vue()
    ],
    server: {
      host: "0.0.0.0",
      port: 5180,
      open: true,
      proxy: {
        [env.VITE_APP_BASE_API]: {
          target: env.VITE_API_BASE_URL,
          secure: false, // 请求是否为https
          changeOrigin: true, // 是否跨域
          // rewrite: (path) => path.replace(/^\/api/, '')
        },
      },
    },
    resolve: {
      alias: {
        // 设置路径
        '~': resolve(__dirname, './'),
        // 设置别名
        '@': resolve(__dirname, './src')
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    build: {
      chunkSizeWarningLimit: 20 * 1024, // 打包文件大小限制
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              const module = id.toString().split('node_modules/')[1].split('/')[0]
              if (['birpc', 'hookable'].includes(module)) return // 排除无用 chunk
              return module
            }
          }
        }
      }
    },
  };
});
