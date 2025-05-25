# frontend

## 项目结构

```sh
fastapi_project/frontend
├─ public               # 静态资源文件 
│  └─ site              # 帮助文档模块
├─ src                  # 源代码
│  ├─ api               # 接口文件
│  ├─ components        # 组件模块
│  ├─ layouts           # 布局模块
│  ├─ router            # 路由模块
│  ├─ store             # 状态管理模块
│  ├─ utils             # 工具模块
│  ├─ view              # 视图模块
│  ├─ App.vue           # 根组件
│  ├─ main.js           # 入口文件
│  └─ styles.css        # 全局样式文件
├─ .env.development     # 项目开发环境配置
├─ .env.production      # 项目生产环境配置
├─ index.html           # 模板文件
├─ package.json         # 项目依赖文件
├─ tsconfig.json        # ts配置文件
├─ vite.config.js       # vite服务配置文件
└─ README.md            # 项目说明文档

```

## 快速开始

```sh
# 进入前端工程目录
cd frontend
# 安装依赖
npm install
# 启动前端服务
npm run dev
# 构建前端, 生成 `frontend/dist` 目录
npm run build
```
