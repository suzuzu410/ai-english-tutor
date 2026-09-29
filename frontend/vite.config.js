import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite' // 1. 导入插件

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // 2. 添加插件
  ],
})