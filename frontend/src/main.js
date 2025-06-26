import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import Antd from "ant-design-vue";
import "ant-design-vue/dist/reset.css";
import VChart from "vue-echarts";
import "echarts";
import './style.css'
import { createPinia } from 'pinia';
import { useConfigStore } from "@/store/index";
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 新增：引入NProgress
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(ElementPlus)

// 新增：配置NProgress
NProgress.configure({
  showSpinner: false, // 关闭加载动画
  trickleSpeed: 100, // 进度条递增速度
  easing: 'ease', // 动画方式
  speed: 500 // 动画速度
});

// 新增：路由钩子
router.beforeEach((to, from, next) => {
  NProgress.start(); // 开始进度条
  next();
});

router.afterEach(() => {
  NProgress.done(); // 结束进度条
});

const initConfig = async () => {
  const configStore = useConfigStore();
  await configStore.getConfig();

  const loginTitle = configStore.getConfigValue("sys_web_title");
  const loginLogo = configStore.getConfigValue("sys_web_favicon");

  if (loginTitle) {
    document.title = loginTitle;
  }

  if (loginLogo) {
    const favicon = document.querySelector('link[rel="icon"]');
    if (favicon) {
      favicon.href = loginLogo;
    }
  }
};

// 初始化配置并挂载应用
initConfig().then(() => {
  app.use(router);
  app.use(Antd);
  app.component("VChart", VChart);
  app.mount("#app");
});
